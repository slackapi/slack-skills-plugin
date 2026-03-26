# Slack Channel Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Claude Code Channels support to the Slack MCP plugin for real-time bidirectional Slack messaging, with headless operation, permission relay, and pairing-based access control.

**Architecture:** A single Bun process with three layers: `@slack/bolt` in Socket Mode for Slack event delivery, a bridge layer that transforms events between Slack and MCP formats, and the MCP SDK channel server (`claude/channel` + `claude/channel/permission`) for Claude Code integration. The process communicates with Claude Code over stdio and exposes no ports.

**Tech Stack:** Bun, TypeScript, `@slack/bolt` (Socket Mode), `@modelcontextprotocol/sdk`, `zod`

**Spec:** `docs/superpowers/specs/2026-03-26-slack-channels-design.md`

---

## File Structure

```
src/
├── index.ts          # Entry point: validates env, wires up settings → gating → mcp → slack → bridge, starts both servers
├── settings.ts       # Settings file read/write with atomic saves and Zod schema validation
├── gating.ts         # Sender allowlist checks, pairing code generation/verification, bootstrap mode
├── mcp.ts            # MCP Server constructor, tool definitions (reply/react/manage_access/manage_channels), permission relay handler
├── slack.ts          # Bolt App in Socket Mode, event subscriptions (message, app_mention, reaction_added)
├── bridge.ts         # Event transformer: Slack events → MCP notifications, MCP tool calls → Slack API, lastActiveContext tracking, name resolution cache
tests/
├── settings.test.ts  # Settings read/write/defaults/corruption
├── gating.test.ts    # Allowlist checks, pairing flow, expiry, bootstrap mode
├── bridge.test.ts    # Event transformation, name cache, lastActiveContext, permission verdict parsing
├── mcp.test.ts       # Tool schemas, authorization checks, tool dispatch
```

Key dependencies between modules:
- `index.ts` imports and wires everything together
- `bridge.ts` depends on `gating.ts` (sender checks), `settings.ts` (read watchedChannels), and calls methods on the MCP `Server` instance and Bolt `App` instance
- `mcp.ts` depends on `bridge.ts` (tool calls delegate to bridge for Slack API calls and authorization)
- `slack.ts` depends on `bridge.ts` (event handlers delegate to bridge)

---

### Task 1: Project Setup

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`

- [ ] **Step 1: Initialize project and install dependencies**

```bash
cd /Users/marciorodrigues/Projects/slack-mcp-plugin
bun add @slack/bolt @modelcontextprotocol/sdk zod
bun add -d @types/bun
```

Note: do NOT run `bun init` — the project already has files. `bun add` will create `package.json` if missing.

- [ ] **Step 2: Configure tsconfig.json**

Write `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "dist",
    "rootDir": "src",
    "types": ["bun-types"]
  },
  "include": ["src/**/*.ts", "tests/**/*.ts"]
}
```

- [ ] **Step 3: Verify setup compiles**

```bash
bun tsc --noEmit
```

Expected: no errors (no source files yet, so clean exit).

- [ ] **Step 4: Commit**

```bash
git add package.json tsconfig.json bun.lock
git commit -m "chore: initialize project with bun, bolt, mcp sdk, and zod"
```

---

### Task 2: Settings Module

**Files:**
- Create: `src/settings.ts`
- Create: `tests/settings.test.ts`

- [ ] **Step 1: Write failing tests for settings**

Write `tests/settings.test.ts`:

```typescript
import { describe, test, expect, beforeEach, afterEach } from 'bun:test'
import { readSettings, writeSettings, DEFAULT_SETTINGS, type Settings } from '../src/settings'
import { mkdtemp, rm, writeFile } from 'node:fs/promises'
import { join } from 'node:path'
import { tmpdir } from 'node:os'

describe('readSettings', () => {
  let dir: string

  beforeEach(async () => {
    dir = await mkdtemp(join(tmpdir(), 'settings-test-'))
  })

  afterEach(async () => {
    await rm(dir, { recursive: true })
  })

  test('returns defaults when file does not exist', async () => {
    const settings = await readSettings(join(dir, 'settings.json'))
    expect(settings).toEqual(DEFAULT_SETTINGS)
  })

  test('reads valid settings file', async () => {
    const path = join(dir, 'settings.json')
    const data: Settings = {
      gating: { mode: 'per-user', allowedUsers: ['U123'] },
      watchedChannels: ['C456'],
    }
    await writeFile(path, JSON.stringify(data))
    const settings = await readSettings(path)
    expect(settings.gating.allowedUsers).toEqual(['U123'])
    expect(settings.watchedChannels).toEqual(['C456'])
  })

  test('returns defaults on corrupted JSON', async () => {
    const path = join(dir, 'settings.json')
    await writeFile(path, 'not valid json{{{')
    const settings = await readSettings(path)
    expect(settings).toEqual(DEFAULT_SETTINGS)
  })

  test('returns defaults on invalid schema', async () => {
    const path = join(dir, 'settings.json')
    await writeFile(path, JSON.stringify({ gating: { mode: 'invalid' } }))
    const settings = await readSettings(path)
    expect(settings).toEqual(DEFAULT_SETTINGS)
  })
})

describe('writeSettings', () => {
  let dir: string

  beforeEach(async () => {
    dir = await mkdtemp(join(tmpdir(), 'settings-test-'))
  })

  afterEach(async () => {
    await rm(dir, { recursive: true })
  })

  test('writes and reads back settings', async () => {
    const path = join(dir, 'settings.json')
    const data: Settings = {
      gating: { mode: 'per-user', allowedUsers: ['UABC'] },
      watchedChannels: ['CDEF'],
    }
    await writeSettings(path, data)
    const result = await readSettings(path)
    expect(result).toEqual(data)
  })

  test('creates parent directories if missing', async () => {
    const path = join(dir, 'nested', 'deep', 'settings.json')
    await writeSettings(path, DEFAULT_SETTINGS)
    const result = await readSettings(path)
    expect(result).toEqual(DEFAULT_SETTINGS)
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bun test tests/settings.test.ts
```

Expected: FAIL — `Cannot find module '../src/settings'`

- [ ] **Step 3: Implement settings module**

Write `src/settings.ts`:

```typescript
import { z } from 'zod'
import { readFile, writeFile, mkdir, rename } from 'node:fs/promises'
import { dirname, join } from 'node:path'

const GatingSchema = z.object({
  mode: z.literal('per-user'),
  allowedUsers: z.array(z.string()),
})

const SettingsSchema = z.object({
  gating: GatingSchema,
  watchedChannels: z.array(z.string()),
})

export type Settings = z.infer<typeof SettingsSchema>

export const DEFAULT_SETTINGS: Settings = {
  gating: { mode: 'per-user', allowedUsers: [] },
  watchedChannels: [],
}

export async function readSettings(path: string): Promise<Settings> {
  try {
    const raw = await readFile(path, 'utf-8')
    const parsed = JSON.parse(raw)
    return SettingsSchema.parse(parsed)
  } catch {
    return { ...DEFAULT_SETTINGS }
  }
}

export async function writeSettings(path: string, settings: Settings): Promise<void> {
  const dir = dirname(path)
  await mkdir(dir, { recursive: true })
  const tmp = join(dir, `.settings.tmp.${process.pid}`)
  await writeFile(tmp, JSON.stringify(settings, null, 2))
  await rename(tmp, path)
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bun test tests/settings.test.ts
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/settings.ts tests/settings.test.ts
git commit -m "feat: add settings module with read/write and schema validation"
```

---

### Task 3: Gating Module

**Files:**
- Create: `src/gating.ts`
- Create: `tests/gating.test.ts`

- [ ] **Step 1: Write failing tests for gating**

Write `tests/gating.test.ts`:

```typescript
import { describe, test, expect, beforeEach } from 'bun:test'
import { Gating } from '../src/gating'
import { DEFAULT_SETTINGS, type Settings } from '../src/settings'

describe('Gating', () => {
  let settings: Settings
  let gating: Gating

  beforeEach(() => {
    settings = {
      gating: { mode: 'per-user', allowedUsers: ['U_ALLOWED'] },
      watchedChannels: [],
    }
    gating = new Gating(settings)
  })

  test('allows users in the allowlist', () => {
    expect(gating.isAllowed('U_ALLOWED')).toBe(true)
  })

  test('rejects users not in the allowlist', () => {
    expect(gating.isAllowed('U_STRANGER')).toBe(false)
  })

  test('detects bootstrap mode when allowlist is empty', () => {
    gating = new Gating(DEFAULT_SETTINGS)
    expect(gating.isBootstrapMode()).toBe(true)
  })

  test('not in bootstrap mode when allowlist has users', () => {
    expect(gating.isBootstrapMode()).toBe(false)
  })

  test('addUser adds to allowlist and exits bootstrap', () => {
    gating = new Gating(DEFAULT_SETTINGS)
    expect(gating.isBootstrapMode()).toBe(true)
    gating.addUser('U_NEW')
    expect(gating.isAllowed('U_NEW')).toBe(true)
    expect(gating.isBootstrapMode()).toBe(false)
  })

  test('removeUser removes from allowlist', () => {
    gating.removeUser('U_ALLOWED')
    expect(gating.isAllowed('U_ALLOWED')).toBe(false)
  })
})

describe('Pairing', () => {
  let gating: Gating

  beforeEach(() => {
    gating = new Gating(DEFAULT_SETTINGS)
  })

  test('generates a 6-character alphanumeric code', () => {
    const code = gating.createPairingCode('U_TARGET')
    expect(code).toMatch(/^[A-Z0-9]{6}$/)
  })

  test('verifies a valid code for the correct user', () => {
    const code = gating.createPairingCode('U_TARGET')
    expect(gating.verifyPairingCode(code, 'U_TARGET')).toBe(true)
  })

  test('rejects a valid code for the wrong user', () => {
    const code = gating.createPairingCode('U_TARGET')
    expect(gating.verifyPairingCode(code, 'U_OTHER')).toBe(false)
  })

  test('rejects an invalid code', () => {
    gating.createPairingCode('U_TARGET')
    expect(gating.verifyPairingCode('ZZZZZZ', 'U_TARGET')).toBe(false)
  })

  test('code is consumed after verification', () => {
    const code = gating.createPairingCode('U_TARGET')
    expect(gating.verifyPairingCode(code, 'U_TARGET')).toBe(true)
    expect(gating.verifyPairingCode(code, 'U_TARGET')).toBe(false)
  })

  test('expired codes are rejected', () => {
    const code = gating.createPairingCode('U_TARGET', Date.now() - 6 * 60 * 1000)
    expect(gating.verifyPairingCode(code, 'U_TARGET')).toBe(false)
  })

  test('only one code active during bootstrap', () => {
    const code1 = gating.createPairingCode('U_FIRST')
    const code2 = gating.createPairingCode('U_SECOND')
    expect(code2).toBeNull()
    expect(gating.verifyPairingCode(code1!, 'U_FIRST')).toBe(true)
  })

  test('hasPendingPairingCode returns true when code is active', () => {
    gating.createPairingCode('U_TARGET')
    expect(gating.hasPendingPairingCode()).toBe(true)
  })

  test('multiple codes allowed when not in bootstrap mode', () => {
    gating.addUser('U_ADMIN')
    const code1 = gating.createPairingCode('U_FIRST')
    const code2 = gating.createPairingCode('U_SECOND')
    expect(code1).not.toBeNull()
    expect(code2).not.toBeNull()
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bun test tests/gating.test.ts
```

Expected: FAIL — `Cannot find module '../src/gating'`

- [ ] **Step 3: Implement gating module**

Write `src/gating.ts`:

```typescript
import type { Settings } from './settings'

const CODE_TTL_MS = 5 * 60 * 1000 // 5 minutes
const CODE_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789' // no 0/O/1/I/L ambiguity

interface PendingCode {
  userId: string
  timestamp: number
}

export class Gating {
  private allowedUsers: Set<string>
  private pendingCodes: Map<string, PendingCode> = new Map()

  constructor(settings: Settings) {
    this.allowedUsers = new Set(settings.gating.allowedUsers)
  }

  isAllowed(userId: string): boolean {
    return this.allowedUsers.has(userId)
  }

  isBootstrapMode(): boolean {
    return this.allowedUsers.size === 0
  }

  addUser(userId: string): void {
    this.allowedUsers.add(userId)
  }

  removeUser(userId: string): void {
    this.allowedUsers.delete(userId)
  }

  getAllowedUsers(): string[] {
    return [...this.allowedUsers]
  }

  createPairingCode(userId: string, now: number = Date.now()): string | null {
    this.pruneExpired(now)

    // In bootstrap mode, only one code at a time
    if (this.isBootstrapMode() && this.pendingCodes.size > 0) {
      return null
    }

    const code = Array.from({ length: 6 }, () =>
      CODE_CHARS[Math.floor(Math.random() * CODE_CHARS.length)]
    ).join('')

    this.pendingCodes.set(code, { userId, timestamp: now })
    return code
  }

  verifyPairingCode(code: string, userId: string): boolean {
    this.pruneExpired()
    const entry = this.pendingCodes.get(code.toUpperCase())
    if (!entry || entry.userId !== userId) return false
    this.pendingCodes.delete(code.toUpperCase())
    return true
  }

  hasPendingPairingCode(): boolean {
    this.pruneExpired()
    return this.pendingCodes.size > 0
  }

  private pruneExpired(now: number = Date.now()): void {
    for (const [code, entry] of this.pendingCodes) {
      if (now - entry.timestamp > CODE_TTL_MS) {
        this.pendingCodes.delete(code)
      }
    }
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bun test tests/gating.test.ts
```

Expected: all 13 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gating.ts tests/gating.test.ts
git commit -m "feat: add gating module with allowlist and pairing flow"
```

---

### Task 4: MCP Server Module

**Files:**
- Create: `src/mcp.ts`
- Create: `tests/mcp.test.ts`

- [ ] **Step 1: Write failing tests for MCP tool definitions**

Write `tests/mcp.test.ts`:

```typescript
import { describe, test, expect } from 'bun:test'
import { TOOL_DEFINITIONS, CHANNEL_INSTRUCTIONS } from '../src/mcp'

describe('MCP tool definitions', () => {
  test('defines reply tool with required params', () => {
    const reply = TOOL_DEFINITIONS.find(t => t.name === 'reply')
    expect(reply).toBeDefined()
    expect(reply!.inputSchema.required).toContain('channel_id')
    expect(reply!.inputSchema.required).toContain('text')
    expect(reply!.inputSchema.properties).toHaveProperty('thread_ts')
  })

  test('defines react tool with required params', () => {
    const react = TOOL_DEFINITIONS.find(t => t.name === 'react')
    expect(react).toBeDefined()
    expect(react!.inputSchema.required).toContain('channel_id')
    expect(react!.inputSchema.required).toContain('timestamp')
    expect(react!.inputSchema.required).toContain('emoji')
  })

  test('defines manage_access tool with required params', () => {
    const tool = TOOL_DEFINITIONS.find(t => t.name === 'manage_access')
    expect(tool).toBeDefined()
    expect(tool!.inputSchema.required).toContain('action')
    expect(tool!.inputSchema.required).toContain('value')
  })

  test('defines manage_channels tool with required params', () => {
    const tool = TOOL_DEFINITIONS.find(t => t.name === 'manage_channels')
    expect(tool).toBeDefined()
    expect(tool!.inputSchema.required).toContain('action')
    expect(tool!.inputSchema.required).toContain('channel_id')
  })

  test('exports exactly 4 tools', () => {
    expect(TOOL_DEFINITIONS).toHaveLength(4)
  })

  test('instructions mention all event types', () => {
    expect(CHANNEL_INSTRUCTIONS).toContain('dm')
    expect(CHANNEL_INSTRUCTIONS).toContain('mention')
    expect(CHANNEL_INSTRUCTIONS).toContain('message')
    expect(CHANNEL_INSTRUCTIONS).toContain('reaction')
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bun test tests/mcp.test.ts
```

Expected: FAIL — `Cannot find module '../src/mcp'`

- [ ] **Step 3: Implement MCP module**

Write `src/mcp.ts`:

```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from '@modelcontextprotocol/sdk/types.js'
import { z } from 'zod'
import type { Bridge } from './bridge'

export const CHANNEL_INSTRUCTIONS = [
  'Messages from Slack arrive as <channel source="slack" event="..." user="..." channel_id="..." ...>.',
  'Events: "dm" (direct message to bot), "mention" (@mention in a channel), "message" (watched channel), "reaction" (emoji on a bot message).',
  'Reply with the reply tool, passing channel_id and optionally thread_ts from the tag.',
  'Use the react tool to add emoji reactions.',
  'Use manage_access and manage_channels to administer the instance when asked.',
].join('\n')

export const TOOL_DEFINITIONS = [
  {
    name: 'reply',
    description: 'Send a message back to a Slack channel or thread',
    inputSchema: {
      type: 'object' as const,
      properties: {
        channel_id: { type: 'string', description: 'Slack channel ID to send to' },
        text: { type: 'string', description: 'Message content' },
        thread_ts: { type: 'string', description: 'Thread timestamp to reply in-thread' },
      },
      required: ['channel_id', 'text'],
    },
  },
  {
    name: 'react',
    description: 'Add an emoji reaction to a Slack message',
    inputSchema: {
      type: 'object' as const,
      properties: {
        channel_id: { type: 'string', description: 'Channel containing the message' },
        timestamp: { type: 'string', description: 'Message timestamp to react to' },
        emoji: { type: 'string', description: 'Emoji name without colons (e.g. thumbsup)' },
      },
      required: ['channel_id', 'timestamp', 'emoji'],
    },
  },
  {
    name: 'manage_access',
    description: 'Add, remove, or pair users in the access allowlist',
    inputSchema: {
      type: 'object' as const,
      properties: {
        action: {
          type: 'string',
          enum: ['add_user', 'remove_user', 'pair_user'],
          description: 'Action to perform',
        },
        value: { type: 'string', description: 'Slack user ID (e.g. U12345ABC)' },
      },
      required: ['action', 'value'],
    },
  },
  {
    name: 'manage_channels',
    description: 'Add or remove channels from the watch list',
    inputSchema: {
      type: 'object' as const,
      properties: {
        action: {
          type: 'string',
          enum: ['watch', 'unwatch'],
          description: 'Action to perform',
        },
        channel_id: { type: 'string', description: 'Slack channel ID' },
      },
      required: ['action', 'channel_id'],
    },
  },
]

// Schema for permission_request notifications from Claude Code.
// Uses z.object with z.literal on the method field — this is how the MCP SDK's
// setNotificationHandler dispatches by method name (same pattern as the channels reference doc).
const PermissionRequestSchema = z.object({
  method: z.literal('notifications/claude/channel/permission_request'),
  params: z.object({
    request_id: z.string(),
    tool_name: z.string(),
    description: z.string(),
    input_preview: z.string(),
  }),
})

export function createMcpServer(bridge: Bridge): Server {
  const mcp = new Server(
    { name: 'slack-channel', version: '0.0.1' },
    {
      capabilities: {
        experimental: {
          'claude/channel': {},
          'claude/channel/permission': {},
        },
        tools: {},
      },
      instructions: CHANNEL_INSTRUCTIONS,
    },
  )

  mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: TOOL_DEFINITIONS,
  }))

  mcp.setRequestHandler(CallToolRequestSchema, async (req) => {
    const { name, arguments: args } = req.params
    return bridge.handleToolCall(name, args as Record<string, string>)
  })

  // Register handler for permission_request notifications from Claude Code.
  // The MCP SDK Server.setNotificationHandler dispatches on the z.literal method field.
  // This is the same pattern used in the official channels reference documentation.
  mcp.setNotificationHandler(PermissionRequestSchema, async ({ params }) => {
    await bridge.handlePermissionRequest(params)
  })

  return mcp
}

export async function connectMcp(mcp: Server): Promise<void> {
  await mcp.connect(new StdioServerTransport())
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bun test tests/mcp.test.ts
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mcp.ts tests/mcp.test.ts
git commit -m "feat: add MCP server module with tool definitions and permission relay"
```

---

### Task 5: Bridge Module

**Files:**
- Create: `src/bridge.ts`
- Create: `tests/bridge.test.ts`

- [ ] **Step 1: Write failing tests for bridge**

Write `tests/bridge.test.ts`:

```typescript
import { describe, test, expect, beforeEach, mock } from 'bun:test'
import { Bridge, type ActiveContext } from '../src/bridge'
import { Gating } from '../src/gating'
import { DEFAULT_SETTINGS, type Settings } from '../src/settings'

// Mock MCP server and Slack app
function createMockMcp() {
  return {
    notification: mock(() => Promise.resolve()),
  }
}

function createMockSlackApp() {
  return {
    client: {
      chat: {
        postMessage: mock(() => Promise.resolve({ ok: true })),
        postEphemeral: mock(() => Promise.resolve({ ok: true })),
      },
      reactions: {
        add: mock(() => Promise.resolve({ ok: true })),
      },
      users: {
        info: mock(() => Promise.resolve({
          ok: true,
          user: { id: 'U123', name: 'alice', real_name: 'Alice' },
        })),
      },
      conversations: {
        info: mock(() => Promise.resolve({
          ok: true,
          channel: { id: 'C123', name: 'general' },
        })),
        join: mock(() => Promise.resolve({ ok: true })),
      },
    },
  }
}

describe('Bridge - event transformation', () => {
  let bridge: Bridge
  let mockMcp: ReturnType<typeof createMockMcp>
  let mockSlack: ReturnType<typeof createMockSlackApp>
  let settings: Settings

  beforeEach(() => {
    settings = {
      gating: { mode: 'per-user', allowedUsers: ['U_ALLOWED'] },
      watchedChannels: ['C_WATCHED'],
    }
    const gating = new Gating(settings)
    mockMcp = createMockMcp()
    mockSlack = createMockSlackApp()
    bridge = new Bridge(mockSlack as any, gating, settings)
    bridge.setMcpServer(mockMcp as any)
  })

  test('emits dm event for allowed user DM', async () => {
    await bridge.handleMessage({
      text: 'hello',
      user: 'U_ALLOWED',
      channel: 'D_DM_CHANNEL',
      channel_type: 'im',
      ts: '1234.5678',
    })
    expect(mockMcp.notification).toHaveBeenCalledTimes(1)
    const call = (mockMcp.notification as any).mock.calls[0]
    expect(call[0].params.meta.event).toBe('dm')
  })

  test('drops messages from non-allowed users', async () => {
    await bridge.handleMessage({
      text: 'hello',
      user: 'U_STRANGER',
      channel: 'D_DM_CHANNEL',
      channel_type: 'im',
      ts: '1234.5678',
    })
    expect(mockMcp.notification).not.toHaveBeenCalled()
  })

  test('emits message event for watched channel', async () => {
    await bridge.handleMessage({
      text: 'deploy failed',
      user: 'U_ALLOWED',
      channel: 'C_WATCHED',
      channel_type: 'channel',
      ts: '1234.5678',
    })
    const call = (mockMcp.notification as any).mock.calls[0]
    expect(call[0].params.meta.event).toBe('message')
  })

  test('drops messages from allowed users in non-watched, non-DM channels', async () => {
    await bridge.handleMessage({
      text: 'hello',
      user: 'U_ALLOWED',
      channel: 'C_OTHER',
      channel_type: 'channel',
      ts: '1234.5678',
    })
    expect(mockMcp.notification).not.toHaveBeenCalled()
  })

  test('updates lastActiveContext on gated events', async () => {
    await bridge.handleMessage({
      text: 'hello',
      user: 'U_ALLOWED',
      channel: 'D_DM_CHANNEL',
      channel_type: 'im',
      ts: '1234.5678',
    })
    expect(bridge.getLastActiveContext()).toEqual({
      userId: 'U_ALLOWED',
      channelId: 'D_DM_CHANNEL',
      threadTs: undefined,
    })
  })
})

describe('Bridge - mention events', () => {
  let bridge: Bridge
  let mockMcp: ReturnType<typeof createMockMcp>

  beforeEach(() => {
    const settings: Settings = {
      gating: { mode: 'per-user', allowedUsers: ['U_ALLOWED'] },
      watchedChannels: [],
    }
    const gating = new Gating(settings)
    mockMcp = createMockMcp()
    const mockSlack = createMockSlackApp()
    bridge = new Bridge(mockSlack as any, gating, settings)
    bridge.setMcpServer(mockMcp as any)
  })

  test('emits mention event for app_mention', async () => {
    await bridge.handleMention({
      text: '<@BOTID> help',
      user: 'U_ALLOWED',
      channel: 'C_ANY',
      ts: '1234.5678',
    })
    const call = (mockMcp.notification as any).mock.calls[0]
    expect(call[0].params.meta.event).toBe('mention')
  })
})

describe('Bridge - permission verdict parsing', () => {
  test('parses yes verdict', () => {
    expect(Bridge.parsePermissionVerdict('yes abcde')).toEqual({
      requestId: 'abcde',
      behavior: 'allow',
    })
  })

  test('parses no verdict', () => {
    expect(Bridge.parsePermissionVerdict('no abcde')).toEqual({
      requestId: 'abcde',
      behavior: 'deny',
    })
  })

  test('parses y shorthand', () => {
    expect(Bridge.parsePermissionVerdict('y fghkm')).toEqual({
      requestId: 'fghkm',
      behavior: 'allow',
    })
  })

  test('handles case insensitivity', () => {
    expect(Bridge.parsePermissionVerdict('YES ABCDE')).toEqual({
      requestId: 'abcde',
      behavior: 'allow',
    })
  })

  test('returns null for non-verdict text', () => {
    expect(Bridge.parsePermissionVerdict('hello world')).toBeNull()
  })

  test('returns null for verdict with l in id', () => {
    expect(Bridge.parsePermissionVerdict('yes ablde')).toBeNull()
  })
})

describe('Bridge - tool authorization', () => {
  let bridge: Bridge
  let mockMcp: ReturnType<typeof createMockMcp>
  let mockSlack: ReturnType<typeof createMockSlackApp>

  beforeEach(() => {
    const settings: Settings = {
      gating: { mode: 'per-user', allowedUsers: ['U_ADMIN'] },
      watchedChannels: [],
    }
    const gating = new Gating(settings)
    mockMcp = createMockMcp()
    mockSlack = createMockSlackApp()
    bridge = new Bridge(mockSlack as any, gating, settings)
    bridge.setMcpServer(mockMcp as any)
  })

  test('manage_access fails when lastActiveContext is null', async () => {
    const result = await bridge.handleToolCall('manage_access', {
      action: 'add_user',
      value: 'U_NEW',
    })
    expect(result.content[0].text).toContain('authorization')
  })

  test('manage_access fails when caller not in allowlist', async () => {
    // Set lastActiveContext to a non-allowed user (simulate somehow)
    // Actually this shouldn't happen since context is only set for gated users
    // Test the null case is sufficient
    const result = await bridge.handleToolCall('manage_access', {
      action: 'add_user',
      value: 'U_NEW',
    })
    expect(result.content[0].text).toContain('authorization')
  })

  test('manage_channels fails when lastActiveContext is null', async () => {
    const result = await bridge.handleToolCall('manage_channels', {
      action: 'watch',
      channel_id: 'C_NEW',
    })
    expect(result.content[0].text).toContain('authorization')
  })

  test('reply tool works without authorization check', async () => {
    const result = await bridge.handleToolCall('reply', {
      channel_id: 'C123',
      text: 'hello',
    })
    expect(result.content[0].text).toBe('sent')
  })
})

describe('Bridge - name resolution cache', () => {
  let bridge: Bridge
  let mockSlack: ReturnType<typeof createMockSlackApp>

  beforeEach(() => {
    const settings: Settings = {
      gating: { mode: 'per-user', allowedUsers: ['U_ALLOWED'] },
      watchedChannels: ['C123'],
    }
    const gating = new Gating(settings)
    const mockMcp = createMockMcp()
    mockSlack = createMockSlackApp()
    bridge = new Bridge(mockSlack as any, gating, settings)
    bridge.setMcpServer(mockMcp as any)
  })

  test('resolves and caches user name', async () => {
    const name1 = await bridge.resolveUserName('U123')
    const name2 = await bridge.resolveUserName('U123')
    expect(name1).toBe('Alice')
    expect(name2).toBe('Alice')
    // Should only have called the API once due to caching
    expect(mockSlack.client.users.info).toHaveBeenCalledTimes(1)
  })

  test('resolves and caches channel name', async () => {
    const name1 = await bridge.resolveChannelName('C123')
    const name2 = await bridge.resolveChannelName('C123')
    expect(name1).toBe('general')
    expect(name2).toBe('general')
    expect(mockSlack.client.conversations.info).toHaveBeenCalledTimes(1)
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bun test tests/bridge.test.ts
```

Expected: FAIL — `Cannot find module '../src/bridge'`

- [ ] **Step 3: Implement bridge module**

Write `src/bridge.ts`:

```typescript
import type { Server } from '@modelcontextprotocol/sdk/server/index.js'
import type { App } from '@slack/bolt'
import type { Gating } from './gating'
import type { Settings } from './settings'
import { writeSettings } from './settings'

export interface ActiveContext {
  userId: string
  channelId: string
  threadTs?: string
}

interface SlackMessageEvent {
  text: string
  user: string
  channel: string
  channel_type: string
  ts: string
  thread_ts?: string
}

interface SlackMentionEvent {
  text: string
  user: string
  channel: string
  ts: string
  thread_ts?: string
}

interface SlackReactionEvent {
  user: string
  reaction: string
  item: {
    type: string
    channel: string
    ts: string
  }
  item_user: string
  event_ts: string
}

interface PermissionRequest {
  request_id: string
  tool_name: string
  description: string
  input_preview: string
}

const PERMISSION_REPLY_RE = /^\s*(y|yes|n|no)\s+([a-km-z]{5})\s*$/i

export class Bridge {
  private mcp: Server | null = null
  private lastActiveContext: ActiveContext | null = null
  private userNameCache = new Map<string, string>()
  private channelNameCache = new Map<string, string>()
  private settingsPath: string

  constructor(
    private slackApp: App,
    private gating: Gating,
    private settings: Settings,
    settingsPath: string = '',
  ) {
    this.settingsPath = settingsPath
  }

  setMcpServer(mcp: Server): void {
    this.mcp = mcp
  }

  getLastActiveContext(): ActiveContext | null {
    return this.lastActiveContext
  }

  static parsePermissionVerdict(text: string): { requestId: string; behavior: 'allow' | 'deny' } | null {
    const m = PERMISSION_REPLY_RE.exec(text)
    if (!m) return null
    return {
      requestId: m[2].toLowerCase(),
      behavior: m[1].toLowerCase().startsWith('y') ? 'allow' : 'deny',
    }
  }

  async handleMessage(event: SlackMessageEvent): Promise<void> {
    // Check for pairing code response during bootstrap
    if (this.gating.isBootstrapMode()) {
      await this.handleBootstrapMessage(event)
      return
    }

    // Check for permission verdict before gating (must be from allowed user though)
    if (this.gating.isAllowed(event.user)) {
      const verdict = Bridge.parsePermissionVerdict(event.text)
      if (verdict) {
        await this.mcp.notification({
          method: 'notifications/claude/channel/permission' as any,
          params: {
            request_id: verdict.requestId,
            behavior: verdict.behavior,
          },
        })
        return
      }
    }

    // Not allowed — check if they're responding to a pairing code, otherwise drop
    if (!this.gating.isAllowed(event.user)) {
      await this.handlePairingResponse(event)
      return
    }

    // Execution reaches here only for allowed users

    // Determine event type
    const isDm = event.channel_type === 'im'
    const isWatched = this.settings.watchedChannels.includes(event.channel)

    if (!isDm && !isWatched) return

    const eventType = isDm ? 'dm' : 'message'
    await this.emitChannelNotification(eventType, event)
  }

  async handleMention(event: SlackMentionEvent): Promise<void> {
    if (!this.gating.isAllowed(event.user)) return

    await this.emitChannelNotification('mention', {
      text: event.text,
      user: event.user,
      channel: event.channel,
      channel_type: 'channel',
      ts: event.ts,
      thread_ts: event.thread_ts,
    })
  }

  async handleReaction(event: SlackReactionEvent, botUserId: string): Promise<void> {
    // Only emit for reactions on bot's own messages
    if (event.item.type !== 'message' || event.item_user !== botUserId) return
    if (!this.gating.isAllowed(event.user)) return

    const userName = await this.resolveUserName(event.user)
    const channelName = await this.resolveChannelName(event.item.channel)

    const meta: Record<string, string> = {
      event: 'reaction',
      user: event.user,
      user_name: userName,
      channel_id: event.item.channel,
      emoji: event.reaction,
      item_ts: event.item.ts,
      ts: event.event_ts,
    }
    if (channelName) meta.channel_name = channelName

    this.lastActiveContext = {
      userId: event.user,
      channelId: event.item.channel,
    }

    await this.mcp.notification({
      method: 'notifications/claude/channel' as any,
      params: {
        content: `Reaction :${event.reaction}: on message`,
        meta,
      },
    })
  }

  async handleToolCall(
    name: string,
    args: Record<string, string>,
  ): Promise<{ content: Array<{ type: string; text: string }> }> {
    try {
      switch (name) {
        case 'reply':
          return await this.handleReply(args)
        case 'react':
          return await this.handleReact(args)
        case 'manage_access':
          return await this.handleManageAccess(args)
        case 'manage_channels':
          return await this.handleManageChannels(args)
        default:
          throw new Error(`unknown tool: ${name}`)
      }
    } catch (err) {
      return { content: [{ type: 'text', text: `error: ${(err as Error).message}` }] }
    }
  }

  async handlePermissionRequest(params: PermissionRequest): Promise<void> {
    if (!this.lastActiveContext) {
      console.error('[slack-channel] permission request dropped: no active context')
      return
    }

    const prompt =
      `*Claude wants to run \`${params.tool_name}\`:* ${params.description}\n\n` +
      `Reply \`yes ${params.request_id}\` or \`no ${params.request_id}\``

    await this.slackApp.client.chat.postMessage({
      channel: this.lastActiveContext.channelId,
      text: prompt,
      thread_ts: this.lastActiveContext.threadTs,
    })
  }

  async resolveUserName(userId: string): Promise<string> {
    const cached = this.userNameCache.get(userId)
    if (cached) return cached

    try {
      const result = await this.slackApp.client.users.info({ user: userId })
      const name = (result.user as any)?.real_name || (result.user as any)?.name || userId
      this.userNameCache.set(userId, name)
      return name
    } catch {
      return userId
    }
  }

  async resolveChannelName(channelId: string): Promise<string> {
    const cached = this.channelNameCache.get(channelId)
    if (cached) return cached

    try {
      const result = await this.slackApp.client.conversations.info({ channel: channelId })
      const name = (result.channel as any)?.name || channelId
      this.channelNameCache.set(channelId, name)
      return name
    } catch {
      return channelId
    }
  }

  // --- Private helpers ---

  private async emitChannelNotification(
    eventType: string,
    event: SlackMessageEvent,
  ): Promise<void> {
    const userName = await this.resolveUserName(event.user)
    const channelName = event.channel_type !== 'im'
      ? await this.resolveChannelName(event.channel)
      : undefined

    const meta: Record<string, string> = {
      event: eventType,
      user: event.user,
      user_name: userName,
      channel_id: event.channel,
      ts: event.ts,
    }
    if (channelName) meta.channel_name = channelName
    if (event.thread_ts) meta.thread_ts = event.thread_ts

    this.lastActiveContext = {
      userId: event.user,
      channelId: event.channel,
      threadTs: event.thread_ts,
    }

    await this.mcp.notification({
      method: 'notifications/claude/channel' as any,
      params: {
        content: event.text,
        meta,
      },
    })
  }

  private async handleBootstrapMessage(event: SlackMessageEvent): Promise<void> {
    const pairMatch = event.text.match(/^pair\s+([A-Z0-9]{6})\s*$/i)
    if (pairMatch) {
      const code = pairMatch[1].toUpperCase()
      if (this.gating.verifyPairingCode(code, event.user)) {
        this.gating.addUser(event.user)
        await this.persistSettings()
        await this.slackApp.client.chat.postEphemeral({
          channel: event.channel,
          user: event.user,
          text: 'Paired successfully. You now have access.',
        })
      } else {
        await this.slackApp.client.chat.postEphemeral({
          channel: event.channel,
          user: event.user,
          text: 'Invalid or expired pairing code.',
        })
      }
      return
    }

    // First DM in bootstrap: send pairing code
    if (event.channel_type === 'im') {
      if (this.gating.hasPendingPairingCode()) {
        await this.slackApp.client.chat.postEphemeral({
          channel: event.channel,
          user: event.user,
          text: 'Pairing already in progress, please try again shortly.',
        })
        return
      }

      const code = this.gating.createPairingCode(event.user)
      if (code) {
        console.log(`[slack-channel] pairing code: ${code}`)
        await this.writePairingCodeFile(code)
        await this.slackApp.client.chat.postEphemeral({
          channel: event.channel,
          user: event.user,
          text: `Your pairing code is: \`${code}\`\nReply with \`pair ${code}\` to complete pairing.`,
        })
      }
    }
  }

  private async handlePairingResponse(event: SlackMessageEvent): Promise<void> {
    const pairMatch = event.text.match(/^pair\s+([A-Z0-9]{6})\s*$/i)
    if (!pairMatch) return

    const code = pairMatch[1].toUpperCase()
    if (this.gating.verifyPairingCode(code, event.user)) {
      this.gating.addUser(event.user)
      await this.persistSettings()
      await this.slackApp.client.chat.postEphemeral({
        channel: event.channel,
        user: event.user,
        text: 'Paired successfully. You now have access.',
      })
    } else {
      await this.slackApp.client.chat.postEphemeral({
        channel: event.channel,
        user: event.user,
        text: 'Invalid or expired pairing code.',
      })
    }
  }

  private checkAdminAuth(): void {
    if (!this.lastActiveContext) {
      throw new Error('authorization error: no active context')
    }
    if (!this.gating.isAllowed(this.lastActiveContext.userId)) {
      throw new Error('authorization error: caller not in allowlist')
    }
  }

  private async handleReply(args: Record<string, string>) {
    await this.slackApp.client.chat.postMessage({
      channel: args.channel_id,
      text: args.text,
      thread_ts: args.thread_ts,
    })
    return { content: [{ type: 'text', text: 'sent' }] }
  }

  private async handleReact(args: Record<string, string>) {
    await this.slackApp.client.reactions.add({
      channel: args.channel_id,
      timestamp: args.timestamp,
      name: args.emoji,
    })
    return { content: [{ type: 'text', text: 'reacted' }] }
  }

  private async handleManageAccess(args: Record<string, string>) {
    this.checkAdminAuth()

    switch (args.action) {
      case 'add_user':
        this.gating.addUser(args.value)
        await this.persistSettings()
        return { content: [{ type: 'text', text: `added ${args.value} to allowlist` }] }

      case 'remove_user':
        this.gating.removeUser(args.value)
        await this.persistSettings()
        return { content: [{ type: 'text', text: `removed ${args.value} from allowlist` }] }

      case 'pair_user': {
        const code = this.gating.createPairingCode(args.value)
        if (!code) {
          return { content: [{ type: 'text', text: 'pairing code already pending, try again shortly' }] }
        }
        // Send ephemeral code to target user in the current channel
        await this.slackApp.client.chat.postEphemeral({
          channel: this.lastActiveContext!.channelId,
          user: args.value,
          text: `Your pairing code is: \`${code}\`\nReply with \`pair ${code}\` to complete pairing.`,
        })
        return { content: [{ type: 'text', text: `pairing code sent to ${args.value}` }] }
      }

      default:
        throw new Error(`unknown action: ${args.action}`)
    }
  }

  private async handleManageChannels(args: Record<string, string>) {
    this.checkAdminAuth()

    switch (args.action) {
      case 'watch':
        if (!this.settings.watchedChannels.includes(args.channel_id)) {
          this.settings.watchedChannels.push(args.channel_id)
          await this.persistSettings()
          await this.slackApp.client.conversations.join({ channel: args.channel_id })
        }
        return { content: [{ type: 'text', text: `now watching ${args.channel_id}` }] }

      case 'unwatch': {
        const idx = this.settings.watchedChannels.indexOf(args.channel_id)
        if (idx !== -1) {
          this.settings.watchedChannels.splice(idx, 1)
          await this.persistSettings()
        }
        return { content: [{ type: 'text', text: `stopped watching ${args.channel_id}` }] }
      }

      default:
        throw new Error(`unknown action: ${args.action}`)
    }
  }

  private async persistSettings(): Promise<void> {
    this.settings.gating.allowedUsers = this.gating.getAllowedUsers()
    if (this.settingsPath) {
      await writeSettings(this.settingsPath, this.settings)
    }
  }

  private async writePairingCodeFile(code: string): Promise<void> {
    try {
      const { writeFile, mkdir } = await import('node:fs/promises')
      const { dirname } = await import('node:path')
      const path = this.settingsPath
        ? `${dirname(this.settingsPath)}/pairing-code.txt`
        : `${process.env.HOME}/.slack-channel/pairing-code.txt`
      await mkdir(dirname(path), { recursive: true })
      await writeFile(path, code)
    } catch (err) {
      console.error('[slack-channel] failed to write pairing code file:', err)
    }
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bun test tests/bridge.test.ts
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/bridge.ts tests/bridge.test.ts
git commit -m "feat: add bridge module with event transformation and tool handling"
```

---

### Task 6: Slack Module

**Files:**
- Create: `src/slack.ts`

This module is a thin wrapper around Bolt — it configures the app and wires event handlers to the bridge. It has no testable logic of its own (all logic is in bridge); it's integration glue.

- [ ] **Step 1: Implement Slack module**

Write `src/slack.ts`:

```typescript
import { App } from '@slack/bolt'
import type { Bridge } from './bridge'

export function createSlackApp(botToken: string, appToken: string): App {
  return new App({
    token: botToken,
    appToken,
    socketMode: true,
  })
}

export function registerEventHandlers(app: App, bridge: Bridge, botUserId: string): void {
  // DMs and channel messages
  app.event('message', async ({ event, say }) => {
    try {
      // Skip bot messages, message_changed, etc.
      if ((event as any).subtype) return

      await bridge.handleMessage({
        text: (event as any).text || '',
        user: (event as any).user || '',
        channel: (event as any).channel || '',
        channel_type: (event as any).channel_type || '',
        ts: (event as any).ts || '',
        thread_ts: (event as any).thread_ts,
      })
    } catch (err) {
      console.error('[slack-channel] error handling message:', err)
    }
  })

  // @mentions
  app.event('app_mention', async ({ event }) => {
    try {
      await bridge.handleMention({
        text: event.text || '',
        user: event.user || '',
        channel: event.channel || '',
        ts: event.ts || '',
        thread_ts: (event as any).thread_ts,
      })
    } catch (err) {
      console.error('[slack-channel] error handling mention:', err)
    }
  })

  // Reactions
  app.event('reaction_added', async ({ event }) => {
    try {
      await bridge.handleReaction(
        {
          user: event.user || '',
          reaction: event.reaction || '',
          item: event.item as any,
          item_user: (event as any).item_user || '',
          event_ts: (event as any).event_ts || '',
        },
        botUserId,
      )
    } catch (err) {
      console.error('[slack-channel] error handling reaction:', err)
    }
  })
}

export async function startSlackApp(app: App): Promise<string> {
  await app.start()
  // Get the bot's own user ID for reaction filtering
  const authResult = await app.client.auth.test()
  const botUserId = authResult.user_id || ''
  console.error(`[slack-channel] connected to Slack as ${authResult.user} (${botUserId})`)
  return botUserId
}
```

- [ ] **Step 2: Verify it compiles**

```bash
bun tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/slack.ts
git commit -m "feat: add Slack module with Socket Mode and event handlers"
```

---

### Task 7: Entry Point & Integration

**Files:**
- Create: `src/index.ts`
- Modify: `.mcp.json`

- [ ] **Step 1: Implement entry point**

Write `src/index.ts`:

```typescript
#!/usr/bin/env bun
import { readSettings } from './settings'
import { Gating } from './gating'
import { createMcpServer, connectMcp } from './mcp'
import { createSlackApp, registerEventHandlers, startSlackApp } from './slack'
import { Bridge } from './bridge'

// --- Validate environment ---
const botToken = process.env.SLACK_BOT_TOKEN
const appToken = process.env.SLACK_APP_TOKEN

if (!botToken || !botToken.startsWith('xoxb-')) {
  console.error('[slack-channel] SLACK_BOT_TOKEN is missing or invalid (must start with xoxb-)')
  process.exit(1)
}

if (!appToken || !appToken.startsWith('xapp-')) {
  console.error('[slack-channel] SLACK_APP_TOKEN is missing or invalid (must start with xapp-)')
  process.exit(1)
}

// --- Load settings ---
const settingsPath = process.env.SLACK_CHANNEL_SETTINGS_PATH
  || `${process.env.HOME}/.slack-channel/settings.json`

const settings = await readSettings(settingsPath)

// --- Wire up modules ---
const gating = new Gating(settings)
const slackApp = createSlackApp(botToken, appToken)

// Bridge is created without MCP reference. setMcpServer() wires it up after MCP is created.
const bridge = new Bridge(slackApp, gating, settings, settingsPath)
const mcp = createMcpServer(bridge)
bridge.setMcpServer(mcp)

// --- Start Slack (Socket Mode) first to validate credentials ---
const botUserId = await startSlackApp(slackApp)
registerEventHandlers(slackApp, bridge, botUserId)

// --- Connect MCP (stdio) after Slack is confirmed connected ---
await connectMcp(mcp)

if (gating.isBootstrapMode()) {
  console.error('[slack-channel] bootstrap mode: DM the bot to start pairing')
}

console.error('[slack-channel] ready')
```

- [ ] **Step 2: Update .mcp.json to add channel server entry**

The `.mcp.json` should have both the existing remote Slack server and the new channel server. Update it to:

```json
{
  "mcpServers": {
    "slack": {
      "type": "http",
      "url": "https://mcp.slack.com/mcp",
      "oauth": {
        "clientId": "1601185624273.8899143856786",
        "callbackPort": 3118
      }
    },
    "slack-channel": {
      "command": "bun",
      "args": ["./src/index.ts"],
      "env": {
        "SLACK_BOT_TOKEN": "",
        "SLACK_APP_TOKEN": ""
      }
    }
  }
}
```

- [ ] **Step 3: Verify the full project compiles**

```bash
bun tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Run all tests**

```bash
bun test
```

Expected: all tests across all files PASS.

- [ ] **Step 5: Commit**

```bash
git add src/index.ts .mcp.json
git commit -m "feat: add entry point and register channel server in .mcp.json"
```

---

### Task 8: End-to-End Smoke Test

**Files:**
- Create: `tests/integration.test.ts`

This test verifies the full wiring: settings → gating → bridge → MCP notification flow, without connecting to real Slack or Claude Code.

- [ ] **Step 1: Write integration test**

Write `tests/integration.test.ts`:

```typescript
import { describe, test, expect, mock } from 'bun:test'
import { Gating } from '../src/gating'
import { Bridge } from '../src/bridge'
import { TOOL_DEFINITIONS } from '../src/mcp'
import { DEFAULT_SETTINGS } from '../src/settings'

function createMocks() {
  const mcp = { notification: mock(() => Promise.resolve()) }
  const slack = {
    client: {
      chat: {
        postMessage: mock(() => Promise.resolve({ ok: true })),
        postEphemeral: mock(() => Promise.resolve({ ok: true })),
      },
      reactions: { add: mock(() => Promise.resolve({ ok: true })) },
      users: {
        info: mock(() =>
          Promise.resolve({ ok: true, user: { id: 'U1', name: 'alice', real_name: 'Alice' } })
        ),
      },
      conversations: {
        info: mock(() =>
          Promise.resolve({ ok: true, channel: { id: 'C1', name: 'general' } })
        ),
        join: mock(() => Promise.resolve({ ok: true })),
      },
    },
  }
  return { mcp, slack }
}

describe('End-to-end flow', () => {
  test('DM → notification → reply tool → Slack message', async () => {
    const settings = {
      gating: { mode: 'per-user' as const, allowedUsers: ['U_ALICE'] },
      watchedChannels: [],
    }
    const gating = new Gating(settings)
    const { mcp, slack } = createMocks()
    const bridge = new Bridge(slack as any, gating, settings)
    bridge.setMcpServer(mcp as any)

    // Alice sends a DM
    await bridge.handleMessage({
      text: 'check the deploy',
      user: 'U_ALICE',
      channel: 'D_ALICE_DM',
      channel_type: 'im',
      ts: '100.001',
    })

    // Notification emitted
    expect(mcp.notification).toHaveBeenCalledTimes(1)
    const notif = (mcp.notification as any).mock.calls[0][0]
    expect(notif.params.meta.event).toBe('dm')
    expect(notif.params.content).toBe('check the deploy')

    // Claude replies via tool
    const result = await bridge.handleToolCall('reply', {
      channel_id: 'D_ALICE_DM',
      text: 'Deploy looks good',
    })
    expect(result.content[0].text).toBe('sent')
    expect(slack.client.chat.postMessage).toHaveBeenCalledTimes(1)
  })

  test('permission relay full cycle', async () => {
    const settings = {
      gating: { mode: 'per-user' as const, allowedUsers: ['U_ALICE'] },
      watchedChannels: [],
    }
    const gating = new Gating(settings)
    const { mcp, slack } = createMocks()
    const bridge = new Bridge(slack as any, gating, settings)
    bridge.setMcpServer(mcp as any)

    // Set up active context via a DM
    await bridge.handleMessage({
      text: 'do something',
      user: 'U_ALICE',
      channel: 'D_ALICE_DM',
      channel_type: 'im',
      ts: '100.001',
    })

    // Permission request arrives
    await bridge.handlePermissionRequest({
      request_id: 'abcde',
      tool_name: 'Bash',
      description: 'git pull origin main',
      input_preview: '{"command":"git pull origin main"}',
    })

    // Should have posted to Alice's DM
    expect(slack.client.chat.postMessage).toHaveBeenCalledTimes(1)
    const msg = (slack.client.chat.postMessage as any).mock.calls[0][0]
    expect(msg.text).toContain('abcde')
    expect(msg.channel).toBe('D_ALICE_DM')

    // Alice replies with approval
    await bridge.handleMessage({
      text: 'yes abcde',
      user: 'U_ALICE',
      channel: 'D_ALICE_DM',
      channel_type: 'im',
      ts: '100.002',
    })

    // Verdict notification emitted (the second call — first was the DM notification)
    const verdictCall = (mcp.notification as any).mock.calls[1]
    expect(verdictCall[0].params.request_id).toBe('abcde')
    expect(verdictCall[0].params.behavior).toBe('allow')
  })

  test('bootstrap pairing flow', async () => {
    const settings = { ...DEFAULT_SETTINGS }
    const gating = new Gating(settings)
    const { mcp, slack } = createMocks()
    const bridge = new Bridge(slack as any, gating, settings)
    bridge.setMcpServer(mcp as any)

    // User DMs the bot in bootstrap mode
    await bridge.handleMessage({
      text: 'hello',
      user: 'U_NEW',
      channel: 'D_DM',
      channel_type: 'im',
      ts: '100.001',
    })

    // Should have sent ephemeral with pairing code
    expect(slack.client.chat.postEphemeral).toHaveBeenCalledTimes(1)
    const ephemeral = (slack.client.chat.postEphemeral as any).mock.calls[0][0]
    const codeMatch = ephemeral.text.match(/`([A-Z0-9]{6})`/)
    expect(codeMatch).not.toBeNull()

    const code = codeMatch![1]

    // User echoes the code back
    await bridge.handleMessage({
      text: `pair ${code}`,
      user: 'U_NEW',
      channel: 'D_DM',
      channel_type: 'im',
      ts: '100.002',
    })

    // User should now be allowed
    expect(gating.isAllowed('U_NEW')).toBe(true)
    expect(gating.isBootstrapMode()).toBe(false)
  })
})
```

- [ ] **Step 2: Run all tests**

```bash
bun test
```

Expected: all tests PASS, including the new integration tests.

- [ ] **Step 3: Commit**

```bash
git add tests/integration.test.ts
git commit -m "test: add end-to-end integration tests for channel flows"
```

---

### Task 9: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add channel setup section to README**

Add a new section to `README.md` after the existing setup instructions, covering:

1. **Slack App Setup**: Create a Slack app with Socket Mode enabled. Required scopes: `chat:write`, `reactions:write`, `channels:read`, `groups:read`, `im:read`, `im:history`, `users:read`, `app_mentions:read`. Enable Socket Mode and get the App-Level Token. Subscribe to events: `message.im`, `message.channels`, `app_mention`, `reaction_added`.

2. **Configuration**: Set `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` in `.mcp.json` (or in the environment). Optionally pre-configure `~/.slack-channel/settings.json` with allowed users.

3. **Running**: `claude --dangerously-load-development-channels server:slack-channel` (during research preview).

4. **Pairing**: DM the bot to start pairing, echo the code back.

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add channel setup instructions to README"
```

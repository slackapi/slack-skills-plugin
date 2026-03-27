import { describe, test, expect, beforeEach, mock } from 'bun:test'
import { Bridge } from '../src/bridge'
import { Gating } from '../src/gating'
import type { Settings } from '../src/settings'

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
        info: mock(() => Promise.resolve({ user: { real_name: 'Alice' } })),
      },
      conversations: {
        info: mock(() => Promise.resolve({ channel: { name: 'general' } })),
        join: mock(() => Promise.resolve({ ok: true })),
      },
    },
  }
}

describe('Bridge - event transformation', () => {
  let bridge: Bridge
  let mockSlack: ReturnType<typeof createMockSlackApp>
  let mockMcp: ReturnType<typeof createMockMcp>
  let gating: Gating
  let settings: Settings

  beforeEach(() => {
    settings = {
      gating: { mode: 'per-user', allowedUsers: ['U_ALLOWED'] },
      watchedChannels: ['C_WATCHED'],
    }
    gating = new Gating(settings)
    mockSlack = createMockSlackApp()
    mockMcp = createMockMcp()
    bridge = new Bridge(mockSlack as any, gating, settings)
    bridge.setMcpServer(mockMcp as any)
  })

  test('emits dm notification for allowed user DM', async () => {
    await bridge.handleMessage({
      user: 'U_ALLOWED',
      text: 'hello bot',
      channel: 'D_DM',
      channel_type: 'im',
      ts: '1234.5678',
    })

    expect(mockMcp.notification).toHaveBeenCalledTimes(1)
    const call = (mockMcp.notification as any).mock.calls[0]
    expect(call[0].method).toBe('notifications/claude/channel/message')
    expect(call[0].params.content).toContain('hello bot')
    expect(call[0].params.content).toContain('event="dm"')
  })

  test('drops messages from non-allowed users (not bootstrap)', async () => {
    await bridge.handleMessage({
      user: 'U_STRANGER',
      text: 'hello',
      channel: 'D_DM',
      channel_type: 'im',
      ts: '1234.5678',
    })

    expect(mockMcp.notification).not.toHaveBeenCalled()
  })

  test('emits message notification for watched channel', async () => {
    await bridge.handleMessage({
      user: 'U_ALLOWED',
      text: 'channel message',
      channel: 'C_WATCHED',
      channel_type: 'channel',
      ts: '1234.5678',
    })

    expect(mockMcp.notification).toHaveBeenCalledTimes(1)
    const call = (mockMcp.notification as any).mock.calls[0]
    expect(call[0].params.content).toContain('event="message"')
    expect(call[0].params.content).toContain('channel message')
  })

  test('drops messages from non-watched channels', async () => {
    await bridge.handleMessage({
      user: 'U_ALLOWED',
      text: 'ignored message',
      channel: 'C_OTHER',
      channel_type: 'channel',
      ts: '1234.5678',
    })

    expect(mockMcp.notification).not.toHaveBeenCalled()
  })

  test('updates lastActiveContext on DM', async () => {
    await bridge.handleMessage({
      user: 'U_ALLOWED',
      text: 'hello',
      channel: 'D_DM',
      channel_type: 'im',
      ts: '1234.5678',
    })

    // lastActiveContext should be set
    const ctx = bridge.lastActiveContext
    expect(ctx).not.toBeNull()
    expect(ctx!.userId).toBe('U_ALLOWED')
    expect(ctx!.channelId).toBe('D_DM')
  })
})

describe('Bridge - mention events', () => {
  let bridge: Bridge
  let mockSlack: ReturnType<typeof createMockSlackApp>
  let mockMcp: ReturnType<typeof createMockMcp>
  let gating: Gating
  let settings: Settings

  beforeEach(() => {
    settings = {
      gating: { mode: 'per-user', allowedUsers: ['U_ALLOWED'] },
      watchedChannels: [],
    }
    gating = new Gating(settings)
    mockSlack = createMockSlackApp()
    mockMcp = createMockMcp()
    bridge = new Bridge(mockSlack as any, gating, settings)
    bridge.setMcpServer(mockMcp as any)
  })

  test('forwards app_mention as mention event', async () => {
    await bridge.handleMention({
      user: 'U_ALLOWED',
      text: '<@UBOT> help me',
      channel: 'C_GENERAL',
      ts: '1234.5678',
    })

    expect(mockMcp.notification).toHaveBeenCalledTimes(1)
    const call = (mockMcp.notification as any).mock.calls[0]
    expect(call[0].params.content).toContain('event="mention"')
    expect(call[0].params.content).toContain('help me')
  })
})

describe('Bridge - permission verdict parsing', () => {
  let bridge: Bridge
  let mockSlack: ReturnType<typeof createMockSlackApp>
  let mockMcp: ReturnType<typeof createMockMcp>
  let gating: Gating
  let settings: Settings

  beforeEach(() => {
    settings = {
      gating: { mode: 'per-user', allowedUsers: ['U_ALLOWED'] },
      watchedChannels: [],
    }
    gating = new Gating(settings)
    mockSlack = createMockSlackApp()
    mockMcp = createMockMcp()
    bridge = new Bridge(mockSlack as any, gating, settings)
    bridge.setMcpServer(mockMcp as any)
  })

  test('recognizes "yes" as approval', async () => {
    // Set up a pending permission request
    await bridge.handlePermissionRequest({
      request_id: 'req-1',
      tool_name: 'bash',
      description: 'Run command',
      input_preview: 'ls -la',
    })

    // Simulate user replying "yes"
    await bridge.handleMessage({
      user: 'U_ALLOWED',
      text: 'yes',
      channel: 'D_DM',
      channel_type: 'im',
      ts: '2222.3333',
    })

    // Should have sent the permission verdict notification
    const calls = (mockMcp.notification as any).mock.calls
    // First call is the permission prompt forwarded to user, last is the verdict
    const verdictCall = calls.find(
      (c: any) => c[0].method === 'notifications/claude/channel/permission_verdict'
    )
    expect(verdictCall).toBeDefined()
    expect(verdictCall[0].params.approved).toBe(true)
  })

  test('recognizes "n" as rejection', async () => {
    await bridge.handlePermissionRequest({
      request_id: 'req-2',
      tool_name: 'bash',
      description: 'Run command',
      input_preview: 'rm -rf /',
    })

    await bridge.handleMessage({
      user: 'U_ALLOWED',
      text: 'n',
      channel: 'D_DM',
      channel_type: 'im',
      ts: '2222.3333',
    })

    const calls = (mockMcp.notification as any).mock.calls
    const verdictCall = calls.find(
      (c: any) => c[0].method === 'notifications/claude/channel/permission_verdict'
    )
    expect(verdictCall).toBeDefined()
    expect(verdictCall[0].params.approved).toBe(false)
  })

  test('recognizes "Y" (case insensitive) as approval', async () => {
    await bridge.handlePermissionRequest({
      request_id: 'req-3',
      tool_name: 'bash',
      description: 'Run command',
      input_preview: 'echo hi',
    })

    await bridge.handleMessage({
      user: 'U_ALLOWED',
      text: 'Y',
      channel: 'D_DM',
      channel_type: 'im',
      ts: '2222.3333',
    })

    const calls = (mockMcp.notification as any).mock.calls
    const verdictCall = calls.find(
      (c: any) => c[0].method === 'notifications/claude/channel/permission_verdict'
    )
    expect(verdictCall).toBeDefined()
    expect(verdictCall[0].params.approved).toBe(true)
  })

  test('does not treat "l" as a verdict (ambiguous with IDs)', async () => {
    await bridge.handlePermissionRequest({
      request_id: 'req-4',
      tool_name: 'bash',
      description: 'Run command',
      input_preview: 'echo test',
    })

    await bridge.handleMessage({
      user: 'U_ALLOWED',
      text: 'l',
      channel: 'D_DM',
      channel_type: 'im',
      ts: '2222.3333',
    })

    // 'l' should NOT be treated as a verdict; it should be forwarded as a regular message
    const calls = (mockMcp.notification as any).mock.calls
    const verdictCall = calls.find(
      (c: any) => c[0].method === 'notifications/claude/channel/permission_verdict'
    )
    expect(verdictCall).toBeUndefined()
  })
})

describe('Bridge - tool authorization', () => {
  let bridge: Bridge
  let mockSlack: ReturnType<typeof createMockSlackApp>
  let mockMcp: ReturnType<typeof createMockMcp>
  let gating: Gating
  let settings: Settings

  beforeEach(() => {
    settings = {
      gating: { mode: 'per-user', allowedUsers: ['U_ALLOWED'] },
      watchedChannels: ['C_WATCHED'],
    }
    gating = new Gating(settings)
    mockSlack = createMockSlackApp()
    mockMcp = createMockMcp()
    bridge = new Bridge(mockSlack as any, gating, settings)
    bridge.setMcpServer(mockMcp as any)
  })

  test('manage_access fails with no active context', async () => {
    const result = await bridge.handleToolCall('manage_access', {
      action: 'add_user',
      value: 'U_NEW',
    })

    expect(result.isError).toBe(true)
    expect(result.content[0].text).toContain('No active context')
  })

  test('manage_channels fails with no active context', async () => {
    const result = await bridge.handleToolCall('manage_channels', {
      action: 'watch',
      channel_id: 'C_NEW',
    })

    expect(result.isError).toBe(true)
    expect(result.content[0].text).toContain('No active context')
  })

  test('reply works without admin auth', async () => {
    const result = await bridge.handleToolCall('reply', {
      channel_id: 'C_GENERAL',
      text: 'Hello world',
    })

    expect(result.isError).toBeUndefined()
    expect(mockSlack.client.chat.postMessage).toHaveBeenCalledTimes(1)
  })
})

describe('Bridge - name resolution cache', () => {
  let bridge: Bridge
  let mockSlack: ReturnType<typeof createMockSlackApp>
  let mockMcp: ReturnType<typeof createMockMcp>
  let gating: Gating
  let settings: Settings

  beforeEach(() => {
    settings = {
      gating: { mode: 'per-user', allowedUsers: ['U_ALLOWED'] },
      watchedChannels: [],
    }
    gating = new Gating(settings)
    mockSlack = createMockSlackApp()
    mockMcp = createMockMcp()
    bridge = new Bridge(mockSlack as any, gating, settings)
    bridge.setMcpServer(mockMcp as any)
  })

  test('resolves user name and caches it', async () => {
    const name1 = await bridge.resolveUserName('U_ALICE')
    expect(name1).toBe('Alice')
    expect(mockSlack.client.users.info).toHaveBeenCalledTimes(1)

    // Second call should use cache
    const name2 = await bridge.resolveUserName('U_ALICE')
    expect(name2).toBe('Alice')
    expect(mockSlack.client.users.info).toHaveBeenCalledTimes(1)
  })

  test('resolves channel name and caches it', async () => {
    const name1 = await bridge.resolveChannelName('C_GEN')
    expect(name1).toBe('general')
    expect(mockSlack.client.conversations.info).toHaveBeenCalledTimes(1)

    // Second call should use cache
    const name2 = await bridge.resolveChannelName('C_GEN')
    expect(name2).toBe('general')
    expect(mockSlack.client.conversations.info).toHaveBeenCalledTimes(1)
  })
})

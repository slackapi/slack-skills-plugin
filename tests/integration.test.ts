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

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { TOOLS, handleToolCall } from '../src/reactions'

function createMockSlack() {
  return {
    reactions: {
      add: vi.fn(() => Promise.resolve({ ok: true })),
      remove: vi.fn(() => Promise.resolve({ ok: true })),
    },
  }
}

describe('TOOLS definitions', () => {
  test('exports slack_add_reaction and slack_remove_reaction', () => {
    const names = TOOLS.map(t => t.name)
    expect(names).toContain('slack_add_reaction')
    expect(names).toContain('slack_remove_reaction')
  })

  test('slack_add_reaction requires channel_id, message_ts, emoji_name', () => {
    const tool = TOOLS.find(t => t.name === 'slack_add_reaction')!
    expect(tool.inputSchema.required).toEqual(['channel_id', 'message_ts', 'emoji_name'])
  })

  test('slack_remove_reaction requires channel_id, message_ts, emoji_name', () => {
    const tool = TOOLS.find(t => t.name === 'slack_remove_reaction')!
    expect(tool.inputSchema.required).toEqual(['channel_id', 'message_ts', 'emoji_name'])
  })

  test('emoji_name description mentions no colons', () => {
    const tool = TOOLS.find(t => t.name === 'slack_add_reaction')!
    expect(tool.inputSchema.properties.emoji_name.description).toContain('without colons')
  })
})

describe('handleToolCall - slack_add_reaction', () => {
  let mockSlack: ReturnType<typeof createMockSlack>

  beforeEach(() => {
    mockSlack = createMockSlack()
  })

  test('calls reactions.add with correct params', async () => {
    await handleToolCall(mockSlack, 'slack_add_reaction', {
      channel_id: 'C123',
      message_ts: '1234.5678',
      emoji_name: 'thumbsup',
    })
    expect(mockSlack.reactions.add).toHaveBeenCalledWith({
      channel: 'C123',
      timestamp: '1234.5678',
      name: 'thumbsup',
    })
  })

  test('returns success response', async () => {
    const result = await handleToolCall(mockSlack, 'slack_add_reaction', {
      channel_id: 'C123',
      message_ts: '1234.5678',
      emoji_name: 'thumbsup',
    })
    expect(result.content[0].text).toBe('reaction added')
    expect(result.isError).toBeUndefined()
  })

  test('returns error response on API failure', async () => {
    mockSlack.reactions.add.mockRejectedValueOnce(new Error('already_reacted'))
    const result = await handleToolCall(mockSlack, 'slack_add_reaction', {
      channel_id: 'C123',
      message_ts: '1234.5678',
      emoji_name: 'thumbsup',
    })
    expect(result.content[0].text).toContain('already_reacted')
    expect(result.isError).toBe(true)
  })

  test('does not call reactions.remove', async () => {
    await handleToolCall(mockSlack, 'slack_add_reaction', {
      channel_id: 'C123',
      message_ts: '1234.5678',
      emoji_name: 'thumbsup',
    })
    expect(mockSlack.reactions.remove).not.toHaveBeenCalled()
  })
})

describe('handleToolCall - slack_remove_reaction', () => {
  let mockSlack: ReturnType<typeof createMockSlack>

  beforeEach(() => {
    mockSlack = createMockSlack()
  })

  test('calls reactions.remove with correct params', async () => {
    await handleToolCall(mockSlack, 'slack_remove_reaction', {
      channel_id: 'C456',
      message_ts: '9999.0001',
      emoji_name: 'eyes',
    })
    expect(mockSlack.reactions.remove).toHaveBeenCalledWith({
      channel: 'C456',
      timestamp: '9999.0001',
      name: 'eyes',
    })
  })

  test('returns success response', async () => {
    const result = await handleToolCall(mockSlack, 'slack_remove_reaction', {
      channel_id: 'C456',
      message_ts: '9999.0001',
      emoji_name: 'eyes',
    })
    expect(result.content[0].text).toBe('reaction removed')
    expect(result.isError).toBeUndefined()
  })

  test('returns error response on API failure', async () => {
    mockSlack.reactions.remove.mockRejectedValueOnce(new Error('no_reaction'))
    const result = await handleToolCall(mockSlack, 'slack_remove_reaction', {
      channel_id: 'C456',
      message_ts: '9999.0001',
      emoji_name: 'eyes',
    })
    expect(result.content[0].text).toContain('no_reaction')
    expect(result.isError).toBe(true)
  })

  test('does not call reactions.add', async () => {
    await handleToolCall(mockSlack, 'slack_remove_reaction', {
      channel_id: 'C456',
      message_ts: '9999.0001',
      emoji_name: 'eyes',
    })
    expect(mockSlack.reactions.add).not.toHaveBeenCalled()
  })
})

describe('handleToolCall - unknown tool', () => {
  test('returns error response', async () => {
    const mockSlack = createMockSlack()
    const result = await handleToolCall(mockSlack, 'slack_unknown_tool', {})
    expect(result.content[0].text).toContain('unknown tool')
    expect(result.isError).toBe(true)
  })

  test('does not call any Slack API', async () => {
    const mockSlack = createMockSlack()
    await handleToolCall(mockSlack, 'slack_unknown_tool', {})
    expect(mockSlack.reactions.add).not.toHaveBeenCalled()
    expect(mockSlack.reactions.remove).not.toHaveBeenCalled()
  })
})

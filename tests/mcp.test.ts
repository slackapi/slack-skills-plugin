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

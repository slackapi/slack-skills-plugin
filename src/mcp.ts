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
  mcp.setNotificationHandler(PermissionRequestSchema, async ({ params }) => {
    await bridge.handlePermissionRequest(params)
  })

  return mcp
}

export async function connectMcp(mcp: Server): Promise<void> {
  await mcp.connect(new StdioServerTransport())
}

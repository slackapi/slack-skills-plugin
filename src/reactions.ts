import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js'
import { WebClient } from '@slack/web-api'
import { fileURLToPath } from 'node:url'

interface SlackReactionsClient {
  reactions: {
    add: (params: { channel: string; timestamp: string; name: string }) => Promise<unknown>
    remove: (params: { channel: string; timestamp: string; name: string }) => Promise<unknown>
  }
}

export const TOOLS = [
  {
    name: 'slack_add_reaction',
    description: 'Add an emoji reaction to a Slack message',
    inputSchema: {
      type: 'object' as const,
      properties: {
        channel_id: { type: 'string', description: 'ID of the channel containing the message' },
        message_ts: { type: 'string', description: 'Timestamp of the message to react to' },
        emoji_name: { type: 'string', description: 'Emoji name without colons (e.g. thumbsup, white_check_mark, eyes)' },
      },
      required: ['channel_id', 'message_ts', 'emoji_name'],
    },
  },
  {
    name: 'slack_remove_reaction',
    description: 'Remove an emoji reaction from a Slack message',
    inputSchema: {
      type: 'object' as const,
      properties: {
        channel_id: { type: 'string', description: 'ID of the channel containing the message' },
        message_ts: { type: 'string', description: 'Timestamp of the message' },
        emoji_name: { type: 'string', description: 'Emoji name without colons (e.g. thumbsup, white_check_mark, eyes)' },
      },
      required: ['channel_id', 'message_ts', 'emoji_name'],
    },
  },
]

export async function handleToolCall(
  slack: SlackReactionsClient,
  name: string,
  args: Record<string, string>,
): Promise<{ content: Array<{ type: string; text: string }>; isError?: boolean }> {
  try {
    switch (name) {
      case 'slack_add_reaction':
        await slack.reactions.add({ channel: args.channel_id, timestamp: args.message_ts, name: args.emoji_name })
        return { content: [{ type: 'text', text: 'reaction added' }] }

      case 'slack_remove_reaction':
        await slack.reactions.remove({ channel: args.channel_id, timestamp: args.message_ts, name: args.emoji_name })
        return { content: [{ type: 'text', text: 'reaction removed' }] }

      default:
        throw new Error(`unknown tool: ${name}`)
    }
  } catch (err) {
    return { content: [{ type: 'text', text: `error: ${(err as Error).message}` }], isError: true }
  }
}

export function createServer(slack: SlackReactionsClient): Server {
  const server = new Server(
    { name: 'slack-reactions', version: '1.0.0' },
    { capabilities: { tools: {} } },
  )

  server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }))

  server.setRequestHandler(CallToolRequestSchema, async (req) => {
    const { name, arguments: args } = req.params
    return handleToolCall(slack, name, args as Record<string, string>)
  })

  return server
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const token = process.env.SLACK_BOT_TOKEN
  if (!token?.startsWith('xoxb-')) {
    console.error('[slack-reactions] SLACK_BOT_TOKEN is missing or invalid (must start with xoxb-)')
    process.exit(1)
  }

  const slack = new WebClient(token)
  const server = createServer(slack)
  await server.connect(new StdioServerTransport())
}

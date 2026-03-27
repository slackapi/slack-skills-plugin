import type { Server } from '@modelcontextprotocol/sdk/server/index.js'
import type { Settings } from './settings'
import { writeSettings } from './settings'
import type { Gating } from './gating'
import { writeFile, mkdir } from 'node:fs/promises'
import { dirname, join } from 'node:path'

interface SlackMessage {
  user: string
  text: string
  channel: string
  channel_type?: string
  ts: string
  thread_ts?: string
}

interface MentionEvent {
  user: string
  text: string
  channel: string
  ts: string
  thread_ts?: string
}

interface ReactionEvent {
  user: string
  reaction: string
  item: {
    channel: string
    ts: string
  }
}

interface PermissionRequest {
  request_id: string
  tool_name: string
  description: string
  input_preview: string
}

interface ActiveContext {
  userId: string
  channelId: string
  threadTs?: string
}

interface ToolResult {
  content: Array<{ type: string; text: string }>
  isError?: boolean
}

// Verdicts: yes/y approve, no/n reject. Exclude 'l' due to ID ambiguity.
const APPROVAL_PATTERN = /^(yes|y)$/i
const REJECTION_PATTERN = /^(no|n)$/i

export class Bridge {
  private slackApp: any
  mcp: Server | null = null
  lastActiveContext: ActiveContext | null = null

  private settings: Settings
  private settingsPath: string
  private gating: Gating

  private pendingPermission: {
    requestId: string
    toolName: string
    description: string
    inputPreview: string
  } | null = null

  private userNameCache: Map<string, string> = new Map()
  private channelNameCache: Map<string, string> = new Map()

  constructor(slackApp: any, gating: Gating, settings: Settings, settingsPath?: string) {
    this.slackApp = slackApp
    this.gating = gating
    this.settings = settings
    this.settingsPath = settingsPath ?? 'settings.json'
  }

  setMcpServer(mcp: Server): void {
    this.mcp = mcp
  }

  // ──────────────────────────────────────────────────
  // Message handling
  // ──────────────────────────────────────────────────

  async handleMessage(event: SlackMessage): Promise<void> {
    const { user, text, channel, channel_type, ts, thread_ts } = event

    // Bootstrap mode: first user to message becomes admin
    if (this.gating.isBootstrapMode()) {
      await this.handleBootstrapMessage(user, text, channel, ts)
      return
    }

    // Allowed user path
    if (this.gating.isAllowed(user)) {
      // Check for pending permission verdict
      if (this.pendingPermission) {
        const verdict = this.parseVerdict(text)
        if (verdict !== null) {
          await this.sendPermissionVerdict(this.pendingPermission.requestId, verdict)
          this.pendingPermission = null
          return
        }
      }

      // Update active context
      this.lastActiveContext = { userId: user, channelId: channel, threadTs: thread_ts }

      // DM -> emit dm notification
      if (channel_type === 'im') {
        await this.emitNotification('dm', user, channel, text, ts, thread_ts)
        return
      }

      // Watched channel -> emit message notification
      if (this.settings.watchedChannels.includes(channel)) {
        await this.emitNotification('message', user, channel, text, ts, thread_ts)
        return
      }

      // Not a DM and not a watched channel -> drop
      return
    }

    // Not allowed user -> attempt pairing response
    await this.handlePairingResponse(user, text, channel)
  }

  async handleMention(event: MentionEvent): Promise<void> {
    const { user, text, channel, ts, thread_ts } = event

    // Update active context
    this.lastActiveContext = { userId: user, channelId: channel, threadTs: thread_ts }

    await this.emitNotification('mention', user, channel, text, ts, thread_ts)
  }

  async handleReaction(event: ReactionEvent): Promise<void> {
    const { user, reaction, item } = event

    if (!this.gating.isAllowed(user)) return

    this.lastActiveContext = { userId: user, channelId: item.channel }

    const userName = await this.resolveUserName(user)
    const content = `<channel source="slack" event="reaction" user="${userName}" user_id="${user}" channel_id="${item.channel}" timestamp="${item.ts}" emoji="${reaction}">`

    this.mcp!.notification({
      method: 'notifications/claude/channel/message',
      params: { content },
    })
  }

  // ──────────────────────────────────────────────────
  // Tool call handling
  // ──────────────────────────────────────────────────

  async handleToolCall(name: string, args: Record<string, string>): Promise<ToolResult> {
    switch (name) {
      case 'reply':
        return this.handleReply(args)
      case 'react':
        return this.handleReact(args)
      case 'manage_access':
        return this.handleManageAccess(args)
      case 'manage_channels':
        return this.handleManageChannels(args)
      default:
        return {
          content: [{ type: 'text', text: `Unknown tool: ${name}` }],
          isError: true,
        }
    }
  }

  // ──────────────────────────────────────────────────
  // Permission relay
  // ──────────────────────────────────────────────────

  async handlePermissionRequest(params: PermissionRequest): Promise<void> {
    this.pendingPermission = {
      requestId: params.request_id,
      toolName: params.tool_name,
      description: params.description,
      inputPreview: params.input_preview,
    }

    // Forward the permission prompt to the active user's DM
    if (this.lastActiveContext) {
      const prompt = [
        `*Permission Request*`,
        `Tool: \`${params.tool_name}\``,
        `Description: ${params.description}`,
        `Preview: \`${params.input_preview}\``,
        `Reply *yes* or *no* to approve/reject.`,
      ].join('\n')

      await this.slackApp.client.chat.postMessage({
        channel: this.lastActiveContext.channelId,
        text: prompt,
      })
    }
  }

  // ──────────────────────────────────────────────────
  // Name resolution
  // ──────────────────────────────────────────────────

  async resolveUserName(userId: string): Promise<string> {
    const cached = this.userNameCache.get(userId)
    if (cached) return cached

    try {
      const result = await this.slackApp.client.users.info({ user: userId })
      const name = result.user?.real_name || result.user?.name || userId
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
      const name = result.channel?.name || channelId
      this.channelNameCache.set(channelId, name)
      return name
    } catch {
      return channelId
    }
  }

  // ──────────────────────────────────────────────────
  // Private helpers
  // ──────────────────────────────────────────────────

  private async emitNotification(
    eventType: string,
    userId: string,
    channelId: string,
    text: string,
    ts: string,
    threadTs?: string,
  ): Promise<void> {
    const userName = await this.resolveUserName(userId)
    const threadAttr = threadTs ? ` thread_ts="${threadTs}"` : ''
    const content = `<channel source="slack" event="${eventType}" user="${userName}" user_id="${userId}" channel_id="${channelId}" ts="${ts}"${threadAttr}>${text}</channel>`

    this.mcp!.notification({
      method: 'notifications/claude/channel/message',
      params: { content },
    })
  }

  private async handleBootstrapMessage(
    userId: string,
    text: string,
    channel: string,
    ts: string,
  ): Promise<void> {
    // If there's a pending pairing code, check if this is the code
    if (this.gating.hasPendingPairingCode()) {
      const code = text.trim().toUpperCase()
      if (this.gating.verifyPairingCode(code, userId)) {
        this.gating.addUser(userId)
        await this.persistSettings()

        await this.slackApp.client.chat.postMessage({
          channel,
          text: `Paired successfully! You are now the admin.`,
        })

        // Emit a notification so Claude knows
        this.lastActiveContext = { userId, channelId: channel }
        await this.emitNotification('dm', userId, channel, '[User paired as admin]', ts)
      }
      return
    }

    // Generate a pairing code and emit it as a notification for Claude to display
    const code = this.gating.createPairingCode(userId)
    if (code) {
      await this.writePairingCodeFile(code)

      this.mcp!.notification({
        method: 'notifications/claude/channel/message',
        params: {
          content: `<channel source="slack" event="bootstrap" user_id="${userId}" channel_id="${channel}">A new user wants to pair. Pairing code: ${code}. Ask the operator to verify this code in the terminal.</channel>`,
        },
      })
    }
  }

  private async handlePairingResponse(
    userId: string,
    text: string,
    channel: string,
  ): Promise<void> {
    const code = text.trim().toUpperCase()
    if (this.gating.verifyPairingCode(code, userId)) {
      this.gating.addUser(userId)
      await this.persistSettings()

      await this.slackApp.client.chat.postMessage({
        channel,
        text: `Paired successfully! You now have access.`,
      })
    }
  }

  private parseVerdict(text: string): boolean | null {
    const trimmed = text.trim()
    if (APPROVAL_PATTERN.test(trimmed)) return true
    if (REJECTION_PATTERN.test(trimmed)) return false
    return null
  }

  private async sendPermissionVerdict(requestId: string, approved: boolean): Promise<void> {
    this.mcp!.notification({
      method: 'notifications/claude/channel/permission_verdict',
      params: {
        request_id: requestId,
        approved,
      },
    })
  }

  private checkAdminAuth(): ToolResult | null {
    if (!this.lastActiveContext) {
      return {
        content: [{ type: 'text', text: 'No active context — cannot verify admin.' }],
        isError: true,
      }
    }
    if (!this.gating.isAllowed(this.lastActiveContext.userId)) {
      return {
        content: [{ type: 'text', text: 'Unauthorized — only allowed users can manage access.' }],
        isError: true,
      }
    }
    return null
  }

  private async handleReply(args: Record<string, string>): Promise<ToolResult> {
    const { channel_id, text, thread_ts } = args

    await this.slackApp.client.chat.postMessage({
      channel: channel_id,
      text,
      ...(thread_ts ? { thread_ts } : {}),
    })

    return {
      content: [{ type: 'text', text: 'Message sent.' }],
    }
  }

  private async handleReact(args: Record<string, string>): Promise<ToolResult> {
    const { channel_id, timestamp, emoji } = args

    await this.slackApp.client.reactions.add({
      channel: channel_id,
      timestamp,
      name: emoji,
    })

    return {
      content: [{ type: 'text', text: `Reacted with :${emoji}:` }],
    }
  }

  private async handleManageAccess(args: Record<string, string>): Promise<ToolResult> {
    const authError = this.checkAdminAuth()
    if (authError) return authError

    const { action, value } = args

    switch (action) {
      case 'add_user':
        this.gating.addUser(value)
        await this.persistSettings()
        return {
          content: [{ type: 'text', text: `User ${value} added to allowlist.` }],
        }

      case 'remove_user':
        this.gating.removeUser(value)
        await this.persistSettings()
        return {
          content: [{ type: 'text', text: `User ${value} removed from allowlist.` }],
        }

      case 'pair_user': {
        const code = this.gating.createPairingCode(value)
        if (!code) {
          return {
            content: [{ type: 'text', text: 'Failed to create pairing code (one may already be pending).' }],
            isError: true,
          }
        }

        // Send the code via ephemeral message to the requesting user
        if (this.lastActiveContext) {
          await this.slackApp.client.chat.postEphemeral({
            channel: this.lastActiveContext.channelId,
            user: this.lastActiveContext.userId,
            text: `Pairing code for <@${value}>: \`${code}\` (expires in 5 minutes)`,
          })
        }

        return {
          content: [{ type: 'text', text: `Pairing code created for ${value}. Sent via ephemeral message.` }],
        }
      }

      default:
        return {
          content: [{ type: 'text', text: `Unknown action: ${action}` }],
          isError: true,
        }
    }
  }

  private async handleManageChannels(args: Record<string, string>): Promise<ToolResult> {
    const authError = this.checkAdminAuth()
    if (authError) return authError

    const { action, channel_id } = args

    switch (action) {
      case 'watch': {
        if (!this.settings.watchedChannels.includes(channel_id)) {
          this.settings.watchedChannels.push(channel_id)
          await this.persistSettings()

          // Join the channel so the bot receives messages
          try {
            await this.slackApp.client.conversations.join({ channel: channel_id })
          } catch {
            // Already in channel or can't join — not fatal
          }
        }

        const name = await this.resolveChannelName(channel_id)
        return {
          content: [{ type: 'text', text: `Now watching #${name} (${channel_id}).` }],
        }
      }

      case 'unwatch': {
        this.settings.watchedChannels = this.settings.watchedChannels.filter(
          (c) => c !== channel_id,
        )
        await this.persistSettings()

        const name = await this.resolveChannelName(channel_id)
        return {
          content: [{ type: 'text', text: `Stopped watching #${name} (${channel_id}).` }],
        }
      }

      default:
        return {
          content: [{ type: 'text', text: `Unknown action: ${action}` }],
          isError: true,
        }
    }
  }

  private async persistSettings(): Promise<void> {
    const updated: Settings = {
      gating: {
        mode: 'per-user',
        allowedUsers: this.gating.getAllowedUsers(),
      },
      watchedChannels: this.settings.watchedChannels,
    }
    this.settings = updated

    try {
      await writeSettings(this.settingsPath, updated)
    } catch {
      // Settings write failure is non-fatal in runtime
    }
  }

  private async writePairingCodeFile(code: string): Promise<void> {
    try {
      const dir = dirname(this.settingsPath)
      await mkdir(dir, { recursive: true })
      const codePath = join(dir, '.pairing-code')
      await writeFile(codePath, code)
    } catch {
      // Non-fatal
    }
  }
}

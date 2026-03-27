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
        await this.mcp!.notification({
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

    await this.mcp!.notification({
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

    await this.mcp!.notification({
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

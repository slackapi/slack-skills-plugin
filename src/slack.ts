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
  app.event('message', async ({ event }) => {
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

  // Permission approval/denial buttons
  app.action('permission_approve', async ({ action, body, ack }) => {
    await ack()
    try {
      const userId = (body as any).user?.id || ''
      const requestId = (action as any).value
      const channelId = (body as any).channel?.id || ''
      const messageTs = (body as any).message?.ts || ''
      await bridge.handlePermissionAction(requestId, true, channelId, messageTs, userId)
    } catch (err) {
      console.error('[slack-channel] error handling permission approve:', err)
    }
  })

  app.action('permission_deny', async ({ action, body, ack }) => {
    await ack()
    try {
      const userId = (body as any).user?.id || ''
      const requestId = (action as any).value
      const channelId = (body as any).channel?.id || ''
      const messageTs = (body as any).message?.ts || ''
      await bridge.handlePermissionAction(requestId, false, channelId, messageTs, userId)
    } catch (err) {
      console.error('[slack-channel] error handling permission deny:', err)
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

export async function getBotUserId(app: App): Promise<string> {
  const authResult = await app.client.auth.test()
  console.error(`[slack-channel] authenticated as ${authResult.user} (${authResult.user_id})`)
  return authResult.user_id || ''
}

export async function startSlackApp(app: App): Promise<void> {
  await app.start()
  console.error('[slack-channel] Socket Mode connected')
}

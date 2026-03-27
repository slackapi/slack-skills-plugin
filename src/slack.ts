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

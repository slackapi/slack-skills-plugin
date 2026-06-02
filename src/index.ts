#!/usr/bin/env node
import { readSettings } from './settings'
import { Gating } from './gating'
import { createMcpServer, connectMcp } from './mcp'
import { createSlackApp, registerEventHandlers, getBotUserId, startSlackApp } from './slack'
import { Bridge } from './bridge'

// --- Validate environment ---
const botToken = process.env.SLACK_BOT_TOKEN
const appToken = process.env.SLACK_APP_TOKEN

if (!botToken || !botToken.startsWith('xoxb-')) {
  console.error('[slack-channel] SLACK_BOT_TOKEN is missing or invalid (must start with xoxb-)')
  process.exit(1)
}

if (!appToken || !appToken.startsWith('xapp-')) {
  console.error('[slack-channel] SLACK_APP_TOKEN is missing or invalid (must start with xapp-)')
  process.exit(1)
}

// --- Load settings ---
const settingsPath = process.env.SLACK_CHANNEL_SETTINGS_PATH
  || `${process.env.HOME}/.slack-channel/settings.json`

const settings = await readSettings(settingsPath)

// --- Wire up modules ---
const gating = new Gating(settings)
const slackApp = createSlackApp(botToken, appToken)

// Bridge is created without MCP reference. setMcpServer() wires it up after MCP is created.
const bridge = new Bridge(slackApp, gating, settings, settingsPath)
const mcp = createMcpServer(bridge)
bridge.setMcpServer(mcp)

// --- Get bot identity and register handlers before connecting ---
const botUserId = await getBotUserId(slackApp)
registerEventHandlers(slackApp, bridge, botUserId)

// --- Start Slack (Socket Mode) — handlers already registered ---
await startSlackApp(slackApp)

// --- Connect MCP (stdio) after Slack is confirmed connected ---
await connectMcp(mcp)

if (gating.isBootstrapMode()) {
  console.error('[slack-channel] bootstrap mode: DM the bot to start pairing')
}

console.error('[slack-channel] ready')

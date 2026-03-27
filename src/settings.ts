import { z } from 'zod'
import { readFile, writeFile, mkdir, rename } from 'node:fs/promises'
import { dirname, join } from 'node:path'

const GatingSchema = z.object({
  mode: z.literal('per-user'),
  allowedUsers: z.array(z.string()),
})

const SettingsSchema = z.object({
  gating: GatingSchema,
  watchedChannels: z.array(z.string()),
})

export type Settings = z.infer<typeof SettingsSchema>

export const DEFAULT_SETTINGS: Settings = {
  gating: { mode: 'per-user', allowedUsers: [] },
  watchedChannels: [],
}

export async function readSettings(path: string): Promise<Settings> {
  try {
    const raw = await readFile(path, 'utf-8')
    const parsed = JSON.parse(raw)
    return SettingsSchema.parse(parsed)
  } catch {
    return { ...DEFAULT_SETTINGS }
  }
}

export async function writeSettings(path: string, settings: Settings): Promise<void> {
  const dir = dirname(path)
  await mkdir(dir, { recursive: true })
  const tmp = join(dir, `.settings.tmp.${process.pid}`)
  await writeFile(tmp, JSON.stringify(settings, null, 2))
  await rename(tmp, path)
}

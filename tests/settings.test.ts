import { describe, test, expect, beforeEach, afterEach } from 'vitest'
import { readSettings, writeSettings, DEFAULT_SETTINGS, type Settings } from '../src/settings'
import { mkdtemp, rm, writeFile } from 'node:fs/promises'
import { join } from 'node:path'
import { tmpdir } from 'node:os'

describe('readSettings', () => {
  let dir: string

  beforeEach(async () => {
    dir = await mkdtemp(join(tmpdir(), 'settings-test-'))
  })

  afterEach(async () => {
    await rm(dir, { recursive: true })
  })

  test('returns defaults when file does not exist', async () => {
    const settings = await readSettings(join(dir, 'settings.json'))
    expect(settings).toEqual(DEFAULT_SETTINGS)
  })

  test('reads valid settings file', async () => {
    const path = join(dir, 'settings.json')
    const data: Settings = {
      gating: { mode: 'per-user', allowedUsers: ['U123'] },
      watchedChannels: ['C456'],
    }
    await writeFile(path, JSON.stringify(data))
    const settings = await readSettings(path)
    expect(settings.gating.allowedUsers).toEqual(['U123'])
    expect(settings.watchedChannels).toEqual(['C456'])
  })

  test('returns defaults on corrupted JSON', async () => {
    const path = join(dir, 'settings.json')
    await writeFile(path, 'not valid json{{{')
    const settings = await readSettings(path)
    expect(settings).toEqual(DEFAULT_SETTINGS)
  })

  test('returns defaults on invalid schema', async () => {
    const path = join(dir, 'settings.json')
    await writeFile(path, JSON.stringify({ gating: { mode: 'invalid' } }))
    const settings = await readSettings(path)
    expect(settings).toEqual(DEFAULT_SETTINGS)
  })
})

describe('writeSettings', () => {
  let dir: string

  beforeEach(async () => {
    dir = await mkdtemp(join(tmpdir(), 'settings-test-'))
  })

  afterEach(async () => {
    await rm(dir, { recursive: true })
  })

  test('writes and reads back settings', async () => {
    const path = join(dir, 'settings.json')
    const data: Settings = {
      gating: { mode: 'per-user', allowedUsers: ['UABC'] },
      watchedChannels: ['CDEF'],
    }
    await writeSettings(path, data)
    const result = await readSettings(path)
    expect(result).toEqual(data)
  })

  test('creates parent directories if missing', async () => {
    const path = join(dir, 'nested', 'deep', 'settings.json')
    await writeSettings(path, DEFAULT_SETTINGS)
    const result = await readSettings(path)
    expect(result).toEqual(DEFAULT_SETTINGS)
  })
})

import { describe, test, expect, beforeEach } from 'bun:test'
import { Gating } from '../src/gating'
import { DEFAULT_SETTINGS, type Settings } from '../src/settings'

describe('Gating', () => {
  let settings: Settings
  let gating: Gating

  beforeEach(() => {
    settings = {
      gating: { mode: 'per-user', allowedUsers: ['U_ALLOWED'] },
      watchedChannels: [],
    }
    gating = new Gating(settings)
  })

  test('allows users in the allowlist', () => {
    expect(gating.isAllowed('U_ALLOWED')).toBe(true)
  })

  test('rejects users not in the allowlist', () => {
    expect(gating.isAllowed('U_STRANGER')).toBe(false)
  })

  test('detects bootstrap mode when allowlist is empty', () => {
    gating = new Gating(DEFAULT_SETTINGS)
    expect(gating.isBootstrapMode()).toBe(true)
  })

  test('not in bootstrap mode when allowlist has users', () => {
    expect(gating.isBootstrapMode()).toBe(false)
  })

  test('addUser adds to allowlist and exits bootstrap', () => {
    gating = new Gating(DEFAULT_SETTINGS)
    expect(gating.isBootstrapMode()).toBe(true)
    gating.addUser('U_NEW')
    expect(gating.isAllowed('U_NEW')).toBe(true)
    expect(gating.isBootstrapMode()).toBe(false)
  })

  test('removeUser removes from allowlist', () => {
    gating.removeUser('U_ALLOWED')
    expect(gating.isAllowed('U_ALLOWED')).toBe(false)
  })
})

describe('Pairing', () => {
  let gating: Gating

  beforeEach(() => {
    gating = new Gating(DEFAULT_SETTINGS)
  })

  test('generates a 6-character alphanumeric code', () => {
    const code = gating.createPairingCode('U_TARGET')
    expect(code).toMatch(/^[A-Z0-9]{6}$/)
  })

  test('verifies a valid code for the correct user', () => {
    const code = gating.createPairingCode('U_TARGET')
    expect(gating.verifyPairingCode(code!, 'U_TARGET')).toBe(true)
  })

  test('rejects a valid code for the wrong user', () => {
    const code = gating.createPairingCode('U_TARGET')
    expect(gating.verifyPairingCode(code!, 'U_OTHER')).toBe(false)
  })

  test('rejects an invalid code', () => {
    gating.createPairingCode('U_TARGET')
    expect(gating.verifyPairingCode('ZZZZZZ', 'U_TARGET')).toBe(false)
  })

  test('code is consumed after verification', () => {
    const code = gating.createPairingCode('U_TARGET')
    expect(gating.verifyPairingCode(code!, 'U_TARGET')).toBe(true)
    expect(gating.verifyPairingCode(code!, 'U_TARGET')).toBe(false)
  })

  test('expired codes are rejected', () => {
    const code = gating.createPairingCode('U_TARGET', Date.now() - 6 * 60 * 1000)
    expect(gating.verifyPairingCode(code!, 'U_TARGET')).toBe(false)
  })

  test('only one code active during bootstrap', () => {
    const code1 = gating.createPairingCode('U_FIRST')
    const code2 = gating.createPairingCode('U_SECOND')
    expect(code2).toBeNull()
    expect(gating.verifyPairingCode(code1!, 'U_FIRST')).toBe(true)
  })

  test('hasPendingPairingCode returns true when code is active', () => {
    gating.createPairingCode('U_TARGET')
    expect(gating.hasPendingPairingCode()).toBe(true)
  })

  test('multiple codes allowed when not in bootstrap mode', () => {
    gating.addUser('U_ADMIN')
    const code1 = gating.createPairingCode('U_FIRST')
    const code2 = gating.createPairingCode('U_SECOND')
    expect(code1).not.toBeNull()
    expect(code2).not.toBeNull()
  })
})

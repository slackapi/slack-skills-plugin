import { randomBytes } from 'node:crypto'
import type { Settings } from './settings'

const CODE_TTL_MS = 5 * 60 * 1000 // 5 minutes
const CODE_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789' // no 0/O/1/I/L ambiguity

interface PendingCode {
  userId: string
  timestamp: number
}

export class Gating {
  private allowedUsers: Set<string>
  private pendingCodes: Map<string, PendingCode> = new Map()

  constructor(settings: Settings) {
    this.allowedUsers = new Set(settings.gating.allowedUsers)
  }

  isAllowed(userId: string): boolean {
    return this.allowedUsers.has(userId)
  }

  isBootstrapMode(): boolean {
    return this.allowedUsers.size === 0
  }

  addUser(userId: string): void {
    this.allowedUsers.add(userId)
  }

  removeUser(userId: string): void {
    this.allowedUsers.delete(userId)
  }

  getAllowedUsers(): string[] {
    return [...this.allowedUsers]
  }

  createPairingCode(userId: string, now: number = Date.now()): string | null {
    this.pruneExpired(now)

    // In bootstrap mode, only one code at a time
    if (this.isBootstrapMode() && this.pendingCodes.size > 0) {
      return null
    }

    const bytes = randomBytes(6)
    const code = Array.from(bytes, (b) => CODE_CHARS[b % CODE_CHARS.length]).join('')

    this.pendingCodes.set(code, { userId, timestamp: now })
    return code
  }

  verifyPairingCode(code: string, userId: string): boolean {
    this.pruneExpired()
    const entry = this.pendingCodes.get(code.toUpperCase())
    if (!entry || entry.userId !== userId) return false
    this.pendingCodes.delete(code.toUpperCase())
    return true
  }

  hasPendingPairingCode(): boolean {
    this.pruneExpired()
    return this.pendingCodes.size > 0
  }

  private pruneExpired(now: number = Date.now()): void {
    for (const [code, entry] of this.pendingCodes) {
      if (now - entry.timestamp > CODE_TTL_MS) {
        this.pendingCodes.delete(code)
      }
    }
  }
}

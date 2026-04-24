/**
 * Sync service - persists data to backend for cross-device syncing.
 * Falls back silently to localStorage-only if backend is unreachable.
 */
import axios from 'axios'

const BACKEND = 'https://backend-production-2e5d.up.railway.app'

const sync = axios.create({
  baseURL: BACKEND,
  timeout: 15000,
})

// ── Works ─────────────────────────────────────────────────────────────

export async function syncPushWork(work: Record<string, unknown>): Promise<void> {
  try {
    await sync.post('/sync/works', work)
  } catch (err) {
    console.warn('syncPushWork failed (offline):', err)
  }
}

export async function syncFetchWorks(): Promise<Record<string, unknown>[]> {
  try {
    const { data } = await sync.get('/sync/works')
    return data.items || []
  } catch {
    return []
  }
}

// ── Listings ──────────────────────────────────────────────────────────

export async function syncPushListing(listing: Record<string, unknown>): Promise<void> {
  try {
    await sync.post('/sync/listings', listing)
  } catch (err) {
    console.warn('syncPushListing failed (offline):', err)
  }
}

export async function syncFetchListings(): Promise<Record<string, unknown>[]> {
  try {
    const { data } = await sync.get('/sync/listings')
    return data.items || []
  } catch {
    return []
  }
}

export async function syncFetchListing(id: number): Promise<Record<string, unknown> | null> {
  try {
    const { data } = await sync.get(`/sync/listings/${id}`)
    return data
  } catch {
    return null
  }
}

export async function syncDeleteListing(id: number): Promise<void> {
  try {
    await sync.delete(`/sync/listings/${id}`)
  } catch (err) {
    console.warn('syncDeleteListing failed:', err)
  }
}

// ── Purchases ─────────────────────────────────────────────────────────

export async function syncPushPurchase(purchase: Record<string, unknown>): Promise<void> {
  try {
    await sync.post('/sync/purchases', purchase)
  } catch (err) {
    console.warn('syncPushPurchase failed (offline):', err)
  }
}

export async function syncFetchPurchases(buyerId?: number): Promise<Record<string, unknown>[]> {
  try {
    const { data } = await sync.get('/sync/purchases', {
      params: buyerId ? { buyer_id: buyerId } : {},
    })
    return data.items || []
  } catch {
    return []
  }
}

// ── Requests ──────────────────────────────────────────────────────────

export async function syncPushRequest(req: Record<string, unknown>): Promise<void> {
  try {
    await sync.post('/sync/requests', req)
  } catch (err) {
    console.warn('syncPushRequest failed (offline):', err)
  }
}

export async function syncFetchRequests(): Promise<Record<string, unknown>[]> {
  try {
    const { data } = await sync.get('/sync/requests')
    return data.items || []
  } catch {
    return []
  }
}

// ── Stats ─────────────────────────────────────────────────────────────

export async function syncFetchStats(): Promise<Record<string, unknown> | null> {
  try {
    const { data } = await sync.get('/sync/stats')
    return data
  } catch {
    return null
  }
}

import axios, { AxiosInstance } from 'axios'

// Determine API base URL based on environment
function getApiBaseUrl(): string {
  // If VITE_API_URL is explicitly set in environment variables, use it
  const envUrl = import.meta.env.VITE_API_URL

  // Check if we're in production (not localhost)
  const isLocalhost = window.location.hostname === 'localhost' ||
                     window.location.hostname === '127.0.0.1'

  // If env URL is set and we're in development, use it
  if (envUrl && isLocalhost) {
    return envUrl
  }

  // In production (Railway or similar), detect backend URL
  if (!isLocalhost) {
    const hostname = window.location.hostname

    // Railway pattern: replace '-production' or similar with backend service name
    if (hostname.includes('railway.app') || hostname.includes('up.railway.app')) {
      // Try to construct backend URL
      // Pattern: artlockr-frontend-production.up.railway.app -> artlockr-backend-production.up.railway.app
      const backendHostname = hostname.replace(/frontend/i, 'backend')
      return `https://${backendHostname}`
    }

    // For custom domains, use same origin (backend must be on same domain)
    console.log('ℹ️ Using same origin for API calls:', window.location.origin)
    return window.location.origin
  }

  // Default fallback for local development
  return 'http://localhost:8000'
}

const BASE = getApiBaseUrl()

const http: AxiosInstance = axios.create({ baseURL: BASE })

// Log API base URL for debugging
console.log('🔗 API Base URL:', BASE)
console.log('📍 Current hostname:', window.location.hostname)
console.log('🌍 Environment mode:', import.meta.env.MODE)

// ── Auth / Profiles ───────────────────────────────────────────────────────────

export const register = (
  email: string,
  username: string,
  password: string,
  role: 'artist' | 'company',
  company_name?: string,
) =>
  http.post('/profiles/register', null, {
    params: { email, username, password, role, company_name },
  })

export const login = (email: string, password: string) =>
  http.post('/profiles/login', null, { params: { email, password } })

export const getArtistProfile = (userId: number) =>
  http.get(`/profiles/artist/${userId}`)

export const getCompanyProfile = (userId: number) =>
  http.get(`/profiles/company/${userId}`)

export const updateArtistProfile = (userId: number, data: Record<string, unknown>) =>
  http.put(`/profiles/artist/${userId}`, null, { params: data })

export const updateCompanyProfile = (userId: number, data: Record<string, unknown>) =>
  http.put(`/profiles/company/${userId}`, null, { params: data })

// ── Marketplace ───────────────────────────────────────────────────────────────

export const getListings = (params?: Record<string, unknown>) =>
  http.get('/marketplace/listings', { params })

export const getListing = (id: number) =>
  http.get(`/marketplace/listings/${id}`)

export const getStats = () =>
  http.get('/marketplace/stats')

export const uploadWork = (formData: FormData) =>
  http.post('/marketplace/works/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000, // 60 second timeout
  })

export const createListing = (formData: FormData) =>
  http.post('/marketplace/listings/create', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000, // 30 second timeout
  })

export const purchaseListing = (listingId: number, buyerId: number) =>
  http.post(`/marketplace/listings/${listingId}/purchase`, null, {
    params: { buyer_id: buyerId },
  })

export const getMyPurchases = (buyerId: number) =>
  http.get('/marketplace/purchases', { params: { buyer_id: buyerId } })

export const verifyLicense = (licenseKey: string) =>
  http.get(`/marketplace/license/${licenseKey}`)

// ── Public Datasets ───────────────────────────────────────────────────────────

export const getPublicDatasets = (params?: Record<string, unknown>) =>
  http.get('/marketplace/public-datasets', { params })

export const searchWikimedia = (q: string, limit = 20) =>
  http.get('/marketplace/public-datasets/search/wikimedia', { params: { q, limit } })

// ── Stripe ────────────────────────────────────────────────────────────────────

export const startStripeOnboarding = (userId: number) =>
  http.post('/stripe/connect/onboard', null, { params: { user_id: userId } })

export const getStripeStatus = (userId: number) =>
  http.get('/stripe/connect/status', { params: { user_id: userId } })

export const getStripeDashboard = (userId: number) =>
  http.get('/stripe/connect/dashboard', { params: { user_id: userId } })

export const createStripeCustomer = (userId: number) =>
  http.post('/stripe/customer/create', null, { params: { user_id: userId } })

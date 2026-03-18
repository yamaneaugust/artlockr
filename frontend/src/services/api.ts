import axios, { AxiosInstance } from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const http: AxiosInstance = axios.create({ baseURL: BASE })

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
  })

export const createListing = (formData: FormData) =>
  http.post('/marketplace/listings/create', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
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

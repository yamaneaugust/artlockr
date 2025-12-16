import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'
import { useAuthStore } from '../store/authStore'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = useAuthStore.getState().token
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Handle auth errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          useAuthStore.getState().logout()
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  // Artwork endpoints
  async uploadArtwork(formData: FormData) {
    return this.client.post('/upload-artwork-private', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  }

  async getArtworks() {
    return this.client.get('/artworks')
  }

  async getArtwork(artworkId: string) {
    return this.client.get(`/artworks/${artworkId}`)
  }

  async deleteArtwork(artworkId: string) {
    return this.client.delete(`/artworks/${artworkId}`)
  }

  // Detection endpoints
  async detectCopyright(artworkId: string, useMultiMetric = true) {
    const endpoint = useMultiMetric
      ? `/detect-copyright-multimetric/${artworkId}`
      : `/detect-copyright-fast/${artworkId}`
    return this.client.post(endpoint)
  }

  async getDetectionResults(artworkId: string) {
    return this.client.get(`/detection-results/${artworkId}`)
  }

  // Privacy endpoints
  async getMyData() {
    return this.client.get('/privacy/my-data')
  }

  async deleteAllData() {
    return this.client.post('/privacy/delete-all')
  }

  async verifyProof(proofHash: string) {
    return this.client.get(`/privacy/verify-proof/${proofHash}`)
  }

  // Consent endpoints
  async grantConsent(consentType: string) {
    return this.client.post('/consent/grant', { consent_type: consentType })
  }

  async grantBatchConsent(consentTypes: string[]) {
    return this.client.post('/consent/grant-batch', { consent_types: consentTypes })
  }

  async getConsentStatus() {
    return this.client.get('/consent/status')
  }

  async withdrawConsent(consentType: string) {
    return this.client.post(`/consent/withdraw/${consentType}`)
  }

  // Cookie endpoints
  async getCookiePolicy() {
    return this.client.get('/cookies/policy')
  }

  async setCookiePreferences(preferences: Record<string, boolean>) {
    return this.client.post('/cookies/preferences', { preferences })
  }

  async getCookiePreferences() {
    return this.client.get('/cookies/preferences')
  }

  // Security endpoints
  async blockOrganization(organizationName: string, reason: string) {
    return this.client.post('/block-organization', {
      organization_name: organizationName,
      reason,
    })
  }

  async getBlockedOrganizations() {
    return this.client.get('/blocked-organizations')
  }

  async getIPReputation(ip: string) {
    return this.client.get(`/ip-reputation/${ip}`)
  }

  async getSecurityAnalytics() {
    return this.client.get('/security/analytics')
  }

  // Admin endpoints
  async getArtStyles() {
    return this.client.get('/art-styles')
  }

  async getFAISSStats() {
    return this.client.get('/faiss/index-stats')
  }

  async getComplianceDashboard() {
    return this.client.get('/compliance/dashboard')
  }
}

export const api = new ApiClient()

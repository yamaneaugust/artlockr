import { useState, useEffect } from 'react'
import { Shield, Lock, Download, Trash2, CheckCircle2, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import toast from 'react-hot-toast'

interface ConsentStatus {
  [key: string]: {
    granted: boolean
    timestamp: string
    version: string
  }
}

const CONSENT_TYPES = [
  {
    type: 'feature_extraction',
    label: 'Feature Extraction',
    description: 'Allow extraction of mathematical features from your artwork',
    required: true,
  },
  {
    type: 'copyright_detection',
    label: 'Copyright Detection',
    description: 'Enable automated copyright detection across AI-generated images',
    required: true,
  },
  {
    type: 'data_analytics',
    label: 'Analytics',
    description: 'Allow anonymous usage analytics to improve the service',
    required: false,
  },
  {
    type: 'email_notifications',
    label: 'Email Notifications',
    description: 'Receive email alerts when copyright matches are detected',
    required: false,
  },
]

const COOKIE_CATEGORIES = [
  {
    category: 'essential',
    label: 'Essential Cookies',
    description: 'Required for basic site functionality and security',
    required: true,
  },
  {
    category: 'functional',
    label: 'Functional Cookies',
    description: 'Remember your preferences and settings',
    required: false,
  },
  {
    category: 'analytics',
    label: 'Analytics Cookies',
    description: 'Help us understand how you use the site',
    required: false,
  },
  {
    category: 'marketing',
    label: 'Marketing Cookies',
    description: 'Used to show you relevant content',
    required: false,
  },
]

export default function Privacy() {
  const [consentStatus, setConsentStatus] = useState<ConsentStatus>({})
  const [cookiePreferences, setCookiePreferences] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  useEffect(() => {
    loadPrivacyData()
  }, [])

  const loadPrivacyData = async () => {
    try {
      const [consentRes, cookieRes] = await Promise.all([
        api.getConsentStatus(),
        api.getCookiePreferences(),
      ])

      setConsentStatus(consentRes.data.consents || {})
      setCookiePreferences(cookieRes.data.preferences || {})
      setLoading(false)
    } catch (error) {
      toast.error('Failed to load privacy settings')
      setLoading(false)
    }
  }

  const handleConsentToggle = async (consentType: string, granted: boolean) => {
    try {
      if (granted) {
        await api.grantConsent(consentType)
      } else {
        await api.withdrawConsent(consentType)
      }
      toast.success('Consent updated successfully')
      loadPrivacyData()
    } catch (error) {
      toast.error('Failed to update consent')
    }
  }

  const handleCookieToggle = async (category: string, enabled: boolean) => {
    try {
      const newPreferences = { ...cookiePreferences, [category]: enabled }
      await api.setCookiePreferences(newPreferences)
      setCookiePreferences(newPreferences)
      toast.success('Cookie preferences updated')
    } catch (error) {
      toast.error('Failed to update cookie preferences')
    }
  }

  const downloadMyData = async () => {
    try {
      const response = await api.getMyData()
      const dataStr = JSON.stringify(response.data, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = `artlockr-data-${new Date().toISOString()}.json`
      link.click()
      toast.success('Data exported successfully')
    } catch (error) {
      toast.error('Failed to export data')
    }
  }

  const deleteAllData = async () => {
    try {
      await api.deleteAllData()
      toast.success('All data deleted successfully')
      setShowDeleteConfirm(false)
    } catch (error) {
      toast.error('Failed to delete data')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading privacy settings...</div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Privacy & Data Control</h1>
        <p className="mt-2 text-gray-600">
          Manage your consent, cookie preferences, and exercise your data rights
        </p>
      </div>

      {/* Privacy Commitment */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-start">
          <Shield className="h-6 w-6 text-green-600 mr-3 flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-bold text-green-900 mb-2">Our Privacy Commitment</h3>
            <ul className="text-sm text-green-800 space-y-1">
              <li>✓ Features-only storage - no images stored by default</li>
              <li>✓ Immediate image deletion after feature extraction</li>
              <li>✓ Cryptographic ownership proofs (SHA-256)</li>
              <li>✓ Full GDPR, CCPA, and COPPA compliance</li>
              <li>✓ Complete data transparency and control</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Consent Management */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Consent Management</h2>
        <div className="space-y-4">
          {CONSENT_TYPES.map((consent) => {
            const status = consentStatus[consent.type]
            const isGranted = status?.granted || false

            return (
              <div
                key={consent.type}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
              >
                <div className="flex-1">
                  <div className="flex items-center">
                    <p className="font-medium text-gray-900">{consent.label}</p>
                    {consent.required && (
                      <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                        Required
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{consent.description}</p>
                  {status && (
                    <p className="text-xs text-gray-500 mt-2">
                      {isGranted ? 'Granted' : 'Withdrawn'} on{' '}
                      {new Date(status.timestamp).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <label className="relative inline-flex items-center cursor-pointer ml-4">
                  <input
                    type="checkbox"
                    checked={isGranted}
                    onChange={(e) => handleConsentToggle(consent.type, e.target.checked)}
                    disabled={consent.required}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>
            )
          })}
        </div>
      </div>

      {/* Cookie Preferences */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Cookie Preferences</h2>
        <div className="space-y-4">
          {COOKIE_CATEGORIES.map((cookie) => {
            const isEnabled = cookiePreferences[cookie.category] !== false

            return (
              <div
                key={cookie.category}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
              >
                <div className="flex-1">
                  <div className="flex items-center">
                    <p className="font-medium text-gray-900">{cookie.label}</p>
                    {cookie.required && (
                      <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                        Required
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{cookie.description}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer ml-4">
                  <input
                    type="checkbox"
                    checked={isEnabled}
                    onChange={(e) => handleCookieToggle(cookie.category, e.target.checked)}
                    disabled={cookie.required}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>
            )
          })}
        </div>
      </div>

      {/* Data Rights */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Your Data Rights</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={downloadMyData}
            className="flex items-center justify-center p-4 border-2 border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors"
          >
            <Download className="h-5 w-5 text-primary-600 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Download My Data</p>
              <p className="text-sm text-gray-600">Export all your data (GDPR)</p>
            </div>
          </button>

          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="flex items-center justify-center p-4 border-2 border-red-300 rounded-lg hover:border-red-500 hover:bg-red-50 transition-colors"
          >
            <Trash2 className="h-5 w-5 text-red-600 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Delete All Data</p>
              <p className="text-sm text-gray-600">Permanently remove your data</p>
            </div>
          </button>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <div className="flex items-center mb-4">
              <AlertCircle className="h-6 w-6 text-red-600 mr-3" />
              <h3 className="text-xl font-bold text-gray-900">Confirm Data Deletion</h3>
            </div>
            <p className="text-gray-600 mb-6">
              This will permanently delete all your data, including artwork features, detection
              results, and account information. This action cannot be undone.
            </p>
            <div className="flex space-x-4">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
              <button onClick={deleteAllData} className="btn-primary flex-1 bg-red-600 hover:bg-red-700">
                Delete Everything
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import { useState, useEffect } from 'react'
import { Cookie, X, Settings } from 'lucide-react'
import { api } from '../services/api'

export default function CookieConsent() {
  const [show, setShow] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [preferences, setPreferences] = useState({
    essential: true,
    functional: false,
    analytics: false,
    marketing: false,
  })

  useEffect(() => {
    // Check if user has already set cookie preferences
    const hasConsent = localStorage.getItem('cookie-consent')
    if (!hasConsent) {
      setShow(true)
    }
  }, [])

  const acceptAll = async () => {
    const allAccepted = {
      essential: true,
      functional: true,
      analytics: true,
      marketing: true,
    }
    await savePreferences(allAccepted)
  }

  const acceptEssential = async () => {
    const essentialOnly = {
      essential: true,
      functional: false,
      analytics: false,
      marketing: false,
    }
    await savePreferences(essentialOnly)
  }

  const saveCustomPreferences = async () => {
    await savePreferences(preferences)
    setShowSettings(false)
  }

  const savePreferences = async (prefs: typeof preferences) => {
    try {
      await api.setCookiePreferences(prefs)
      localStorage.setItem('cookie-consent', 'true')
      setShow(false)
    } catch (error) {
      console.error('Failed to save cookie preferences:', error)
    }
  }

  if (!show) return null

  return (
    <div className="fixed bottom-0 inset-x-0 z-50 pb-4 px-4">
      <div className="max-w-4xl mx-auto">
        {!showSettings ? (
          // Main cookie banner
          <div className="bg-white rounded-xl shadow-2xl border border-gray-200 p-6">
            <div className="flex items-start">
              <Cookie className="h-6 w-6 text-primary-600 mr-3 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h3 className="text-lg font-bold text-gray-900 mb-2">Cookie Preferences</h3>
                <p className="text-sm text-gray-600 mb-4">
                  We use cookies to enhance your experience, analyze site usage, and assist in our
                  marketing efforts. You can customize your cookie preferences or accept all cookies.
                </p>
                <div className="flex flex-wrap gap-3">
                  <button onClick={acceptAll} className="btn-primary">
                    Accept All
                  </button>
                  <button onClick={acceptEssential} className="btn-secondary">
                    Essential Only
                  </button>
                  <button
                    onClick={() => setShowSettings(true)}
                    className="flex items-center btn-secondary"
                  >
                    <Settings className="h-4 w-4 mr-2" />
                    Customize
                  </button>
                </div>
              </div>
              <button
                onClick={() => setShow(false)}
                className="text-gray-400 hover:text-gray-600 ml-4"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
        ) : (
          // Cookie settings panel
          <div className="bg-white rounded-xl shadow-2xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-gray-900">Customize Cookie Preferences</h3>
              <button
                onClick={() => setShowSettings(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4 mb-6">
              {/* Essential Cookies */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center">
                    <p className="font-medium text-gray-900">Essential Cookies</p>
                    <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                      Required
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    Required for basic site functionality and security
                  </p>
                </div>
                <div className="ml-4">
                  <input
                    type="checkbox"
                    checked={true}
                    disabled
                    className="h-5 w-5 text-primary-600 rounded"
                  />
                </div>
              </div>

              {/* Functional Cookies */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">Functional Cookies</p>
                  <p className="text-sm text-gray-600 mt-1">
                    Remember your preferences and settings
                  </p>
                </div>
                <div className="ml-4">
                  <input
                    type="checkbox"
                    checked={preferences.functional}
                    onChange={(e) =>
                      setPreferences({ ...preferences, functional: e.target.checked })
                    }
                    className="h-5 w-5 text-primary-600 rounded"
                  />
                </div>
              </div>

              {/* Analytics Cookies */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">Analytics Cookies</p>
                  <p className="text-sm text-gray-600 mt-1">
                    Help us understand how you use the site
                  </p>
                </div>
                <div className="ml-4">
                  <input
                    type="checkbox"
                    checked={preferences.analytics}
                    onChange={(e) =>
                      setPreferences({ ...preferences, analytics: e.target.checked })
                    }
                    className="h-5 w-5 text-primary-600 rounded"
                  />
                </div>
              </div>

              {/* Marketing Cookies */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">Marketing Cookies</p>
                  <p className="text-sm text-gray-600 mt-1">Used to show you relevant content</p>
                </div>
                <div className="ml-4">
                  <input
                    type="checkbox"
                    checked={preferences.marketing}
                    onChange={(e) =>
                      setPreferences({ ...preferences, marketing: e.target.checked })
                    }
                    className="h-5 w-5 text-primary-600 rounded"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button onClick={saveCustomPreferences} className="btn-primary flex-1">
                Save Preferences
              </button>
              <button onClick={() => setShowSettings(false)} className="btn-secondary flex-1">
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

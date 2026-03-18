import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Upload, CreditCard, TrendingUp, CheckCircle, ExternalLink, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { getArtistProfile, getCompanyProfile, startStripeOnboarding, getStripeStatus } from '../services/api'
import { useAuthStore } from '../store/authStore'

export default function Dashboard() {
  const { user, setUser } = useAuthStore()
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [onboarding, setOnboarding] = useState(false)

  useEffect(() => {
    if (!user) return
    const fetch = user.role === 'artist' ? getArtistProfile : getCompanyProfile
    fetch(user.id)
      .then(({ data }) => setProfile(data))
      .catch(() => null)
      .finally(() => setLoading(false))
  }, [user])

  const handleStripeOnboard = async () => {
    if (!user) return
    setOnboarding(true)
    try {
      const { data } = await startStripeOnboarding(user.id)
      window.location.href = data.onboarding_url
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Stripe error'
      toast.error(msg)
      setOnboarding(false)
    }
  }

  const checkStripeStatus = async () => {
    if (!user) return
    try {
      const { data } = await getStripeStatus(user.id)
      if (data.onboarded) {
        setUser({ ...user, stripe_onboarded: true })
        toast.success('Stripe account verified!')
      } else {
        toast('Onboarding not yet complete', { icon: 'ℹ️' })
      }
    } catch {
      toast.error('Could not check Stripe status')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-violet-500" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {user?.username}
          </h1>
          <p className="text-sm text-gray-500 mt-0.5 capitalize">{user?.role} account</p>
        </div>
        {user?.role === 'artist' && (
          <Link
            to="/upload"
            className="flex items-center gap-2 px-4 py-2 bg-violet-600 text-white text-sm font-medium rounded-lg hover:bg-violet-700 transition-colors"
          >
            <Upload className="h-4 w-4" />
            Upload work
          </Link>
        )}
        {user?.role === 'company' && (
          <Link
            to="/marketplace"
            className="flex items-center gap-2 px-4 py-2 bg-violet-600 text-white text-sm font-medium rounded-lg hover:bg-violet-700 transition-colors"
          >
            Browse marketplace
          </Link>
        )}
      </div>

      {/* Artist dashboard */}
      {user?.role === 'artist' && profile && (
        <>
          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {[
              { label: 'Active listings', value: profile.listing_count as number },
              { label: 'Total sales', value: profile.total_sales as number },
              {
                label: 'Earnings',
                value: `$${((profile.total_earnings as number) ?? 0).toFixed(2)}`,
              },
            ].map((s) => (
              <div key={s.label} className="bg-white rounded-xl border p-4">
                <p className="text-2xl font-bold text-violet-700">{s.value}</p>
                <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>

          {/* Stripe Connect */}
          <div className="bg-white rounded-xl border p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-semibold text-gray-900">Payment setup</h2>
                <p className="text-sm text-gray-500 mt-0.5">
                  Connect Stripe to receive payouts when your work is purchased.
                </p>
              </div>
              {user.stripe_onboarded ? (
                <span className="flex items-center gap-1.5 text-sm text-green-600 font-medium">
                  <CheckCircle className="h-4 w-4" />
                  Connected
                </span>
              ) : (
                <div className="flex gap-2">
                  <button
                    onClick={checkStripeStatus}
                    className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Check status
                  </button>
                  <button
                    onClick={handleStripeOnboard}
                    disabled={onboarding}
                    className="flex items-center gap-1.5 px-4 py-2 bg-violet-600 text-white text-sm font-medium rounded-lg hover:bg-violet-700 disabled:opacity-60 transition-colors"
                  >
                    {onboarding ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <ExternalLink className="h-4 w-4" />
                    )}
                    Set up Stripe
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Recent listings */}
          {Array.isArray(profile.listings) && (profile.listings as unknown[]).length > 0 && (
            <div className="bg-white rounded-xl border p-6">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Your listings</h2>
              <div className="space-y-3">
                {(profile.listings as Record<string, unknown>[]).map((l) => (
                  <Link
                    key={l.id as number}
                    to={`/marketplace/${l.id}`}
                    className="flex items-center justify-between hover:bg-gray-50 rounded-lg p-2 -mx-2 transition-colors"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-900">{l.title as string}</p>
                      <p className="text-xs text-gray-500 capitalize">
                        {(l.license_type as string).replace('_', ' ')} · {l.work_type as string}
                      </p>
                    </div>
                    <span className="text-sm font-bold text-violet-700">
                      ${(l.price as number).toFixed(2)}
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Company dashboard */}
      {user?.role === 'company' && profile && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {[
              { label: 'Purchases', value: profile.total_purchases as number, icon: CreditCard },
              {
                label: 'Total spent',
                value: `$${((profile.total_spent as number) ?? 0).toFixed(2)}`,
                icon: TrendingUp,
              },
            ].map((s) => (
              <div key={s.label} className="bg-white rounded-xl border p-4">
                <p className="text-2xl font-bold text-violet-700">{s.value}</p>
                <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>

          {Array.isArray(profile.recent_purchases) &&
            (profile.recent_purchases as unknown[]).length > 0 && (
              <div className="bg-white rounded-xl border p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-base font-semibold text-gray-900">Recent purchases</h2>
                  <Link
                    to="/purchases"
                    className="text-sm text-violet-600 hover:underline"
                  >
                    View all
                  </Link>
                </div>
                <div className="space-y-3">
                  {(profile.recent_purchases as Record<string, unknown>[]).map((p) => (
                    <div key={p.id as number} className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {p.listing_title as string}
                        </p>
                        <p className="text-xs text-gray-500 capitalize">
                          {(p.license_type as string).replace('_', ' ')} ·{' '}
                          {new Date(p.purchased_at as string).toLocaleDateString()}
                        </p>
                      </div>
                      <span className="text-sm font-bold text-violet-700">
                        ${(p.amount as number).toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
        </>
      )}
    </div>
  )
}

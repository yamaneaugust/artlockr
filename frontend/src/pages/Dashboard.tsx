import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Search, Upload, Store, Plus, TrendingUp, Loader2 } from 'lucide-react'
import { getArtistProfile, getCompanyProfile } from '../services/api'
import { useAuthStore } from '../store/authStore'

export default function Dashboard() {
  const { user } = useAuthStore()
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)

  const loadLocalData = () => {
    try {
      const listings = JSON.parse(localStorage.getItem('artlock-listings') || '[]')
      const purchases = JSON.parse(localStorage.getItem('artlock-purchases') || '[]')
      return { listings, purchases }
    } catch {
      return { listings: [], purchases: [] }
    }
  }

  useEffect(() => {
    if (!user) return
    const { listings, purchases } = loadLocalData()

    // Filter local data by current user
    const userListings = listings.filter(
      (l: { artist?: { username?: string } }) =>
        l.artist?.username === user.username,
    )
    const userPurchases = purchases.filter(
      (p: { buyer_id?: number }) => p.buyer_id === user.id,
    )

    const fetch = user.role === 'artist' ? getArtistProfile : getCompanyProfile
    fetch(user.id)
      .then(({ data }) => {
        // Merge local data with backend profile
        if (user.role === 'artist') {
          setProfile({
            ...data,
            listing_count: (data.listing_count || 0) + userListings.length,
            total_sales: (data.total_sales || 0) + userListings.reduce(
              (sum: number, l: { sales_count?: number }) => sum + (l.sales_count || 0),
              0,
            ),
            total_earnings: (data.total_earnings || 0) + userListings.reduce(
              (sum: number, l: { sales_count?: number; price?: number }) =>
                sum + ((l.sales_count || 0) * (l.price || 0)),
              0,
            ),
            listings: [...userListings, ...(data.listings || [])],
          })
        } else {
          setProfile({
            ...data,
            total_purchases: (data.total_purchases || 0) + userPurchases.length,
            total_spent: (data.total_spent || 0) + userPurchases.reduce(
              (sum: number, p: { price_paid?: number }) => sum + (p.price_paid || 0),
              0,
            ),
            recent_purchases: [
              ...userPurchases.map((p: Record<string, unknown>) => ({
                id: p.id,
                listing_title: p.listing_title,
                purchased_at: p.purchased_at,
                license_type: p.license_type,
                amount: p.price_paid,
                license_key: p.license_key,
              })),
              ...(data.recent_purchases || []),
            ],
          })
        }
      })
      .catch(() => {
        // Backend unavailable - use only local data
        if (user.role === 'artist') {
          setProfile({
            listing_count: userListings.length,
            total_sales: userListings.reduce(
              (sum: number, l: { sales_count?: number }) => sum + (l.sales_count || 0),
              0,
            ),
            total_earnings: userListings.reduce(
              (sum: number, l: { sales_count?: number; price?: number }) =>
                sum + ((l.sales_count || 0) * (l.price || 0)),
              0,
            ),
            listings: userListings,
          })
        } else {
          setProfile({
            company_name: user.company_name,
            total_purchases: userPurchases.length,
            total_spent: userPurchases.reduce(
              (sum: number, p: { price_paid?: number }) => sum + (p.price_paid || 0),
              0,
            ),
            recent_purchases: userPurchases.map((p: Record<string, unknown>) => ({
              id: p.id,
              listing_title: p.listing_title,
              purchased_at: p.purchased_at,
              license_type: p.license_type,
              amount: p.price_paid,
              license_key: p.license_key,
            })),
          })
        }
      })
      .finally(() => setLoading(false))
  }, [user])

  if (loading) {
    return (
      <div className="min-h-screen bg-artlock-dark flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-orange-500" />
      </div>
    )
  }

  // Artist Dashboard
  if (user?.role === 'artist') {
    return (
      <div className="min-h-screen bg-artlock-dark text-white p-6">
        <div className="max-w-7xl mx-auto">
          {/* Greeting */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold">Hello, {user.username}</h1>
            <p className="text-blue-300 mt-1">Welcome to your creator dashboard</p>
          </div>

          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-blue-900 rounded-xl border border-blue-900/30 p-6">
              <p className="text-blue-400 text-sm mb-1">Active Listings</p>
              <p className="text-3xl font-bold text-white">{(profile?.listing_count as number) || 0}</p>
            </div>
            <div className="bg-blue-900 rounded-xl border border-blue-900/30 p-6">
              <p className="text-blue-400 text-sm mb-1">Total Sales</p>
              <p className="text-3xl font-bold text-white">{(profile?.total_sales as number) || 0}</p>
            </div>
            <div className="bg-blue-900 rounded-xl border border-blue-900/30 p-6">
              <p className="text-blue-400 text-sm mb-1">Earnings</p>
              <p className="text-3xl font-bold text-orange-500">
                ${((profile?.total_earnings as number) || 0).toFixed(2)}
              </p>
            </div>
          </div>

          {/* Main Actions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Detect Copyright */}
            <Link
              to="/detect"
              className="group bg-gradient-to-br from-blue-900 to-blue-800 rounded-2xl border border-blue-900/30 hover:border-blue-900/30 p-8 transition-all hover:scale-105"
            >
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 rounded-full bg-orange-500/20 flex items-center justify-center mb-4 group-hover:bg-orange-500/30 transition-colors">
                  <Search className="w-8 h-8 text-orange-500" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">Detect Copyright</h3>
                <p className="text-blue-300 text-sm">
                  Check if your artwork has been used without permission
                </p>
              </div>
            </Link>

            {/* License & Price */}
            <Link
              to="/upload"
              className="group bg-gradient-to-br from-blue-900 to-blue-800 rounded-2xl border border-blue-900/30 hover:border-blue-900/30 p-8 transition-all hover:scale-105"
            >
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 rounded-full bg-orange-500/20 flex items-center justify-center mb-4 group-hover:bg-orange-500/30 transition-colors">
                  <Upload className="w-8 h-8 text-orange-500" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">License & Price</h3>
                <p className="text-blue-300 text-sm">
                  Upload your work and set your pricing - we handle the licensing
                </p>
              </div>
            </Link>

            {/* Marketplace */}
            <Link
              to="/marketplace"
              className="group bg-gradient-to-br from-blue-900 to-blue-800 rounded-2xl border border-blue-900/30 hover:border-blue-900/30 p-8 transition-all hover:scale-105"
            >
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 rounded-full bg-orange-500/20 flex items-center justify-center mb-4 group-hover:bg-orange-500/30 transition-colors">
                  <Store className="w-8 h-8 text-orange-500" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">Marketplace</h3>
                <p className="text-blue-300 text-sm">
                  View recommended AI companies and create offers
                </p>
              </div>
            </Link>
          </div>

          {/* Recent Activity */}
          {Array.isArray(profile?.listings) && (profile.listings as unknown[]).length > 0 && (
            <div className="mt-8 bg-blue-900 rounded-xl border border-blue-900/30 p-6">
              <h2 className="text-xl font-bold text-white mb-4">Your Recent Listings</h2>
              <div className="space-y-3">
                {(profile.listings as Record<string, unknown>[]).slice(0, 5).map((listing) => (
                  <Link
                    key={listing.id as number}
                    to={`/marketplace/${listing.id}`}
                    className="flex items-center justify-between p-4 bg-blue-950 rounded-lg hover:bg-blue-800 transition-colors"
                  >
                    <div>
                      <p className="text-white font-medium">{listing.title as string}</p>
                      <p className="text-blue-400 text-sm capitalize">
                        {(listing.license_type as string).replace('_', ' ')} · {listing.work_type as string}
                      </p>
                    </div>
                    <span className="text-orange-500 font-bold">
                      ${(listing.price as number).toFixed(2)}
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Company Dashboard
  if (user?.role === 'company') {
    const companyName = (profile?.company_name as string) || user.username

    return (
      <div className="min-h-screen bg-artlock-dark text-white p-6">
        <div className="max-w-7xl mx-auto">
          {/* Greeting */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold">Hello, {companyName}</h1>
            <p className="text-blue-300 mt-1">Welcome to your company dashboard</p>
          </div>

          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="bg-blue-900 rounded-xl border border-blue-900/30 p-6">
              <p className="text-blue-400 text-sm mb-1">Total Purchases</p>
              <p className="text-3xl font-bold text-white">{(profile?.total_purchases as number) || 0}</p>
            </div>
            <div className="bg-blue-900 rounded-xl border border-blue-900/30 p-6">
              <p className="text-blue-400 text-sm mb-1">Total Spent</p>
              <p className="text-3xl font-bold text-orange-500">
                ${((profile?.total_spent as number) || 0).toFixed(2)}
              </p>
            </div>
          </div>

          {/* Main Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Create Request */}
            <Link
              to="/requests/create"
              className="group bg-gradient-to-br from-blue-900 to-blue-800 rounded-2xl border border-blue-900/30 hover:border-blue-900/30 p-8 transition-all hover:scale-105"
            >
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 rounded-full bg-orange-500/20 flex items-center justify-center mb-4 group-hover:bg-orange-500/30 transition-colors">
                  <Plus className="w-8 h-8 text-orange-500" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">Create Request</h3>
                <p className="text-blue-300 text-sm">
                  Specify the type of data and budget you're looking for
                </p>
              </div>
            </Link>

            {/* Browse Recommended Deals */}
            <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-2xl border border-blue-900/30 p-8">
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 rounded-full bg-orange-500/20 flex items-center justify-center mb-4">
                  <TrendingUp className="w-8 h-8 text-orange-500" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">Recommended Deals</h3>
                <p className="text-blue-300 text-sm">
                  Browse curated datasets matched to your needs
                </p>
              </div>
            </div>
          </div>

          {/* Recent Purchases */}
          {Array.isArray(profile?.recent_purchases) && (profile.recent_purchases as unknown[]).length > 0 && (
            <div className="mt-8 bg-blue-900 rounded-xl border border-blue-900/30 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-white">Recent Purchases</h2>
                <Link to="/purchases" className="text-orange-400 hover:text-orange-300 text-sm">
                  View all →
                </Link>
              </div>
              <div className="space-y-3">
                {(profile.recent_purchases as Record<string, unknown>[]).slice(0, 5).map((purchase) => (
                  <div
                    key={purchase.id as number}
                    className="p-4 bg-blue-950 rounded-lg"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-white font-medium">{purchase.listing_title as string}</p>
                        <p className="text-blue-400 text-sm">
                          {new Date(purchase.purchased_at as string).toLocaleDateString()} ·{' '}
                          {((purchase.license_type as string) || 'non_exclusive').replace('_', ' ')}
                        </p>
                      </div>
                      <span className="text-orange-500 font-bold">
                        ${((purchase.amount as number) || 0).toFixed(2)}
                      </span>
                    </div>
                    {Boolean(purchase.license_key) && (
                      <div className="mt-2 pt-2 border-t border-blue-900/30 flex items-center gap-2">
                        <span className="text-xs text-blue-400">License Key:</span>
                        <code className="text-xs text-orange-400 font-mono flex-1">
                          {purchase.license_key as string}
                        </code>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(purchase.license_key as string)
                          }}
                          className="text-xs text-blue-300 hover:text-white"
                        >
                          Copy
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-artlock-dark flex items-center justify-center text-white">
      <p>Unable to load dashboard</p>
    </div>
  )
}

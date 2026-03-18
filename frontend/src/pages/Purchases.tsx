import { useState, useEffect } from 'react'
import { Key, ExternalLink, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { getMyPurchases } from '../services/api'
import { useAuthStore } from '../store/authStore'

interface Purchase {
  id: number
  listing_title: string
  amount: number
  license_key: string
  license_type: string
  status: string
  purchased_at: string
  download_expires_at: string | null
}

export default function Purchases() {
  const { user } = useAuthStore()
  const [purchases, setPurchases] = useState<Purchase[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) return
    getMyPurchases(user.id)
      .then(({ data }) => setPurchases(data))
      .catch(() => toast.error('Failed to load purchases'))
      .finally(() => setLoading(false))
  }, [user])

  const copyKey = (key: string) => {
    navigator.clipboard.writeText(key)
    toast.success('License key copied!')
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white rounded-xl border h-24 animate-pulse" />
        ))}
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">My Licenses</h1>

      {purchases.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <Key className="h-12 w-12 mx-auto mb-3 opacity-40" />
          <p className="text-lg font-medium">No purchases yet</p>
          <p className="text-sm">Browse the marketplace to find creative works to license.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {purchases.map((p) => (
            <div key={p.id} className="bg-white rounded-xl border p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
                    <p className="font-semibold text-gray-900 truncate">{p.listing_title}</p>
                  </div>
                  <div className="flex flex-wrap gap-3 mt-2 text-sm text-gray-500">
                    <span>${p.amount.toFixed(2)}</span>
                    <span className="capitalize">{p.license_type.replace('_', ' ')}</span>
                    <span>{new Date(p.purchased_at).toLocaleDateString()}</span>
                    {p.download_expires_at && (
                      <span className="text-orange-500">
                        Expires {new Date(p.download_expires_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-3 flex items-center gap-2">
                <div className="flex-1 flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2 font-mono text-sm text-gray-700 min-w-0">
                  <Key className="h-3.5 w-3.5 text-gray-400 flex-shrink-0" />
                  <span className="truncate">{p.license_key}</span>
                </div>
                <button
                  onClick={() => copyKey(p.license_key)}
                  className="px-3 py-2 text-sm font-medium text-violet-600 border border-violet-200 rounded-lg hover:bg-violet-50 transition-colors whitespace-nowrap"
                >
                  Copy key
                </button>
                <a
                  href={`/marketplace`}
                  className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                  title="View listing"
                >
                  <ExternalLink className="h-4 w-4" />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Music, Image, Video, FileText, Package, CheckCircle, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'
import { getListing, purchaseListing } from '../services/api'
import { useAuthStore } from '../store/authStore'

const WORK_TYPE_ICONS: Record<string, React.ElementType> = {
  image: Image, audio: Music, video: Video, text: FileText, dataset: Package,
}

export default function ListingDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const [listing, setListing] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [buying, setBuying] = useState(false)

  useEffect(() => {
    getListing(Number(id))
      .then(({ data }) => setListing(data))
      .catch(() => toast.error('Listing not found'))
      .finally(() => setLoading(false))
  }, [id])

  const handlePurchase = async () => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    if (user?.role !== 'company') {
      toast.error('Only company accounts can purchase licenses')
      return
    }
    setBuying(true)
    try {
      const { data } = await purchaseListing(Number(id), user.id)
      // Redirect to Stripe checkout
      window.location.href = data.checkout_url
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Purchase failed'
      toast.error(msg)
    } finally {
      setBuying(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto animate-pulse space-y-4">
        <div className="h-64 bg-gray-200 rounded-xl" />
        <div className="h-8 bg-gray-200 rounded w-2/3" />
        <div className="h-4 bg-gray-200 rounded w-1/2" />
      </div>
    )
  }

  if (!listing) return null

  const work = listing.work as Record<string, unknown>
  const artist = listing.artist as Record<string, unknown>
  const Icon = WORK_TYPE_ICONS[(work.work_type as string)] ?? Package

  return (
    <div className="max-w-4xl mx-auto">
      <div className="grid md:grid-cols-2 gap-8">
        {/* Preview */}
        <div className="bg-gradient-to-br from-violet-50 to-indigo-100 rounded-2xl flex items-center justify-center min-h-64">
          {work.preview_url ? (
            <img
              src={work.preview_url as string}
              alt={listing.title as string}
              className="rounded-2xl max-h-80 object-contain"
            />
          ) : (
            <Icon className="h-24 w-24 text-violet-300" />
          )}
        </div>

        {/* Info */}
        <div className="space-y-4">
          <div>
            <span className="text-xs font-medium text-violet-600 uppercase tracking-wide">
              {(work.work_type as string)} · {(work.file_format as string)}
            </span>
            <h1 className="text-2xl font-bold text-gray-900 mt-1">{listing.title as string}</h1>
            <p className="text-gray-500 mt-1 text-sm">{listing.description as string}</p>
          </div>

          <div className="flex flex-wrap gap-2">
            {((work.tags as string[]) || []).map((tag) => (
              <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                {tag}
              </span>
            ))}
          </div>

          {/* Artist */}
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <div className="h-10 w-10 rounded-full bg-violet-200 flex items-center justify-center font-bold text-violet-700 text-sm">
              {(artist.display_name as string)?.[0]?.toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">
                {artist.display_name as string}
                {(artist.verified as boolean) && <CheckCircle className="inline h-3.5 w-3.5 ml-1 text-violet-500" />}
              </p>
              <p className="text-xs text-gray-500">{artist.total_sales as number} sales</p>
            </div>
          </div>

          {/* Pricing */}
          <div className="border rounded-xl p-4 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">License type</span>
              <span className="text-sm font-semibold text-gray-900 capitalize">
                {(listing.license_type as string).replace('_', ' ')}
              </span>
            </div>
            {(listing.max_buyers as number | null) && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Copies available</span>
                <span className="text-sm font-semibold">
                  {(listing.max_buyers as number) - (listing.sales_count as number)} / {listing.max_buyers as number}
                </span>
              </div>
            )}
            {(listing.license_details as string | null) && (
              <p className="text-xs text-gray-500">{listing.license_details as string}</p>
            )}
            <div className="border-t pt-3 flex items-center justify-between">
              <span className="text-2xl font-bold text-violet-700">
                ${(listing.price as number).toFixed(2)}
              </span>
              <button
                onClick={handlePurchase}
                disabled={buying || listing.status !== 'active'}
                className="px-6 py-2.5 bg-violet-600 hover:bg-violet-700 disabled:opacity-60 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
              >
                {buying ? 'Redirecting…' : listing.status !== 'active' ? 'Sold out' : 'Buy license'}
                {!buying && listing.status === 'active' && <ExternalLink className="h-3.5 w-3.5" />}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

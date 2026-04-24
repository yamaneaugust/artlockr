import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Music, Image, Video, FileText, Package, CheckCircle, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'
import { getListing, purchaseListing } from '../services/api'
import { syncFetchListing, syncPushPurchase } from '../services/sync'
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

  const loadLocalListing = (listingId: number): Record<string, unknown> | null => {
    try {
      const listings = JSON.parse(localStorage.getItem('artlock-listings') || '[]')
      return listings.find((l: { id: number }) => l.id === listingId) || null
    } catch {
      return null
    }
  }

  useEffect(() => {
    const listingId = Number(id)
    const fetchListing = async () => {
      // Try local first (fastest)
      const local = loadLocalListing(listingId)
      if (local) {
        setListing(local)
        setLoading(false)
        return
      }

      // Try sync backend (shared listings from other users)
      const synced = await syncFetchListing(listingId)
      if (synced && synced.work) {
        setListing(synced)
        setLoading(false)
        return
      }

      // Fall back to legacy backend
      try {
        const { data } = await getListing(listingId)
        if (data && data.work) {
          setListing(data)
        } else {
          toast.error('Listing not found')
        }
      } catch {
        toast.error('Listing not found')
      } finally {
        setLoading(false)
      }
    }
    fetchListing()
  }, [id])

  const generateLicenseKey = (): string => {
    const segments = Array.from({ length: 4 }, () =>
      Math.random().toString(36).substring(2, 8).toUpperCase()
    )
    return `ARTLOCK-${segments.join('-')}`
  }

  const savePurchaseLocally = () => {
    const purchases = JSON.parse(localStorage.getItem('artlock-purchases') || '[]')
    const licenseKey = generateLicenseKey()
    const purchaseData = {
      id: Date.now(),
      listing_id: Number(id),
      buyer_id: user?.id,
      buyer_username: user?.username,
      license_key: licenseKey,
      price_paid: (listing?.price as number) ?? 0,
      license_type: listing?.license_type as string | undefined,
      listing_title: listing?.title as string | undefined,
      work_preview_url: ((listing?.work as Record<string, unknown>)?.preview_url) as string | undefined,
      artist_username: ((listing?.artist as Record<string, unknown>)?.display_name) as string | undefined,
      purchased_at: new Date().toISOString(),
    }
    purchases.push(purchaseData)
    localStorage.setItem('artlock-purchases', JSON.stringify(purchases))

    // Increment sales count on the listing
    const listings = JSON.parse(localStorage.getItem('artlock-listings') || '[]')
    const idx = listings.findIndex((l: { id: number }) => l.id === Number(id))
    if (idx >= 0) {
      listings[idx].sales_count = (listings[idx].sales_count || 0) + 1
      localStorage.setItem('artlock-listings', JSON.stringify(listings))
    }

    // Push purchase to shared backend (so artist sees the sale)
    syncPushPurchase(purchaseData as unknown as Record<string, unknown>)

    return licenseKey
  }

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
      // Try backend first (real Stripe checkout)
      try {
        const { data } = await purchaseListing(Number(id), user.id)
        window.location.href = data.checkout_url
        return
      } catch {
        // Backend unavailable - simulate purchase locally
        console.log('Backend unavailable, processing demo purchase')
      }

      // Demo purchase flow - simulate processing time
      await new Promise((resolve) => setTimeout(resolve, 1000))
      const licenseKey = savePurchaseLocally()
      toast.success(`License purchased! Key: ${licenseKey}`, { duration: 8000 })

      // Redirect to dashboard to see purchase
      setTimeout(() => navigate('/dashboard'), 2000)
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
      <div className="min-h-screen bg-artlock-dark p-6">
        <div className="max-w-4xl mx-auto animate-pulse space-y-4">
          <div className="h-64 bg-blue-900 rounded-xl" />
          <div className="h-8 bg-blue-900 rounded w-2/3" />
          <div className="h-4 bg-blue-900 rounded w-1/2" />
        </div>
      </div>
    )
  }

  if (!listing) {
    return (
      <div className="min-h-screen bg-artlock-dark flex items-center justify-center text-white">
        <div className="text-center">
          <Package className="h-12 w-12 mx-auto text-blue-400 mb-3" />
          <p className="text-lg font-medium">Listing not found</p>
          <button
            onClick={() => navigate('/marketplace')}
            className="mt-4 px-6 py-2 bg-orange-500 hover:bg-orange-600 text-white font-medium rounded-lg transition-colors"
          >
            Back to Marketplace
          </button>
        </div>
      </div>
    )
  }

  const work = (listing.work as Record<string, unknown>) || {}
  const artist = (listing.artist as Record<string, unknown>) || {}
  const workType = (work.work_type as string) || 'image'
  const Icon = WORK_TYPE_ICONS[workType] ?? Package
  const price = (listing.price as number) ?? 0
  const licenseType = (listing.license_type as string) || 'non_exclusive'
  const status = (listing.status as string) || 'active'

  return (
    <div className="min-h-screen bg-artlock-dark p-6">
      <div className="max-w-4xl mx-auto">
        <div className="grid md:grid-cols-2 gap-8">
          {/* Preview */}
          <div className="bg-gradient-to-br from-blue-900 to-blue-950 rounded-2xl flex items-center justify-center min-h-64 overflow-hidden">
            {work.preview_url ? (
              <img
                src={work.preview_url as string}
                alt={(listing.title as string) || 'Listing'}
                className="rounded-2xl max-h-80 object-contain"
              />
            ) : (
              <Icon className="h-24 w-24 text-blue-400" />
            )}
          </div>

          {/* Info */}
          <div className="space-y-4">
            <div>
              <span className="text-xs font-medium text-orange-400 uppercase tracking-wide">
                {workType}{work.file_format ? ` · ${work.file_format}` : ''}
              </span>
              <h1 className="text-2xl font-bold text-white mt-1">{(listing.title as string) || 'Untitled'}</h1>
              <p className="text-blue-300 mt-1 text-sm">{(listing.description as string) || ''}</p>
            </div>

            <div className="flex flex-wrap gap-2">
              {((work.tags as string[]) || []).map((tag) => (
                <span key={tag} className="px-2 py-1 bg-blue-900 text-blue-300 text-xs rounded-full">
                  {tag}
                </span>
              ))}
            </div>

            {/* Artist */}
            <div className="flex items-center gap-3 p-3 bg-blue-900/50 rounded-lg border border-blue-900/30">
              <div className="h-10 w-10 rounded-full bg-orange-500/20 flex items-center justify-center font-bold text-orange-400 text-sm">
                {((artist.display_name as string) || 'A')[0]?.toUpperCase()}
              </div>
              <div>
                <p className="text-sm font-medium text-white">
                  {(artist.display_name as string) || 'Anonymous'}
                  {(artist.verified as boolean) && <CheckCircle className="inline h-3.5 w-3.5 ml-1 text-orange-400" />}
                </p>
                {artist.total_sales !== undefined && (
                  <p className="text-xs text-blue-400">{artist.total_sales as number} sales</p>
                )}
              </div>
            </div>

            {/* Pricing */}
            <div className="border border-blue-900/30 rounded-xl p-4 space-y-3 bg-blue-900/30">
              <div className="flex justify-between items-center">
                <span className="text-sm text-blue-300">License type</span>
                <span className="text-sm font-semibold text-white capitalize">
                  {licenseType.replace('_', ' ')}
                </span>
              </div>
              {(listing.max_buyers as number | null) && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-blue-300">Copies available</span>
                  <span className="text-sm font-semibold text-white">
                    {(listing.max_buyers as number) - ((listing.sales_count as number) || 0)} / {listing.max_buyers as number}
                  </span>
                </div>
              )}
              {(listing.license_details as string | null) && (
                <p className="text-xs text-blue-400">{listing.license_details as string}</p>
              )}
              <div className="border-t border-blue-900/30 pt-3 flex items-center justify-between">
                <span className="text-2xl font-bold text-orange-500">
                  ${price.toFixed(2)}
                </span>
                <button
                  onClick={handlePurchase}
                  disabled={buying || status !== 'active'}
                  className="px-6 py-2.5 bg-orange-500 hover:bg-orange-600 disabled:opacity-60 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
                >
                  {buying ? 'Redirecting…' : status !== 'active' ? 'Sold out' : 'Buy license'}
                  {!buying && status === 'active' && <ExternalLink className="h-3.5 w-3.5" />}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

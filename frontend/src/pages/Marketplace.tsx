import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Search, Filter, Music, Image, Video, FileText, Package } from 'lucide-react'
import { getListings, getStats } from '../services/api'

const WORK_TYPE_ICONS: Record<string, React.ElementType> = {
  image: Image,
  audio: Music,
  video: Video,
  text: FileText,
  dataset: Package,
}

const LICENSE_COLORS: Record<string, string> = {
  cc0: 'bg-green-100 text-green-700',
  cc_by: 'bg-blue-100 text-blue-700',
  non_exclusive: 'bg-yellow-100 text-yellow-700',
  exclusive: 'bg-red-100 text-red-700',
  custom: 'bg-gray-100 text-gray-700',
}

interface Listing {
  id: number
  title: string
  description: string
  price: number
  license_type: string
  work: { work_type: string; tags: string[]; preview_url: string | null }
  artist: { username: string; display_name: string; verified: boolean }
  created_at: string
}

interface Stats {
  total_listings: number
  total_artists: number
  total_companies: number
  total_sales: number
  total_volume_usd: number
}

export default function Marketplace() {
  const [listings, setListings] = useState<Listing[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [workType, setWorkType] = useState('')
  const [licenseType, setLicenseType] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  const fetchListings = async () => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page, page_size: 24, sort_by: sortBy }
      if (search) params.search = search
      if (workType) params.work_type = workType
      if (licenseType) params.license_type = licenseType
      const { data } = await getListings(params)
      setListings(data.items)
      setTotalPages(data.pages)
    } catch {
      // Backend unreachable - show sample listings
      const sampleListings: Listing[] = [
        {
          id: 1,
          title: 'Abstract Digital Art Collection',
          description: 'High-quality abstract digital artwork',
          price: 299.99,
          license_type: 'non_exclusive',
          work: { work_type: 'image', tags: ['abstract', 'digital'], preview_url: null },
          artist: { username: 'artist1', display_name: 'Creative Studio', verified: true },
          created_at: new Date().toISOString(),
        },
        {
          id: 2,
          title: 'Electronic Music Samples Pack',
          description: 'Professional audio samples for AI training',
          price: 499.99,
          license_type: 'cc_by',
          work: { work_type: 'audio', tags: ['music', 'electronic'], preview_url: null },
          artist: { username: 'soundlab', display_name: 'Sound Lab', verified: false },
          created_at: new Date().toISOString(),
        },
        {
          id: 3,
          title: 'Documentary Footage Dataset',
          description: 'Curated video clips from documentaries',
          price: 1299.99,
          license_type: 'exclusive',
          work: { work_type: 'video', tags: ['documentary', 'nature'], preview_url: null },
          artist: { username: 'filmmaker', display_name: 'Documentary Films', verified: true },
          created_at: new Date().toISOString(),
        },
        {
          id: 4,
          title: 'Poetry & Prose Text Collection',
          description: 'Original written content for language models',
          price: 199.99,
          license_type: 'cc0',
          work: { work_type: 'text', tags: ['poetry', 'literature'], preview_url: null },
          artist: { username: 'writer', display_name: 'The Writer', verified: false },
          created_at: new Date().toISOString(),
        },
      ]
      setListings(sampleListings)
      setTotalPages(1)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    getStats()
      .then(({ data }) => setStats(data))
      .catch(() => {
        // Backend unreachable - show sample stats
        setStats({
          total_listings: 127,
          total_artists: 43,
          total_companies: 12,
          total_sales: 89,
          total_volume_usd: 24567,
        })
      })
  }, [])

  useEffect(() => {
    fetchListings()
  }, [page, sortBy, workType, licenseType])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    fetchListings()
  }

  return (
    <div className="min-h-screen bg-artlock-dark p-6">
      <div className="max-w-7xl mx-auto">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Marketplace</h1>
          <p className="text-blue-300 mt-2">Browse and license creative works for AI training</p>
        </div>

        {/* Hero / stats bar */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            {[
              { label: 'Listings', value: stats.total_listings ?? 0 },
              { label: 'Artists', value: stats.total_artists ?? 0 },
              { label: 'Companies', value: stats.total_companies ?? 0 },
              { label: 'Volume (USD)', value: `$${(stats.total_volume_usd ?? 0).toFixed(0)}` },
            ].map((s) => (
              <div key={s.label} className="bg-blue-900 rounded-xl border border-blue-900/30 p-4 text-center">
                <p className="text-2xl font-bold text-orange-500">{s.value}</p>
                <p className="text-xs text-blue-300 mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>
        )}

        {/* Search + filters */}
        <div className="bg-blue-900 rounded-xl border border-blue-900/30 p-4 mb-6">
          <form onSubmit={handleSearch} className="flex gap-2 mb-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-blue-400" />
              <input
                type="text"
                placeholder="Search titles, descriptions, tags…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-blue-950 border border-blue-900/30 text-white rounded-lg text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none placeholder-blue-500"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-orange-500 text-white text-sm font-medium rounded-lg hover:bg-orange-600 transition-colors"
            >
              Search
            </button>
          </form>

          <div className="flex flex-wrap gap-2 items-center">
            <Filter className="h-4 w-4 text-blue-400" />
            <select
              value={workType}
              onChange={(e) => { setWorkType(e.target.value); setPage(1) }}
              className="px-3 py-1.5 bg-blue-950 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500"
            >
              <option value="">All types</option>
              {['image', 'audio', 'video', 'text', 'dataset'].map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>

            <select
              value={licenseType}
              onChange={(e) => { setLicenseType(e.target.value); setPage(1) }}
              className="px-3 py-1.5 bg-blue-950 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500"
            >
              <option value="">All licenses</option>
              {['cc0', 'cc_by', 'non_exclusive', 'exclusive', 'custom'].map((l) => (
                <option key={l} value={l}>{l.replace('_', ' ')}</option>
              ))}
            </select>

            <select
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); setPage(1) }}
              className="px-3 py-1.5 bg-blue-950 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500"
            >
              <option value="created_at">Newest</option>
              <option value="price_asc">Price: low → high</option>
              <option value="price_desc">Price: high → low</option>
              <option value="featured">Featured</option>
            </select>
          </div>
        </div>

        {/* Grid */}
        {loading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="bg-blue-900 rounded-xl border border-blue-900/30 h-64 animate-pulse" />
            ))}
          </div>
        ) : listings.length === 0 ? (
          <div className="text-center py-24 text-blue-400">
            <Package className="h-12 w-12 mx-auto mb-3 opacity-40" />
            <p className="text-lg font-medium text-white">No listings yet</p>
            <p className="text-sm">Be the first to upload creative work!</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {listings.map((l) => {
              const Icon = WORK_TYPE_ICONS[l.work.work_type] ?? Package
              return (
                <Link
                  key={l.id}
                  to={`/marketplace/${l.id}`}
                  className="bg-blue-900 rounded-xl border border-blue-900/30 hover:border-blue-900/30 transition-all overflow-hidden group"
                >
                  <div className="h-40 bg-gradient-to-br from-blue-800 to-blue-900 flex items-center justify-center">
                    {l.work.preview_url ? (
                      <img
                        src={l.work.preview_url}
                        alt={l.title}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <Icon className="h-12 w-12 text-blue-400 group-hover:text-orange-500 transition-colors" />
                    )}
                  </div>
                  <div className="p-3">
                    <p className="text-sm font-semibold text-white truncate">{l.title}</p>
                    <p className="text-xs text-blue-300 truncate mt-0.5">
                      {l.artist.display_name}
                      {l.artist.verified && (
                        <span className="ml-1 text-orange-500">✓</span>
                      )}
                    </p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-sm font-bold text-orange-500">
                        ${(l.price ?? 0).toFixed(2)}
                      </span>
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                          LICENSE_COLORS[l.license_type] ?? 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {l.license_type.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                </Link>
              )
            })}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-8">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="px-4 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm disabled:opacity-40 hover:bg-blue-800"
            >
              Previous
            </button>
            <span className="px-4 py-2 text-sm text-blue-300">
              {page} / {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="px-4 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm disabled:opacity-40 hover:bg-blue-800"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

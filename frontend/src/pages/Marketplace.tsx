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
      // silently fail – no listings yet
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    getStats()
      .then(({ data }) => setStats(data))
      .catch(() => null)
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
    <div>
      {/* Hero / stats bar */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Listings', value: stats.total_listings },
            { label: 'Artists', value: stats.total_artists },
            { label: 'Companies', value: stats.total_companies },
            { label: 'Volume (USD)', value: `$${stats.total_volume_usd.toFixed(0)}` },
          ].map((s) => (
            <div key={s.label} className="bg-white rounded-xl border p-4 text-center">
              <p className="text-2xl font-bold text-violet-700">{s.value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Search + filters */}
      <div className="bg-white rounded-xl border p-4 mb-6">
        <form onSubmit={handleSearch} className="flex gap-2 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search titles, descriptions, tags…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-violet-600 text-white text-sm font-medium rounded-lg hover:bg-violet-700 transition-colors"
          >
            Search
          </button>
        </form>

        <div className="flex flex-wrap gap-2 items-center">
          <Filter className="h-4 w-4 text-gray-400" />
          <select
            value={workType}
            onChange={(e) => { setWorkType(e.target.value); setPage(1) }}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-violet-500"
          >
            <option value="">All types</option>
            {['image', 'audio', 'video', 'text', 'dataset'].map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>

          <select
            value={licenseType}
            onChange={(e) => { setLicenseType(e.target.value); setPage(1) }}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-violet-500"
          >
            <option value="">All licenses</option>
            {['cc0', 'cc_by', 'non_exclusive', 'exclusive', 'custom'].map((l) => (
              <option key={l} value={l}>{l.replace('_', ' ')}</option>
            ))}
          </select>

          <select
            value={sortBy}
            onChange={(e) => { setSortBy(e.target.value); setPage(1) }}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-violet-500"
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
            <div key={i} className="bg-white rounded-xl border h-64 animate-pulse" />
          ))}
        </div>
      ) : listings.length === 0 ? (
        <div className="text-center py-24 text-gray-400">
          <Package className="h-12 w-12 mx-auto mb-3 opacity-40" />
          <p className="text-lg font-medium">No listings yet</p>
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
                className="bg-white rounded-xl border hover:shadow-md transition-shadow overflow-hidden group"
              >
                <div className="h-40 bg-gradient-to-br from-violet-50 to-indigo-100 flex items-center justify-center">
                  {l.work.preview_url ? (
                    <img
                      src={l.work.preview_url}
                      alt={l.title}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <Icon className="h-12 w-12 text-violet-300 group-hover:text-violet-500 transition-colors" />
                  )}
                </div>
                <div className="p-3">
                  <p className="text-sm font-semibold text-gray-900 truncate">{l.title}</p>
                  <p className="text-xs text-gray-500 truncate mt-0.5">
                    {l.artist.display_name}
                    {l.artist.verified && (
                      <span className="ml-1 text-violet-500">✓</span>
                    )}
                  </p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-sm font-bold text-violet-700">
                      ${l.price.toFixed(2)}
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
            className="px-4 py-2 border rounded-lg text-sm disabled:opacity-40 hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-gray-600">
            {page} / {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="px-4 py-2 border rounded-lg text-sm disabled:opacity-40 hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}

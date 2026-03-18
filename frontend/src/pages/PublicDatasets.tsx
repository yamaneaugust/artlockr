import { useState, useEffect } from 'react'
import { Search, Database, Music, Image, Video, FileText, Package } from 'lucide-react'
import { getPublicDatasets, searchWikimedia } from '../services/api'

const WORK_TYPE_ICONS: Record<string, React.ElementType> = {
  image: Image, audio: Music, video: Video, text: FileText, dataset: Package,
}

interface Entry {
  id: number
  url: string
  work_type: string
  file_format: string
  dataset_source: string
  license_detected: string | null
  title_detected: string | null
  discovered_at: string
}

export default function PublicDatasets() {
  const [entries, setEntries] = useState<Entry[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'catalogue' | 'wikimedia'>('catalogue')
  const [wikiQuery, setWikiQuery] = useState('')
  const [wikiResults, setWikiResults] = useState<Record<string, unknown>[]>([])
  const [wikiLoading, setWikiLoading] = useState(false)
  const [workType, setWorkType] = useState('')

  useEffect(() => {
    if (tab !== 'catalogue') return
    setLoading(true)
    getPublicDatasets({ work_type: workType || undefined })
      .then(({ data }) => {
        setEntries(data.items)
        setTotal(data.total)
      })
      .catch(() => null)
      .finally(() => setLoading(false))
  }, [tab, workType])

  const handleWikiSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!wikiQuery.trim()) return
    setWikiLoading(true)
    try {
      const { data } = await searchWikimedia(wikiQuery)
      setWikiResults(data.results)
    } catch {
      // noop
    } finally {
      setWikiLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Public Creative Datasets</h1>
        <p className="text-sm text-gray-500 mt-1">
          Freely-licensed works discovered from Common Crawl, Wikimedia Commons, and more.
        </p>
      </div>

      <div className="flex gap-2 mb-6">
        {(['catalogue', 'wikimedia'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              tab === t
                ? 'bg-violet-600 text-white'
                : 'bg-white border text-gray-600 hover:bg-gray-50'
            }`}
          >
            {t === 'catalogue' ? 'Catalogue' : 'Search Wikimedia'}
          </button>
        ))}
      </div>

      {tab === 'catalogue' && (
        <>
          <div className="flex items-center gap-2 mb-4">
            <select
              value={workType}
              onChange={(e) => setWorkType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-violet-500"
            >
              <option value="">All types</option>
              {['image', 'audio', 'video', 'text', 'dataset'].map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <span className="text-sm text-gray-500">{total.toLocaleString()} entries</span>
          </div>

          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="bg-white rounded-xl border h-16 animate-pulse" />
              ))}
            </div>
          ) : entries.length === 0 ? (
            <div className="text-center py-20 text-gray-400">
              <Database className="h-12 w-12 mx-auto mb-3 opacity-40" />
              <p className="text-lg font-medium">No entries yet</p>
              <p className="text-sm">Trigger a Common Crawl scan from the admin panel.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {entries.map((e) => {
                const Icon = WORK_TYPE_ICONS[e.work_type] ?? Package
                return (
                  <a
                    key={e.id}
                    href={e.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 bg-white rounded-xl border p-4 hover:shadow-sm transition-shadow"
                  >
                    <Icon className="h-5 w-5 text-violet-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {e.title_detected || e.url}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {e.dataset_source} · {e.file_format}
                        {e.license_detected && ` · ${e.license_detected}`}
                      </p>
                    </div>
                    <span className="text-xs text-gray-400 flex-shrink-0">
                      {new Date(e.discovered_at).toLocaleDateString()}
                    </span>
                  </a>
                )
              })}
            </div>
          )}
        </>
      )}

      {tab === 'wikimedia' && (
        <>
          <form onSubmit={handleWikiSearch} className="flex gap-2 mb-6">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search Wikimedia Commons…"
                value={wikiQuery}
                onChange={(e) => setWikiQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>
            <button
              type="submit"
              disabled={wikiLoading}
              className="px-4 py-2 bg-violet-600 text-white text-sm font-medium rounded-lg hover:bg-violet-700 disabled:opacity-60 transition-colors"
            >
              {wikiLoading ? 'Searching…' : 'Search'}
            </button>
          </form>

          {wikiResults.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {wikiResults.map((r, i) => (
                <a
                  key={i}
                  href={r.url as string}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-white rounded-xl border overflow-hidden hover:shadow-md transition-shadow group"
                >
                  {r.work_type === 'image' && (
                    <img
                      src={r.url as string}
                      alt={r.title_detected as string}
                      className="h-36 w-full object-cover"
                      onError={(e) => ((e.target as HTMLImageElement).style.display = 'none')}
                    />
                  )}
                  <div className="p-3">
                    <p className="text-xs font-medium text-gray-900 line-clamp-2">
                      {r.title_detected as string}
                    </p>
                    {r.license_detected && (
                      <span className="text-xs text-green-600 mt-1 block">
                        {r.license_detected as string}
                      </span>
                    )}
                  </div>
                </a>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

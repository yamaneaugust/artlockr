import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload as UploadIcon, CheckCircle2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { uploadWork, createListing } from '../services/api'
import { useAuthStore } from '../store/authStore'

const LICENSE_OPTIONS = [
  { value: 'cc0', label: 'CC0 – Public Domain' },
  { value: 'cc_by', label: 'CC-BY – Attribution required' },
  { value: 'non_exclusive', label: 'Non-exclusive commercial license' },
  { value: 'exclusive', label: 'Exclusive license (single buyer)' },
  { value: 'custom', label: 'Custom license' },
]

export default function Upload() {
  const { user } = useAuthStore()
  const [file, setFile] = useState<File | null>(null)
  const [step, setStep] = useState<'upload' | 'listing' | 'done'>('upload')
  const [workId, setWorkId] = useState<number | null>(null)
  const [uploading, setUploading] = useState(false)
  const [listing, setListing] = useState(false)

  const [meta, setMeta] = useState({
    title: '',
    description: '',
    tags: '',
    style: 'general',
  })

  const [listingForm, setListingForm] = useState({
    title: '',
    description: '',
    price: '',
    license_type: 'non_exclusive',
    license_details: '',
    max_buyers: '',
  })

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      'image/*': [],
      'audio/*': [],
      'video/*': [],
      'text/plain': [],
      'application/zip': [],
    },
  })

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || !user) return
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('title', meta.title)
      fd.append('description', meta.description)
      fd.append('tags', meta.tags)
      fd.append('style', meta.style)
      fd.append('artist_id', String(user.id))
      const { data } = await uploadWork(fd)
      setWorkId(data.work_id)
      setListingForm((f) => ({ ...f, title: meta.title }))
      toast.success('Work uploaded!')
      setStep('listing')
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Upload failed'
      toast.error(msg)
    } finally {
      setUploading(false)
    }
  }

  const handleCreateListing = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!workId || !user) return
    setListing(true)
    try {
      const fd = new FormData()
      fd.append('work_id', String(workId))
      fd.append('artist_id', String(user.id))
      fd.append('title', listingForm.title)
      fd.append('description', listingForm.description)
      fd.append('price', listingForm.price)
      fd.append('license_type', listingForm.license_type)
      fd.append('license_details', listingForm.license_details)
      if (listingForm.max_buyers) fd.append('max_buyers', listingForm.max_buyers)
      await createListing(fd)
      toast.success('Listing created!')
      setStep('done')
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Failed to create listing'
      toast.error(msg)
    } finally {
      setListing(false)
    }
  }

  if (step === 'done') {
    return (
      <div className="min-h-screen bg-blue-950 flex items-center justify-center p-4">
        <div className="max-w-lg mx-auto text-center py-20">
          <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white">Listing live!</h2>
          <p className="text-blue-300 mt-2">Your work is now listed on the marketplace.</p>
          <button
            onClick={() => {
              setStep('upload')
              setFile(null)
              setWorkId(null)
            }}
            className="mt-6 px-6 py-2.5 bg-orange-500 text-white rounded-lg font-medium hover:bg-orange-600"
          >
            Upload another
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-blue-950 p-6">
      <div className="max-w-2xl mx-auto space-y-8">
        <h1 className="text-2xl font-bold text-white">
          {step === 'upload' ? 'Upload Creative Work' : 'Create Listing'}
        </h1>

        {step === 'upload' && (
          <form onSubmit={handleUpload} className="space-y-6">
            {/* Dropzone */}
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-blue-900/30 bg-orange-500/10'
                  : file
                  ? 'border-green-400 bg-green-400/10'
                  : 'border-blue-900/30 bg-blue-900 hover:border-blue-900/30'
              }`}
            >
              <input {...getInputProps()} />
              <UploadIcon className="h-10 w-10 mx-auto text-blue-400 mb-2" />
              {file ? (
                <p className="text-sm font-medium text-green-400">{file.name}</p>
              ) : (
                <>
                  <p className="text-sm font-medium text-white">
                    Drop your file here or click to browse
                  </p>
                  <p className="text-xs text-blue-400 mt-1">
                    Images, audio, video, text, or ZIP datasets
                  </p>
                </>
              )}
            </div>

            <div className="grid gap-4">
              <div>
                <label className="block text-sm font-medium text-blue-200 mb-1">Title *</label>
                <input
                  required
                  value={meta.title}
                  onChange={(e) => setMeta((m) => ({ ...m, title: e.target.value }))}
                  className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500 placeholder-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-blue-200 mb-1">Description</label>
                <textarea
                  rows={3}
                  value={meta.description}
                  onChange={(e) => setMeta((m) => ({ ...m, description: e.target.value }))}
                  className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500 resize-none placeholder-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-blue-200 mb-1">
                  Tags (comma-separated)
                </label>
                <input
                  value={meta.tags}
                  onChange={(e) => setMeta((m) => ({ ...m, tags: e.target.value }))}
                  placeholder="portrait, oil painting, landscape"
                  className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500 placeholder-blue-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={!file || uploading}
              className="w-full py-3 bg-orange-500 hover:bg-orange-600 disabled:opacity-60 text-white font-medium rounded-lg transition-colors"
            >
              {uploading ? 'Uploading…' : 'Upload & continue'}
            </button>
          </form>
        )}

        {step === 'listing' && (
          <form onSubmit={handleCreateListing} className="space-y-5">
            <div className="grid gap-4">
              <div>
                <label className="block text-sm font-medium text-blue-200 mb-1">Listing title *</label>
                <input
                  required
                  value={listingForm.title}
                  onChange={(e) => setListingForm((f) => ({ ...f, title: e.target.value }))}
                  className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500 placeholder-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-blue-200 mb-1">Description</label>
                <textarea
                  rows={3}
                  value={listingForm.description}
                  onChange={(e) => setListingForm((f) => ({ ...f, description: e.target.value }))}
                  className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500 resize-none placeholder-blue-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-blue-200 mb-1">Price (USD) *</label>
                  <input
                    required
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={listingForm.price}
                    onChange={(e) => setListingForm((f) => ({ ...f, price: e.target.value }))}
                    className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500 placeholder-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-blue-200 mb-1">Max buyers</label>
                  <input
                    type="number"
                    min="1"
                    placeholder="Unlimited"
                    value={listingForm.max_buyers}
                    onChange={(e) => setListingForm((f) => ({ ...f, max_buyers: e.target.value }))}
                    className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500 placeholder-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-blue-200 mb-1">License type *</label>
                <select
                  value={listingForm.license_type}
                  onChange={(e) => setListingForm((f) => ({ ...f, license_type: e.target.value }))}
                  className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500"
                >
                  {LICENSE_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-blue-200 mb-1">
                  License details / terms
                </label>
                <textarea
                  rows={2}
                  value={listingForm.license_details}
                  onChange={(e) =>
                    setListingForm((f) => ({ ...f, license_details: e.target.value }))
                  }
                  placeholder="Any specific restrictions or permissions…"
                  className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500 resize-none placeholder-blue-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={listing}
              className="w-full py-3 bg-orange-500 hover:bg-orange-600 disabled:opacity-60 text-white font-medium rounded-lg transition-colors"
            >
              {listing ? 'Creating listing…' : 'Publish listing'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

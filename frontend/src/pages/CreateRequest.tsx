import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, CheckCircle2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuthStore } from '../store/authStore'

const WORK_TYPES = [
  { value: 'image', label: 'Images / Artwork' },
  { value: 'audio', label: 'Audio / Music' },
  { value: 'video', label: 'Video' },
  { value: 'text', label: 'Text / Writing' },
  { value: 'dataset', label: 'Dataset (mixed)' },
]

const LICENSE_TYPES = [
  { value: 'any', label: 'Any license' },
  { value: 'cc0', label: 'CC0 – Public Domain' },
  { value: 'cc_by', label: 'CC-BY – Attribution' },
  { value: 'non_exclusive', label: 'Non-exclusive commercial' },
  { value: 'exclusive', label: 'Exclusive license' },
]

export default function CreateRequest() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const [form, setForm] = useState({
    title: '',
    description: '',
    work_type: 'image',
    license_type: 'any',
    quantity: '',
    budget_min: '',
    budget_max: '',
    deadline: '',
    requirements: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return
    setSubmitting(true)

    try {
      await new Promise((resolve) => setTimeout(resolve, 500))
      const requests = JSON.parse(localStorage.getItem('artlock-requests') || '[]')
      requests.push({
        id: Date.now(),
        company_id: user.id,
        company_username: user.username,
        company_name: user.company_name || user.username,
        title: form.title,
        description: form.description,
        work_type: form.work_type,
        license_type: form.license_type,
        quantity: form.quantity ? parseInt(form.quantity) : null,
        budget_min: form.budget_min ? parseFloat(form.budget_min) : null,
        budget_max: form.budget_max ? parseFloat(form.budget_max) : null,
        deadline: form.deadline || null,
        requirements: form.requirements,
        status: 'open',
        created_at: new Date().toISOString(),
      })
      localStorage.setItem('artlock-requests', JSON.stringify(requests))
      toast.success('Request posted!')
      setSubmitted(true)
    } catch {
      toast.error('Failed to create request')
    } finally {
      setSubmitting(false)
    }
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-artlock-dark flex items-center justify-center p-4">
        <div className="max-w-lg mx-auto text-center py-20">
          <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white">Request posted!</h2>
          <p className="text-blue-300 mt-2">
            Artists can now see your request and respond with matching work.
          </p>
          <div className="flex gap-3 justify-center mt-6">
            <button
              onClick={() => {
                setSubmitted(false)
                setForm({
                  title: '',
                  description: '',
                  work_type: 'image',
                  license_type: 'any',
                  quantity: '',
                  budget_min: '',
                  budget_max: '',
                  deadline: '',
                  requirements: '',
                })
              }}
              className="px-6 py-2.5 bg-blue-900 hover:bg-blue-800 text-white rounded-lg font-medium border border-blue-900/30"
            >
              Create another
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-6 py-2.5 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium"
            >
              Go to dashboard
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-artlock-dark p-6">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-full bg-orange-500/20 flex items-center justify-center">
            <Plus className="h-6 w-6 text-orange-500" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Create Data Request</h1>
            <p className="text-sm text-blue-300">
              Post what kind of training data you're looking for
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-blue-200 mb-1">
              Request title *
            </label>
            <input
              required
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              placeholder="e.g. High-quality landscape photography"
              className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500 placeholder-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-blue-200 mb-1">
              Description *
            </label>
            <textarea
              required
              rows={4}
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              placeholder="Describe what you're looking for, the use case, and any specific needs..."
              className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500 resize-none placeholder-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-blue-200 mb-1">Data type *</label>
              <select
                value={form.work_type}
                onChange={(e) => setForm((f) => ({ ...f, work_type: e.target.value }))}
                className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500"
              >
                {WORK_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-blue-200 mb-1">License type</label>
              <select
                value={form.license_type}
                onChange={(e) => setForm((f) => ({ ...f, license_type: e.target.value }))}
                className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500"
              >
                {LICENSE_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-blue-200 mb-1">
              Quantity needed
            </label>
            <input
              type="number"
              min="1"
              value={form.quantity}
              onChange={(e) => setForm((f) => ({ ...f, quantity: e.target.value }))}
              placeholder="e.g. 1000"
              className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500 placeholder-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-blue-200 mb-1">
                Min budget (USD)
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={form.budget_min}
                onChange={(e) => setForm((f) => ({ ...f, budget_min: e.target.value }))}
                placeholder="0"
                className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500 placeholder-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-blue-200 mb-1">
                Max budget (USD)
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={form.budget_max}
                onChange={(e) => setForm((f) => ({ ...f, budget_max: e.target.value }))}
                placeholder="10000"
                className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500 placeholder-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-blue-200 mb-1">Deadline</label>
            <input
              type="date"
              value={form.deadline}
              onChange={(e) => setForm((f) => ({ ...f, deadline: e.target.value }))}
              className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-blue-200 mb-1">
              Additional requirements
            </label>
            <textarea
              rows={3}
              value={form.requirements}
              onChange={(e) => setForm((f) => ({ ...f, requirements: e.target.value }))}
              placeholder="Specific styles, resolutions, formats, licenses, etc."
              className="w-full px-3 py-2 bg-blue-900 border border-blue-900/30 text-white rounded-lg text-sm outline-none focus:ring-2 focus:ring-orange-500 resize-none placeholder-blue-500"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="flex-1 py-3 bg-blue-900 hover:bg-blue-800 text-white font-medium rounded-lg border border-blue-900/30 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 py-3 bg-orange-500 hover:bg-orange-600 disabled:opacity-60 text-white font-medium rounded-lg transition-colors"
            >
              {submitting ? 'Posting…' : 'Post request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

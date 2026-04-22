import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Lock } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

export default function Login() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { login, register } = useAuthStore()

  // Get role and mode from URL
  const urlRole = searchParams.get('role') as 'artist' | 'company' | null
  const urlMode = searchParams.get('mode') as 'login' | 'register' | null
  const hasPreselectedRole = urlRole !== null

  // If role is specified, default to register. Otherwise default to login
  const [mode, setMode] = useState<'login' | 'register'>(
    urlMode || (hasPreselectedRole ? 'register' : 'login')
  )
  const [loading, setLoading] = useState(false)

  const [form, setForm] = useState({
    email: '',
    username: '',
    password: '',
    role: (urlRole || 'artist') as 'artist' | 'company',
    company_name: '',
  })

  // Update role if URL param changes
  useEffect(() => {
    if (urlRole) {
      setForm(f => ({ ...f, role: urlRole }))
    }
  }, [urlRole])

  const [emailError, setEmailError] = useState('')

  const update = (k: keyof typeof form, v: string) => {
    setForm((f) => ({ ...f, [k]: v }))
    if (k === 'email') setEmailError('')
  }

  const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!isValidEmail(form.email)) {
      setEmailError('Please enter a valid email address')
      return
    }

    setLoading(true)
    try {
      if (mode === 'login') {
        await login(form.email, form.password)
      } else {
        await register(
          form.email,
          form.username,
          form.password,
          form.role,
          form.role === 'company' ? form.company_name : undefined,
        )
      }
      navigate('/dashboard')
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Something went wrong'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const getRoleLabel = () => {
    if (form.role === 'artist') return 'Creator'
    return 'AI Company'
  }

  return (
    <div className="min-h-screen bg-[#0a0e27] flex items-center justify-center p-4">
      <div className="bg-[#0a0e27] rounded-2xl shadow-xl w-full max-w-md p-8 border border-blue-900/60">
        <div className="flex flex-col items-center mb-8">
          <Lock className="h-10 w-10 text-orange-500 mb-2" fill="currentColor" />
          <h1 className="text-2xl font-bold text-white">ArtLock</h1>
          <p className="text-sm text-blue-300 mt-1">Creative Data Marketplace</p>
        </div>

        {/* Show role badge if pre-selected */}
        {hasPreselectedRole && (
          <div className="mb-6 p-3 bg-orange-500/10 border border-orange-500/30 rounded-lg text-center">
            <p className="text-sm text-orange-400">
              Signing up as: <span className="font-semibold">{getRoleLabel()}</span>
            </p>
          </div>
        )}

        <div className="flex rounded-lg bg-blue-950/60 p-1 mb-6">
          {(['login', 'register'] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                mode === m
                  ? 'bg-orange-500 text-white shadow-sm'
                  : 'text-blue-300 hover:text-white'
              }`}
            >
              {m === 'login' ? 'Sign in' : 'Create account'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-blue-200 mb-1">Email</label>
            <input
              type="text"
              value={form.email}
              onChange={(e) => update('email', e.target.value)}
              className={`w-full px-3 py-2 bg-[#050823] border text-white rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none placeholder-blue-500 ${emailError ? 'border-red-500' : 'border-blue-700'}`}
            />
            {emailError && (
              <p className="mt-1 text-sm text-red-400">{emailError}</p>
            )}
          </div>

          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium text-blue-200 mb-1">Username</label>
              <input
                type="text"
                required
                value={form.username}
                onChange={(e) => update('username', e.target.value)}
                className="w-full px-3 py-2 bg-[#050823] border border-blue-700 text-white rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none placeholder-blue-500"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-blue-200 mb-1">Password</label>
            <input
              type="password"
              required
              value={form.password}
              onChange={(e) => update('password', e.target.value)}
              className="w-full px-3 py-2 bg-[#050823] border border-blue-700 text-white rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none placeholder-blue-500"
            />
          </div>

          {/* Only show role selector if not pre-selected and in register mode */}
          {mode === 'register' && !hasPreselectedRole && (
            <div>
              <label className="block text-sm font-medium text-blue-200 mb-2">
                I am a…
              </label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { value: 'artist', label: "Creator", sub: "sell my creative work" },
                  { value: 'company', label: "AI Company", sub: "buy licensed datasets" },
                ].map(({ value, label, sub }) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => update('role', value)}
                    className={`p-3 rounded-lg border-2 text-left transition-colors ${
                      form.role === value
                        ? 'border-orange-500 bg-orange-500/10'
                        : 'border-blue-700 hover:border-blue-500'
                    }`}
                  >
                    <p className={`text-sm font-semibold ${form.role === value ? 'text-orange-400' : 'text-white'}`}>
                      {label}
                    </p>
                    <p className="text-xs text-blue-400 mt-0.5">{sub}</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {mode === 'register' && form.role === 'company' && (
            <div>
              <label className="block text-sm font-medium text-blue-200 mb-1">
                Company name
              </label>
              <input
                type="text"
                required
                value={form.company_name}
                onChange={(e) => update('company_name', e.target.value)}
                className="w-full px-3 py-2 bg-[#050823] border border-blue-700 text-white rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none placeholder-blue-500"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-orange-500 hover:bg-orange-600 disabled:opacity-60 text-white font-medium rounded-lg transition-colors"
          >
            {loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>
      </div>
    </div>
  )
}

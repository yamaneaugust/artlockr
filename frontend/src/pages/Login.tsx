import { useState } from 'react'
import { useNavigate, Link, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Palette } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

export default function Login() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { login, register } = useAuthStore()
  const [mode, setMode] = useState<'login' | 'register'>('register')
  const [loading, setLoading] = useState(false)

  const initialRole = (searchParams.get('role') as 'artist' | 'company') || 'artist'

  const [form, setForm] = useState({
    email: '',
    username: '',
    password: '',
    role: initialRole,
    company_name: '',
  })

  const update = (k: keyof typeof form, v: string) =>
    setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
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
      toast.success(mode === 'login' ? 'Welcome back!' : 'Account created!')
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

  return (
    <div className="min-h-screen bg-blue-950 flex items-center justify-center p-4">
      <div className="bg-blue-900 rounded-2xl shadow-xl w-full max-w-md p-8 border border-blue-800">
        <div className="flex flex-col items-center mb-8">
          <Palette className="h-10 w-10 text-orange-500 mb-2" />
          <h1 className="text-2xl font-bold text-white">ArtLock</h1>
          <p className="text-sm text-blue-300 mt-1">Creative Data Marketplace</p>
        </div>

        <div className="flex rounded-lg bg-blue-950 p-1 mb-6">
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
              type="email"
              required
              value={form.email}
              onChange={(e) => update('email', e.target.value)}
              className="w-full px-3 py-2 bg-blue-950 border border-blue-700 text-white rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none placeholder-blue-500"
            />
          </div>

          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium text-blue-200 mb-1">Username</label>
              <input
                type="text"
                required
                value={form.username}
                onChange={(e) => update('username', e.target.value)}
                className="w-full px-3 py-2 bg-blue-950 border border-blue-700 text-white rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none placeholder-blue-500"
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
              className="w-full px-3 py-2 bg-blue-950 border border-blue-700 text-white rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none placeholder-blue-500"
            />
          </div>

          {mode === 'register' && (
            <>
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

              {form.role === 'company' && (
                <div>
                  <label className="block text-sm font-medium text-blue-200 mb-1">
                    Company name
                  </label>
                  <input
                    type="text"
                    required
                    value={form.company_name}
                    onChange={(e) => update('company_name', e.target.value)}
                    className="w-full px-3 py-2 bg-blue-950 border border-blue-700 text-white rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none placeholder-blue-500"
                  />
                </div>
              )}
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-orange-500 hover:bg-orange-600 disabled:opacity-60 text-white font-medium rounded-lg transition-colors"
          >
            {loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-blue-400">
          Or{' '}
          <Link to="/marketplace" className="text-orange-400 hover:text-orange-300 hover:underline">
            browse the marketplace without signing in
          </Link>
        </p>
      </div>
    </div>
  )
}

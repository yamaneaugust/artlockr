import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Lock, Camera, FileCheck, Search, FileText } from 'lucide-react'

function useInView<T extends HTMLElement>(options?: IntersectionObserverInit) {
  const ref = useRef<T | null>(null)
  const [inView, setInView] = useState(false)

  useEffect(() => {
    const node = ref.current
    if (!node) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true)
          observer.unobserve(entry.target)
        }
      },
      { threshold: 0.25, rootMargin: '0px 0px -10% 0px', ...options },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [options])

  return { ref, inView }
}

function RevealSection({
  children,
  className = '',
  delay = 0,
}: {
  children: React.ReactNode
  className?: string
  delay?: number
}) {
  const { ref, inView } = useInView<HTMLElement>()
  return (
    <section
      ref={ref}
      className={`${className} transition-all duration-1000 ease-out will-change-transform ${
        inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
      }`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </section>
  )
}

export default function Homepage() {
  return (
    <div className="min-h-screen bg-[#0a0e27] text-white overflow-hidden relative">
      {/* Starfield background */}
      <div className="fixed inset-0 opacity-50">
        <div className="absolute inset-0" style={{
          backgroundImage: `
            radial-gradient(2px 2px at 20% 30%, white, transparent),
            radial-gradient(2px 2px at 60% 70%, white, transparent),
            radial-gradient(1px 1px at 50% 50%, white, transparent),
            radial-gradient(1px 1px at 80% 10%, white, transparent),
            radial-gradient(2px 2px at 90% 60%, white, transparent),
            radial-gradient(1px 1px at 33% 85%, white, transparent),
            radial-gradient(1px 1px at 75% 40%, white, transparent)
          `,
          backgroundSize: '200% 200%',
          backgroundPosition: '50% 50%'
        }} />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 border-b border-blue-900/30">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2">
              <Lock className="h-8 w-8 text-orange-500" fill="currentColor" />
              <span className="text-xl font-bold text-white">ArtLock</span>
            </Link>

            {/* Center Nav */}
            <div className="hidden md:flex items-center gap-8">
              <Link to="/features" className="text-gray-300 hover:text-white transition-colors">
                Features
              </Link>
              <Link to="/detect" className="text-gray-300 hover:text-white transition-colors">
                Verify Datasets
              </Link>
              <Link to="/marketplace" className="text-gray-300 hover:text-white transition-colors">
                Marketplace
              </Link>
            </div>

            {/* Right Nav */}
            <div className="flex items-center gap-4">
              <Link
                to="/login"
                className="text-gray-300 hover:text-white transition-colors px-4 py-2"
              >
                Log In
              </Link>
              <Link
                to="/login?role=artist"
                className="bg-orange-500 hover:bg-orange-600 text-white font-medium px-6 py-2 rounded-lg transition-colors"
              >
                Sign Up
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-20 px-6 overflow-hidden">
        {/* Orange particle effects */}
        <div className="absolute top-20 right-1/4 w-2 h-2 bg-orange-500 rounded-full blur-sm animate-pulse" />
        <div className="absolute top-40 right-1/3 w-1 h-1 bg-orange-400 rounded-full blur-sm" style={{ animationDelay: '1s' }} />
        <div className="absolute top-60 right-1/2 w-1.5 h-1.5 bg-orange-500 rounded-full blur-sm animate-pulse" style={{ animationDelay: '2s' }} />

        <div className="max-w-7xl mx-auto relative z-10">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            {/* Left: Text Content */}
            <div>
              <h1 className="text-5xl md:text-6xl font-bold leading-tight mb-8">
                Track, <span className="text-orange-500">license</span>, and{' '}
                <span className="text-orange-500">verify</span>
                <br />
                creative content used
                <br />
                in AI <span className="text-orange-500">datasets</span>.
              </h1>
              <div className="flex flex-wrap gap-4">
                <Link
                  to="/login?role=artist"
                  className="px-8 py-4 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-lg transition-colors"
                >
                  I'm a Creator
                </Link>
                <Link
                  to="/login?role=company"
                  className="px-8 py-4 border border-blue-900/30 text-orange-400 hover:bg-orange-500 hover:text-white font-semibold rounded-lg transition-colors"
                >
                  I'm an AI Company
                </Link>
              </div>
            </div>

            {/* Right: Holographic Visual - Fingerprint & Screens */}
            <div className="hidden md:block relative h-96">
              <div className="absolute inset-0">
                {/* Main fingerprint hologram screen */}
                <div className="absolute top-0 right-0 w-80 h-72 border border-blue-900/30 rounded-2xl bg-gradient-to-br from-orange-500/10 via-transparent to-blue-900/20 backdrop-blur-sm transform rotate-6 shadow-2xl shadow-orange-500/30 overflow-hidden">
                  {/* Fingerprint glow */}
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32">
                    <div className="absolute inset-0 rounded-full bg-gradient-radial from-orange-500 via-orange-400 to-transparent opacity-80 blur-xl" />
                    <div className="absolute inset-2 rounded-full" style={{
                      background: `
                        repeating-radial-gradient(circle at center,
                          transparent 0px,
                          transparent 4px,
                          rgba(255, 140, 0, 0.6) 5px,
                          transparent 6px,
                          transparent 10px
                        )
                      `
                    }} />
                  </div>
                  {/* Terminal-like lines */}
                  <div className="absolute top-4 left-4 right-4 space-y-1 opacity-40">
                    <div className="h-0.5 bg-orange-400/60 w-3/4" />
                    <div className="h-0.5 bg-orange-400/40 w-1/2" />
                    <div className="h-0.5 bg-orange-400/50 w-2/3" />
                  </div>
                  {/* Link icon */}
                  <div className="absolute bottom-4 right-4">
                    <svg className="w-12 h-12 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round"/>
                      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round"/>
                    </svg>
                  </div>
                </div>

                {/* Smaller screen accent */}
                <div className="absolute bottom-8 left-0 w-40 h-32 border border-blue-900/30 rounded-xl bg-gradient-to-tl from-orange-500/10 to-transparent transform -rotate-12" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Tagline Panel 1 — "Your Key. Your Art. Your Identity." */}
      <RevealSection className="relative py-32 px-6 overflow-hidden">
        {/* Background holographic key ring */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {/* Left: floating key card */}
          <div className="absolute top-1/2 left-8 md:left-20 -translate-y-1/2 w-40 h-52 border border-blue-900/30 rounded-2xl bg-gradient-to-br from-orange-500/10 via-transparent to-blue-900/20 backdrop-blur-sm transform -rotate-12 shadow-2xl shadow-orange-500/20">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
              <Lock className="w-14 h-14 text-orange-400" strokeWidth={1.5} />
            </div>
            <div className="absolute top-3 left-3 right-3 space-y-1 opacity-40">
              <div className="h-0.5 bg-orange-400/60 w-3/4" />
              <div className="h-0.5 bg-orange-400/40 w-1/2" />
            </div>
          </div>

          {/* Right: floating fingerprint card */}
          <div className="absolute top-1/2 right-8 md:right-20 -translate-y-1/2 w-44 h-52 border border-blue-900/30 rounded-2xl bg-gradient-to-bl from-orange-500/10 via-transparent to-blue-900/20 backdrop-blur-sm transform rotate-6 shadow-2xl shadow-orange-500/30 overflow-hidden">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24">
              <div className="absolute inset-0 rounded-full bg-gradient-radial from-orange-500 via-orange-400 to-transparent opacity-70 blur-lg" />
              <div className="absolute inset-1 rounded-full" style={{
                background: `repeating-radial-gradient(circle at center,
                  transparent 0px, transparent 3px,
                  rgba(255, 140, 0, 0.6) 4px, transparent 5px, transparent 8px)`
              }} />
            </div>
          </div>

          {/* Orange particle effects */}
          <div className="absolute top-10 left-1/3 w-1.5 h-1.5 bg-orange-500 rounded-full blur-sm animate-pulse" />
          <div className="absolute bottom-12 right-1/4 w-1 h-1 bg-orange-400 rounded-full blur-sm animate-pulse" style={{ animationDelay: '1.5s' }} />
          <div className="absolute top-20 right-1/3 w-2 h-2 bg-orange-500 rounded-full blur-sm animate-pulse" style={{ animationDelay: '0.8s' }} />
          <div className="absolute bottom-20 left-1/4 w-1 h-1 bg-orange-400 rounded-full blur-sm" />
        </div>

        <div className="max-w-5xl mx-auto text-center relative z-10">
          <h2 className="text-4xl md:text-6xl font-bold leading-tight">
            Your <span className="text-orange-500">Key</span>. Your <span className="text-orange-500">Art</span>. Your <span className="text-orange-500">Identity</span>.
          </h2>
          <p className="mt-6 text-lg md:text-xl text-gray-400 max-w-2xl mx-auto">
            Every work you register carries a cryptographic fingerprint — provably yours, forever.
          </p>
        </div>
      </RevealSection>

      {/* Tagline Panel 2 — "Train on data you can trust" */}
      <RevealSection className="relative py-32 px-6 overflow-hidden">
        {/* Background holographic data screens */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {/* Left: data chart card */}
          <div className="absolute top-1/2 left-8 md:left-24 -translate-y-1/2 w-48 h-56 border border-blue-900/30 rounded-2xl bg-gradient-to-br from-orange-900/20 via-blue-900/10 to-transparent backdrop-blur-sm transform -rotate-6 shadow-xl shadow-orange-500/20">
            <div className="p-4 space-y-2 opacity-70">
              <div className="flex items-end gap-1.5 h-24">
                <div className="w-3 bg-orange-500/60 h-10 rounded-t" />
                <div className="w-3 bg-orange-500/70 h-16 rounded-t" />
                <div className="w-3 bg-orange-500/50 h-12 rounded-t" />
                <div className="w-3 bg-orange-500/80 h-20 rounded-t" />
                <div className="w-3 bg-orange-500/60 h-14 rounded-t" />
                <div className="w-3 bg-orange-500/70 h-18 rounded-t" />
              </div>
              <div className="space-y-1 pt-2">
                <div className="h-1 bg-orange-400/50 w-3/4 rounded" />
                <div className="h-1 bg-orange-400/40 w-1/2 rounded" />
                <div className="h-1 bg-orange-400/60 w-2/3 rounded" />
              </div>
            </div>
          </div>

          {/* Right: verification card */}
          <div className="absolute top-1/2 right-8 md:right-24 -translate-y-1/2 w-44 h-56 border border-blue-900/30 rounded-2xl bg-gradient-to-bl from-orange-500/10 via-transparent to-blue-900/20 backdrop-blur-sm transform rotate-6 shadow-2xl shadow-orange-500/30 overflow-hidden">
            <div className="absolute top-3 left-3 right-3 space-y-1 opacity-40">
              <div className="h-0.5 bg-orange-400/60 w-3/4" />
              <div className="h-0.5 bg-orange-400/40 w-1/2" />
              <div className="h-0.5 bg-orange-400/50 w-2/3" />
            </div>
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
              <div className="relative">
                <div className="absolute inset-0 rounded-full bg-orange-500/40 blur-xl" />
                <FileCheck className="w-14 h-14 text-orange-400 relative" strokeWidth={1.5} />
              </div>
            </div>
            <div className="absolute bottom-3 left-3 right-3 space-y-1 opacity-40">
              <div className="h-0.5 bg-orange-400/50 w-2/3" />
              <div className="h-0.5 bg-orange-400/40 w-3/4" />
            </div>
          </div>

          {/* Orange particle effects */}
          <div className="absolute top-16 right-1/3 w-1.5 h-1.5 bg-orange-500 rounded-full blur-sm animate-pulse" style={{ animationDelay: '0.3s' }} />
          <div className="absolute bottom-16 left-1/3 w-1 h-1 bg-orange-400 rounded-full blur-sm animate-pulse" style={{ animationDelay: '1.2s' }} />
          <div className="absolute top-1/3 left-1/2 w-2 h-2 bg-orange-500 rounded-full blur-sm animate-pulse" style={{ animationDelay: '2s' }} />
          <div className="absolute bottom-10 right-1/4 w-1 h-1 bg-orange-400 rounded-full blur-sm" />
        </div>

        <div className="max-w-5xl mx-auto text-center relative z-10">
          <h2 className="text-4xl md:text-5xl font-bold leading-tight">
            Train on data you can <span className="text-orange-500">trust</span>.
          </h2>
          <p className="mt-6 text-lg md:text-xl text-gray-400 max-w-2xl mx-auto">
            Verified provenance, audited licenses, and end-to-end transparency for every dataset.
          </p>
        </div>
      </RevealSection>

      {/* CTA Section */}
      <RevealSection className="relative py-16 px-6 mb-20">
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h2 className="text-3xl md:text-4xl font-bold mb-8">
            Create an account today and join a{' '}
            <span className="text-orange-500">trustworthy ecosystem</span> designed for
            transparency and <span className="text-orange-500">control</span>.
          </h2>
        </div>

        {/* Holographic code windows background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {/* Left terminal window */}
          <div className="absolute bottom-4 left-12 w-48 h-56 border border-blue-900/30 rounded-xl bg-gradient-to-br from-orange-900/20 via-blue-900/10 to-transparent transform -rotate-12">
            <div className="p-3 space-y-1 opacity-60">
              <div className="h-1 bg-orange-400/70 w-3/4 rounded" />
              <div className="h-1 bg-orange-400/50 w-1/2 rounded" />
              <div className="h-1 bg-orange-400/60 w-2/3 rounded" />
              <div className="h-1 bg-orange-400/40 w-5/6 rounded" />
              <div className="h-1 bg-orange-400/70 w-1/3 rounded" />
              <div className="h-1 bg-orange-400/50 w-3/4 rounded" />
            </div>
          </div>

          {/* Center main code window */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 w-96 h-72 border border-blue-900/30 rounded-2xl bg-gradient-to-br from-orange-900/30 via-blue-900/20 to-transparent transform rotate-3 shadow-2xl shadow-orange-500/20">
            <div className="p-4 space-y-1.5 opacity-70 font-mono text-xs">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-orange-500/60" />
                <div className="h-1 bg-orange-400/70 w-32 rounded mt-1" />
              </div>
              <div className="h-1 bg-orange-400/50 w-48 rounded" />
              <div className="h-1 bg-orange-400/60 w-40 rounded" />
              <div className="h-1 bg-orange-400/40 w-56 rounded" />
              <div className="h-1 bg-orange-400/70 w-36 rounded" />
              <div className="h-1 bg-orange-400/50 w-44 rounded" />
              <div className="h-1 bg-orange-400/60 w-52 rounded" />
            </div>
            {/* Chat bubble icon */}
            <div className="absolute bottom-4 right-4 w-10 h-10 border border-blue-900/30 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
          </div>

          {/* Right small window with chart */}
          <div className="absolute bottom-8 right-16 w-44 h-48 border border-blue-900/30 rounded-xl bg-gradient-to-tl from-orange-900/20 via-blue-900/10 to-transparent transform rotate-6">
            <div className="p-3 space-y-2 opacity-60">
              {/* Simulated bar chart */}
              <div className="flex items-end gap-1 h-24">
                <div className="w-3 bg-orange-500/60 h-12 rounded-t" />
                <div className="w-3 bg-orange-500/70 h-20 rounded-t" />
                <div className="w-3 bg-orange-500/50 h-16 rounded-t" />
                <div className="w-3 bg-orange-500/80 h-24 rounded-t" />
                <div className="w-3 bg-orange-500/60 h-14 rounded-t" />
              </div>
            </div>
          </div>

          {/* Floating particles */}
          <div className="absolute bottom-32 left-1/4 w-1 h-1 bg-orange-500 rounded-full blur-sm animate-pulse" />
          <div className="absolute bottom-48 right-1/3 w-1.5 h-1.5 bg-orange-400 rounded-full blur-sm" />
          <div className="absolute bottom-20 left-1/3 w-1 h-1 bg-orange-500 rounded-full blur-sm animate-pulse" />
        </div>
      </RevealSection>

      {/* Features Section */}
      <section className="relative py-20 px-6 mt-16">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { icon: Camera, title: 'Register Your Work' },
              { icon: FileCheck, title: 'Define Licensing Rules' },
              { icon: Search, title: 'Verify Datasets' },
              { icon: FileText, title: 'Generate Audit Reports' },
            ].map(({ icon: Icon, title }) => (
              <Link key={title} to="/login" className="text-center group cursor-pointer">
                <div className="mb-4 flex justify-center">
                  <div className="relative">
                    <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-orange-600/30 to-orange-800/20 border border-blue-900/30 flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg shadow-orange-500/20">
                      <Icon className="w-10 h-10 text-orange-400" strokeWidth={1.5} />
                    </div>
                    <div className="absolute inset-0 bg-orange-500/30 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </div>
                <h3 className="text-white font-medium text-sm">{title}</h3>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-blue-900/30 py-8 px-6 mt-20 relative z-10">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-sm text-gray-500">© 2026 ArtLock.</p>
        </div>
      </footer>
    </div>
  )
}

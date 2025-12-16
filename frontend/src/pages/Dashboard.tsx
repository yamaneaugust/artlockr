import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Shield, Upload, Image, AlertTriangle, CheckCircle2, TrendingUp } from 'lucide-react'
import { api } from '../services/api'
import toast from 'react-hot-toast'

interface ArtworkStats {
  total_artworks: number
  scans_performed: number
  matches_found: number
  protected_artworks: number
}

interface RecentMatch {
  id: string
  artwork_title: string
  similarity: number
  detected_at: string
  ai_image_source: string
}

export default function Dashboard() {
  const [stats, setStats] = useState<ArtworkStats>({
    total_artworks: 0,
    scans_performed: 0,
    matches_found: 0,
    protected_artworks: 0,
  })
  const [recentMatches, setRecentMatches] = useState<RecentMatch[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      // TODO: Replace with actual API calls when backend endpoints are ready
      // Simulating data for now
      setTimeout(() => {
        setStats({
          total_artworks: 12,
          scans_performed: 45,
          matches_found: 3,
          protected_artworks: 12,
        })
        setRecentMatches([
          {
            id: '1',
            artwork_title: 'Sunset Landscape',
            similarity: 0.94,
            detected_at: new Date().toISOString(),
            ai_image_source: 'MidJourney Gallery',
          },
          {
            id: '2',
            artwork_title: 'Abstract Portrait',
            similarity: 0.87,
            detected_at: new Date().toISOString(),
            ai_image_source: 'Stable Diffusion Community',
          },
        ])
        setLoading(false)
      }, 1000)
    } catch (error) {
      toast.error('Failed to load dashboard data')
      setLoading(false)
    }
  }

  const statCards = [
    {
      name: 'Total Artworks',
      value: stats.total_artworks,
      icon: Image,
      color: 'bg-blue-500',
      change: '+2 this month',
    },
    {
      name: 'Scans Performed',
      value: stats.scans_performed,
      icon: Shield,
      color: 'bg-green-500',
      change: '+12 this week',
    },
    {
      name: 'Matches Found',
      value: stats.matches_found,
      icon: AlertTriangle,
      color: 'bg-yellow-500',
      change: stats.matches_found > 0 ? 'Action required' : 'All clear',
    },
    {
      name: 'Protected Works',
      value: stats.protected_artworks,
      icon: CheckCircle2,
      color: 'bg-primary-500',
      change: '100% coverage',
    },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Monitor your artwork protection and copyright detection status
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.name} className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <p className="mt-2 text-3xl font-bold text-gray-900">{stat.value}</p>
                  <p className="mt-2 text-sm text-gray-500">{stat.change}</p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon className="h-6 w-6 text-white" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/upload"
            className="flex items-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors"
          >
            <Upload className="h-8 w-8 text-primary-600 mr-3" />
            <div>
              <p className="font-medium text-gray-900">Upload Artwork</p>
              <p className="text-sm text-gray-600">Protect new artwork</p>
            </div>
          </Link>

          <Link
            to="/results"
            className="flex items-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors"
          >
            <Shield className="h-8 w-8 text-primary-600 mr-3" />
            <div>
              <p className="font-medium text-gray-900">View Results</p>
              <p className="text-sm text-gray-600">Check detection results</p>
            </div>
          </Link>

          <Link
            to="/privacy"
            className="flex items-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors"
          >
            <TrendingUp className="h-8 w-8 text-primary-600 mr-3" />
            <div>
              <p className="font-medium text-gray-900">Privacy Settings</p>
              <p className="text-sm text-gray-600">Manage your data</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Matches */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Copyright Matches</h2>
        {recentMatches.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-green-500" />
            <p>No copyright matches detected</p>
            <p className="text-sm mt-1">Your artwork is protected</p>
          </div>
        ) : (
          <div className="space-y-4">
            {recentMatches.map((match) => (
              <div
                key={match.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <AlertTriangle className="h-6 w-6 text-yellow-500" />
                  <div>
                    <p className="font-medium text-gray-900">{match.artwork_title}</p>
                    <p className="text-sm text-gray-600">{match.ai_image_source}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-red-600">
                    {(match.similarity * 100).toFixed(1)}% match
                  </p>
                  <p className="text-sm text-gray-500">
                    {new Date(match.detected_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

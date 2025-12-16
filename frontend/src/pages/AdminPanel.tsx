import { useState, useEffect } from 'react'
import {
  Users,
  Shield,
  Database,
  TrendingUp,
  AlertTriangle,
  Activity,
  Ban,
  FileText,
} from 'lucide-react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { api } from '../services/api'
import toast from 'react-hot-toast'

interface SystemStats {
  total_users: number
  total_artworks: number
  total_scans: number
  blocked_organizations: number
  faiss_index_size: number
  avg_scan_time_ms: number
}

interface SecurityEvent {
  id: string
  type: string
  severity: 'low' | 'medium' | 'high'
  ip_address: string
  timestamp: string
  description: string
}

export default function AdminPanel() {
  const [stats, setStats] = useState<SystemStats>({
    total_users: 0,
    total_artworks: 0,
    total_scans: 0,
    blocked_organizations: 0,
    faiss_index_size: 0,
    avg_scan_time_ms: 0,
  })
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([])
  const [loading, setLoading] = useState(true)

  // Mock data for charts
  const scanActivityData = [
    { date: 'Mon', scans: 45 },
    { date: 'Tue', scans: 52 },
    { date: 'Wed', scans: 61 },
    { date: 'Thu', scans: 58 },
    { date: 'Fri', scans: 73 },
    { date: 'Sat', scans: 38 },
    { date: 'Sun', scans: 42 },
  ]

  const detectionAccuracyData = [
    { name: 'True Positives', value: 87 },
    { name: 'True Negatives', value: 95 },
    { name: 'False Positives', value: 5 },
    { name: 'False Negatives', value: 3 },
  ]

  const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444']

  useEffect(() => {
    loadAdminData()
  }, [])

  const loadAdminData = async () => {
    try {
      // TODO: Replace with actual API calls
      setTimeout(() => {
        setStats({
          total_users: 234,
          total_artworks: 1847,
          total_scans: 5432,
          blocked_organizations: 12,
          faiss_index_size: 50000,
          avg_scan_time_ms: 4.2,
        })

        setSecurityEvents([
          {
            id: '1',
            type: 'Rate Limit Exceeded',
            severity: 'medium',
            ip_address: '192.168.1.100',
            timestamp: new Date().toISOString(),
            description: 'IP exceeded rate limit (120 requests/minute)',
          },
          {
            id: '2',
            type: 'Adversarial Attack Detected',
            severity: 'high',
            ip_address: '10.0.0.45',
            timestamp: new Date().toISOString(),
            description: 'Potential adversarial image upload detected',
          },
        ])

        setLoading(false)
      }, 1000)
    } catch (error) {
      toast.error('Failed to load admin data')
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading admin panel...</div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
        <p className="mt-2 text-gray-600">
          System monitoring, security analytics, and compliance dashboard
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Users</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">{stats.total_users}</p>
            </div>
            <Users className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Protected Artworks</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">{stats.total_artworks}</p>
            </div>
            <Shield className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Scans</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">{stats.total_scans}</p>
            </div>
            <Activity className="h-8 w-8 text-primary-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Blocked Organizations</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">{stats.blocked_organizations}</p>
            </div>
            <Ban className="h-8 w-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scan Activity */}
        <div className="card">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Scan Activity (Last 7 Days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={scanActivityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="scans" stroke="#0ea5e9" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Detection Accuracy */}
        <div className="card">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Detection Accuracy</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={detectionAccuracyData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {detectionAccuracyData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* System Performance */}
      <div className="card">
        <h3 className="text-lg font-bold text-gray-900 mb-4">System Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-600">FAISS Index Size</p>
              <Database className="h-5 w-5 text-gray-400" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{stats.faiss_index_size.toLocaleString()}</p>
            <p className="text-sm text-gray-600 mt-1">vectors indexed</p>
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-600">Avg Scan Time</p>
              <TrendingUp className="h-5 w-5 text-gray-400" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{stats.avg_scan_time_ms}ms</p>
            <p className="text-sm text-gray-600 mt-1">per detection</p>
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-600">System Accuracy</p>
              <Shield className="h-5 w-5 text-gray-400" />
            </div>
            <p className="text-2xl font-bold text-gray-900">~95%</p>
            <p className="text-sm text-gray-600 mt-1">multi-metric fusion</p>
          </div>
        </div>
      </div>

      {/* Security Events */}
      <div className="card">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Recent Security Events</h3>
        <div className="space-y-3">
          {securityEvents.map((event) => (
            <div
              key={event.id}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
            >
              <div className="flex items-center space-x-4">
                <AlertTriangle
                  className={`h-5 w-5 ${
                    event.severity === 'high'
                      ? 'text-red-500'
                      : event.severity === 'medium'
                      ? 'text-yellow-500'
                      : 'text-blue-500'
                  }`}
                />
                <div>
                  <p className="font-medium text-gray-900">{event.type}</p>
                  <p className="text-sm text-gray-600">{event.description}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    IP: {event.ip_address} | {new Date(event.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  event.severity === 'high'
                    ? 'bg-red-100 text-red-700'
                    : event.severity === 'medium'
                    ? 'bg-yellow-100 text-yellow-700'
                    : 'bg-blue-100 text-blue-700'
                }`}
              >
                {event.severity}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Admin Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="flex items-center p-4 border-2 border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors">
            <FileText className="h-6 w-6 text-primary-600 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Export Reports</p>
              <p className="text-sm text-gray-600">Generate system reports</p>
            </div>
          </button>

          <button className="flex items-center p-4 border-2 border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors">
            <Shield className="h-6 w-6 text-primary-600 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Security Settings</p>
              <p className="text-sm text-gray-600">Configure security rules</p>
            </div>
          </button>

          <button className="flex items-center p-4 border-2 border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors">
            <Database className="h-6 w-6 text-primary-600 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Rebuild Index</p>
              <p className="text-sm text-gray-600">Rebuild FAISS index</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  )
}

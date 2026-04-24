import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Search, Upload, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { detectCopyright } from '../services/sync'

type ResultStatus = 'clean' | 'match_found' | 'uncertain'

interface DetectionResult {
  status: ResultStatus
  confidence: number
  matches: { source: string; url: string; similarity: number }[]
  message: string
}

export default function Detect() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<DetectionResult | null>(null)

  const onDrop = useCallback((accepted: File[]) => {
    if (!accepted[0]) return
    setFile(accepted[0])
    setResult(null)
    if (accepted[0].type.startsWith('image/')) {
      const url = URL.createObjectURL(accepted[0])
      setPreview(url)
    } else {
      setPreview(null)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: { 'image/*': [], 'audio/*': [], 'video/*': [] },
  })

  // Resize image via canvas to reduce request size (perceptual hashing works well on smaller images)
  const resizeImage = (file: File, maxSize = 512): Promise<string> => {
    return new Promise((resolve, reject) => {
      const img = new window.Image()
      img.onload = () => {
        const canvas = document.createElement('canvas')
        let { width, height } = img
        if (width > height && width > maxSize) {
          height = (height * maxSize) / width
          width = maxSize
        } else if (height > maxSize) {
          width = (width * maxSize) / height
          height = maxSize
        }
        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')
        if (!ctx) {
          reject(new Error('Canvas context unavailable'))
          return
        }
        ctx.drawImage(img, 0, 0, width, height)
        resolve(canvas.toDataURL('image/jpeg', 0.85))
      }
      img.onerror = () => reject(new Error('Image load failed'))
      img.src = URL.createObjectURL(file)
    })
  }

  const handleDetect = async () => {
    if (!file) return
    setLoading(true)
    try {
      // Resize image to keep request small and fast
      const imageData = file.type.startsWith('image/')
        ? await resizeImage(file)
        : await new Promise<string>((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = () => resolve(reader.result as string)
            reader.onerror = reject
            reader.readAsDataURL(file)
          })

      // Call backend for perceptual hash-based similarity detection
      try {
        const data = await detectCopyright({
          image_data: imageData,
          filename: file.name,
          file_size: file.size,
          file_type: file.type,
        })

        setResult({
          status: data.status,
          confidence: data.confidence,
          matches: data.matches || [],
          message: data.message,
        })
        toast.success('Scan complete')
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : String(err)
        console.error('Backend detection failed:', err)
        toast.error(`Detection failed: ${errorMsg}`)
        setResult({
          status: 'uncertain',
          confidence: 0,
          matches: [],
          message: `Detection failed: ${errorMsg}. Check browser console for details.`,
        })
      }
    } catch (err) {
      console.error('Detection error:', err)
      toast.error('Failed to scan file')
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setFile(null)
    setPreview(null)
    setResult(null)
  }

  return (
    <div className="min-h-screen bg-blue-950 p-6">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Search className="w-8 h-8 text-orange-500" />
            Detect Copyright
          </h1>
          <p className="text-blue-300 mt-2">
            Artists: Upload your artwork to check if it has been used without your permission in AI training datasets. AI Companies: Upload compressed samples from your training data to verify proper licensing and avoid copyright issues.
          </p>
        </div>

        {!result ? (
          <div className="space-y-6">
            {/* Dropzone */}
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
                isDragActive
                  ? 'border-blue-900/30 bg-orange-500/10'
                  : file
                  ? 'border-green-400 bg-green-400/10'
                  : 'border-blue-900/30 bg-blue-900 hover:border-blue-900/30 hover:bg-orange-500/5'
              }`}
            >
              <input {...getInputProps()} />
              {preview ? (
                <div className="flex flex-col items-center gap-3">
                  <img src={preview} alt="Preview" className="max-h-48 rounded-lg object-contain" />
                  <p className="text-sm text-green-400 font-medium">{file?.name}</p>
                  <p className="text-xs text-blue-400">Click to replace</p>
                </div>
              ) : file ? (
                <div className="flex flex-col items-center gap-2">
                  <Upload className="h-10 w-10 text-green-400" />
                  <p className="text-sm font-medium text-green-400">{file.name}</p>
                  <p className="text-xs text-blue-400">Click to replace</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <Upload className="h-10 w-10 text-blue-400 mb-1" />
                  <p className="text-sm font-medium text-white">
                    {isDragActive ? 'Drop your file here' : 'Drop your artwork here or click to browse'}
                  </p>
                  <p className="text-xs text-blue-400">Supports images, audio, and video</p>
                </div>
              )}
            </div>

            <button
              onClick={handleDetect}
              disabled={!file || loading}
              className="w-full py-3 bg-orange-500 hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Scanning…
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Scan for Copyright Violations
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Result card */}
            <div className={`rounded-xl border-2 p-6 ${
              result.status === 'clean'
                ? 'border-green-500 bg-green-500/10'
                : result.status === 'match_found'
                ? 'border-red-500 bg-red-500/10'
                : 'border-yellow-500 bg-yellow-500/10'
            }`}>
              <div className="flex items-center gap-3 mb-3">
                {result.status === 'clean' ? (
                  <CheckCircle className="w-8 h-8 text-green-500" />
                ) : result.status === 'match_found' ? (
                  <AlertTriangle className="w-8 h-8 text-red-500" />
                ) : (
                  <AlertTriangle className="w-8 h-8 text-yellow-500" />
                )}
                <div>
                  <h2 className="text-xl font-bold text-white">
                    {result.status === 'clean'
                      ? 'No Violations Found'
                      : result.status === 'match_found'
                      ? 'Potential Match Detected'
                      : 'Uncertain Result'}
                  </h2>
                  <p className="text-sm text-blue-300">
                    Confidence: {(result.confidence * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
              <p className="text-blue-200">{result.message}</p>
            </div>

            {/* Matches */}
            {result.matches.length > 0 && (
              <div className="bg-blue-900 rounded-xl border border-blue-900/30 p-5">
                <h3 className="text-white font-bold mb-3">Matches Found</h3>
                <div className="space-y-3">
                  {result.matches.map((m, i) => (
                    <div key={i} className="bg-blue-950 rounded-lg overflow-hidden">
                      <div className="flex items-center justify-between p-4">
                        <div className="flex-1">
                          <p className="text-white font-medium">{m.source}</p>
                          {m.url && m.url !== '#' ? (
                            <a
                              href={m.url}
                              className="text-xs text-orange-400 hover:text-orange-300 hover:underline inline-flex items-center gap-1 mt-1"
                            >
                              View listing →
                            </a>
                          ) : (
                            <p className="text-xs text-blue-500 mt-1">Registered work (not listed for sale)</p>
                          )}
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          <span className="text-lg font-bold text-red-400">
                            {(m.similarity * 100).toFixed(0)}% match
                          </span>
                          <span className="text-xs text-blue-400">
                            {m.similarity >= 0.9 ? 'Exact match' : m.similarity >= 0.8 ? 'Very similar' : 'Similar'}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={reset}
              className="w-full py-3 bg-blue-900 hover:bg-blue-800 border border-blue-900/30 text-white font-medium rounded-xl transition-colors"
            >
              Scan Another File
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

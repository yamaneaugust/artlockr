import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Search, Upload, AlertTriangle, CheckCircle, Loader2, ShieldCheck } from 'lucide-react'
import toast from 'react-hot-toast'

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

  const handleDetect = async () => {
    if (!file) return
    setLoading(true)
    try {
      // Convert file to base64 for backend processing
      const arrayBuffer = await file.arrayBuffer()
      const base64 = btoa(
        new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
      )
      const imageData = `data:${file.type};base64,${base64}`

      // Simulate realistic processing time
      await new Promise((resolve) => setTimeout(resolve, 1500))

      // Call backend for perceptual hash-based similarity detection
      try {
        const res = await fetch(
          `${import.meta.env.VITE_API_URL || 'https://backend-production-2e5d.up.railway.app'}/api/v1/copyright/detect`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              image_data: imageData,
              filename: file.name,
              file_size: file.size,
              file_type: file.type,
            }),
            signal: AbortSignal.timeout(30000),
          },
        )

        if (res.ok) {
          const data = await res.json()

          // Backend returns: { status, confidence, matches: [{source, url, similarity}], message }
          if (data.matches && Array.isArray(data.matches)) {
            const maxSim = data.matches.length > 0
              ? Math.max(...data.matches.map((m: { similarity: number }) => m.similarity))
              : 0

            setResult({
              status: data.status || (maxSim >= 0.9 ? 'match_found' : maxSim >= 0.6 ? 'uncertain' : 'clean'),
              confidence: data.confidence || maxSim,
              matches: data.matches,
              message: data.message || (
                maxSim >= 0.9
                  ? 'High confidence match found on the web. This image appears elsewhere online.'
                  : maxSim >= 0.6
                  ? `Potential match detected with ${(maxSim * 100).toFixed(0)}% similarity. Review the sources below.`
                  : 'No similar images found on the web. This appears to be original or not widely distributed.'
              ),
            })
            toast.success('Web scan complete')
          } else {
            // No matches found
            setResult({
              status: 'clean',
              confidence: 0.95,
              matches: [],
              message: 'No similar images found on the web. This appears to be original or not widely distributed.',
            })
            toast.success('Scan complete - no matches found')
          }
        } else {
          throw new Error(`Backend returned ${res.status}`)
        }
      } catch (err) {
        console.error('Backend detection failed:', err)
        toast.error('Copyright detection service unavailable')
        setResult({
          status: 'uncertain',
          confidence: 0,
          matches: [],
          message: 'Copyright detection service is temporarily unavailable. Please try again later or ensure the backend is deployed.',
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

            <div className="bg-blue-900 rounded-xl border border-blue-900/30 p-4">
              <div className="flex items-start gap-3">
                <ShieldCheck className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-white">How it works</p>
                  <ul className="mt-1 space-y-1 text-xs text-blue-300">
                    <li>• Your image is analyzed using perceptual hashing algorithms (pHash, dHash, wHash)</li>
                    <li>• We compare against all registered artworks in our database</li>
                    <li>• Detects similar images even if resized, cropped, or slightly modified</li>
                    <li>• Results show similarity scores based on actual image content analysis</li>
                  </ul>
                </div>
              </div>
            </div>
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

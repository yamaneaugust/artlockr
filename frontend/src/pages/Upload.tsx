import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload as UploadIcon, X, CheckCircle2, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import toast from 'react-hot-toast'

const ART_STYLES = [
  { value: 'photorealistic', label: 'Photorealistic', threshold: 0.90 },
  { value: 'digital_art', label: 'Digital Art', threshold: 0.85 },
  { value: 'painting', label: 'Traditional Painting', threshold: 0.85 },
  { value: 'illustration', label: 'Illustration', threshold: 0.82 },
  { value: 'sketch', label: 'Sketch/Line Art', threshold: 0.78 },
  { value: 'abstract', label: 'Abstract', threshold: 0.75 },
  { value: 'pixel_art', label: 'Pixel Art', threshold: 0.88 },
  { value: 'general', label: 'General (Auto)', threshold: 0.80 },
]

const COMPLEXITY_LEVELS = [
  { value: 'simple', label: 'Simple', description: 'Minimal details, basic shapes' },
  { value: 'medium', label: 'Medium', description: 'Moderate detail and complexity' },
  { value: 'complex', label: 'Complex', description: 'Highly detailed, intricate' },
]

export default function Upload() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [artStyle, setArtStyle] = useState('general')
  const [complexity, setComplexity] = useState('medium')
  const [uploading, setUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file) {
      setSelectedFile(file)
      setUploadSuccess(false)

      // Create preview
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreview(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  })

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first')
      return
    }

    setUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('art_style', artStyle)
      formData.append('complexity', complexity)

      await api.uploadArtwork(formData)

      toast.success('Artwork uploaded successfully! Features extracted and stored securely.')
      setUploadSuccess(true)

      // Reset form after 2 seconds
      setTimeout(() => {
        setSelectedFile(null)
        setPreview(null)
        setUploadSuccess(false)
        setArtStyle('general')
        setComplexity('medium')
      }, 2000)
    } catch (error) {
      toast.error('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const removeFile = () => {
    setSelectedFile(null)
    setPreview(null)
    setUploadSuccess(false)
  }

  const selectedStyleInfo = ART_STYLES.find((s) => s.value === artStyle)

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Upload Artwork</h1>
        <p className="mt-2 text-gray-600">
          Upload your original artwork to protect it with AI-powered copyright detection
        </p>
      </div>

      {/* Privacy Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <CheckCircle2 className="h-5 w-5 text-blue-600 mr-3 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-900">
            <p className="font-medium mb-1">Privacy-First Storage</p>
            <p>
              Your image is processed immediately to extract 2048-dimensional features, then
              permanently deleted. Only mathematical features are stored - never the original image.
              You retain full ownership and can delete your data at any time.
            </p>
          </div>
        </div>
      </div>

      {/* Upload Area */}
      <div className="card">
        {!selectedFile ? (
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
            }`}
          >
            <input {...getInputProps()} />
            <UploadIcon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium text-gray-900 mb-2">
              {isDragActive ? 'Drop your artwork here' : 'Drag & drop your artwork'}
            </p>
            <p className="text-sm text-gray-600">
              or click to browse (PNG, JPG, GIF, WebP up to 10MB)
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Preview */}
            <div className="relative">
              <img
                src={preview!}
                alt="Preview"
                className="w-full h-96 object-contain rounded-lg bg-gray-100"
              />
              <button
                onClick={removeFile}
                className="absolute top-2 right-2 p-2 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* File Info */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-sm text-gray-600">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              {uploadSuccess && (
                <CheckCircle2 className="h-6 w-6 text-green-500" />
              )}
            </div>
          </div>
        )}
      </div>

      {/* Configuration */}
      {selectedFile && !uploadSuccess && (
        <div className="card space-y-6">
          <h2 className="text-xl font-bold text-gray-900">Artwork Configuration</h2>

          {/* Art Style */}
          <div>
            <label className="label">Art Style</label>
            <select
              value={artStyle}
              onChange={(e) => setArtStyle(e.target.value)}
              className="input"
            >
              {ART_STYLES.map((style) => (
                <option key={style.value} value={style.value}>
                  {style.label} (Threshold: {(style.threshold * 100).toFixed(0)}%)
                </option>
              ))}
            </select>
            <p className="mt-2 text-sm text-gray-600">
              Detection threshold: {((selectedStyleInfo?.threshold || 0.8) * 100).toFixed(0)}%
              similarity required for a match
            </p>
          </div>

          {/* Complexity */}
          <div>
            <label className="label">Artwork Complexity</label>
            <div className="grid grid-cols-3 gap-4">
              {COMPLEXITY_LEVELS.map((level) => (
                <button
                  key={level.value}
                  onClick={() => setComplexity(level.value)}
                  className={`p-4 border-2 rounded-lg text-left transition-colors ${
                    complexity === level.value
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <p className="font-medium text-gray-900">{level.label}</p>
                  <p className="text-sm text-gray-600 mt-1">{level.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="btn-primary w-full py-3 text-lg"
          >
            {uploading ? 'Uploading and Processing...' : 'Upload & Protect Artwork'}
          </button>
        </div>
      )}

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="font-medium text-gray-900 mb-2">Feature Extraction</h3>
          <p className="text-sm text-gray-600">
            ResNet deep learning model extracts 2048 unique features from your artwork
          </p>
        </div>
        <div className="card">
          <h3 className="font-medium text-gray-900 mb-2">Instant Deletion</h3>
          <p className="text-sm text-gray-600">
            Original image deleted immediately after processing - only features stored
          </p>
        </div>
        <div className="card">
          <h3 className="font-medium text-gray-900 mb-2">Cryptographic Proof</h3>
          <p className="text-sm text-gray-600">
            SHA-256 hash proof generated to verify your ownership timestamp
          </p>
        </div>
      </div>
    </div>
  )
}

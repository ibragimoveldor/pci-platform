import { useCallback, useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDropzone } from 'react-dropzone'
import { projectsApi, imagesApi, analysisApi, Project, Image, AnalysisStatus } from '../api/client'
import { ArrowLeft, Upload, Play, X, Loader2, CheckCircle, AlertCircle, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const projectId = parseInt(id!)

  // Fetch project
  const { data: project, isLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId).then(r => r.data),
  })

  // Fetch images
  const { data: images = [] } = useQuery({
    queryKey: ['images', projectId],
    queryFn: () => imagesApi.list(projectId).then(r => r.data),
  })

  // Analysis status polling
  const [isPolling, setIsPolling] = useState(false)
  const { data: analysisStatus } = useQuery({
    queryKey: ['analysis-status', projectId],
    queryFn: () => analysisApi.status(projectId).then(r => r.data),
    refetchInterval: isPolling ? 2000 : false,
  })

  useEffect(() => {
    if (project?.status === 2 || project?.status === 3) {
      setIsPolling(true)
    } else {
      setIsPolling(false)
    }
  }, [project?.status])

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (files: File[]) => imagesApi.upload(projectId, files),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['images', projectId] })
      toast.success(`Uploaded ${data.data.uploaded} images`)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Upload failed')
    },
  })

  // Start analysis mutation
  const startAnalysisMutation = useMutation({
    mutationFn: () => analysisApi.start(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      setIsPolling(true)
      toast.success('Analysis started')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to start analysis')
    },
  })

  // Dropzone
  const onDrop = useCallback((acceptedFiles: File[]) => {
    uploadMutation.mutate(acceptedFiles)
  }, [uploadMutation])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.tiff'] },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin" size={32} />
      </div>
    )
  }

  if (!project) {
    return <div className="p-8">Project not found</div>
  }

  const canStartAnalysis = project.status === 1 || project.status === 5 || project.status === 6
  const isProcessing = project.status === 2 || project.status === 3

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <button onClick={() => navigate('/projects')} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1 className="text-2xl font-bold">{project.name}</h1>
          <p className="text-gray-600">{project.description || 'No description'}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Images */}
        <div className="lg:col-span-2">
          {/* Upload zone */}
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors mb-6 ${
              isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="mx-auto mb-2 text-gray-400" size={32} />
            {uploadMutation.isPending ? (
              <p>Uploading...</p>
            ) : isDragActive ? (
              <p>Drop images here...</p>
            ) : (
              <p>Drag & drop images here, or click to select</p>
            )}
          </div>

          {/* Images grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {images.map((image: Image) => (
              <div key={image.id} className="relative group">
                <img
                  src={image.url}
                  alt={image.original_filename}
                  className="w-full h-32 object-cover rounded-lg"
                />
                <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-xs p-1 rounded-b-lg truncate">
                  {image.original_filename}
                </div>
                {image.processed && (
                  <CheckCircle className="absolute top-2 right-2 text-green-500" size={16} />
                )}
              </div>
            ))}
          </div>

          {images.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No images uploaded yet
            </div>
          )}
        </div>

        {/* Right: Analysis panel */}
        <div>
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">Analysis</h2>

            {/* Status */}
            <div className="mb-4">
              <span className="text-sm text-gray-600">Status: </span>
              <span className={`font-medium ${
                project.status === 4 ? 'text-green-600' :
                project.status === 5 ? 'text-red-600' :
                isProcessing ? 'text-yellow-600' : 'text-gray-600'
              }`}>
                {project.status_name}
              </span>
            </div>

            {/* Progress */}
            {isProcessing && analysisStatus && (
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-1">
                  <span>{analysisStatus.message}</span>
                  <span>{analysisStatus.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all"
                    style={{ width: `${analysisStatus.progress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Start button */}
            {canStartAnalysis && (
              <button
                onClick={() => startAnalysisMutation.mutate()}
                disabled={startAnalysisMutation.isPending || project.image_count === 0}
                className="w-full flex items-center justify-center gap-2 bg-primary-600 text-white py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                <Play size={18} />
                Start Analysis
              </button>
            )}

            {project.image_count === 0 && (
              <p className="text-sm text-gray-500 mt-2">Upload images to start analysis</p>
            )}

            {/* Results */}
            {project.status === 4 && project.pci_score !== null && (
              <div className="mt-6">
                <h3 className="font-semibold mb-3">Results</h3>
                
                <div className="text-center p-4 bg-gray-50 rounded-lg mb-4">
                  <div className="text-4xl font-bold mb-1" style={{
                    color: project.pci_score >= 70 ? '#16a34a' :
                           project.pci_score >= 40 ? '#ca8a04' : '#dc2626'
                  }}>
                    {project.pci_score}
                  </div>
                  <div className="text-sm text-gray-600">PCI Score</div>
                  <div className="text-sm font-medium mt-1">
                    {project.results?.condition_rating as string}
                  </div>
                </div>

                {project.results && (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Defects</span>
                      <span>{project.results.total_defects as number}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Defect Area</span>
                      <span>{project.results.defect_area_percentage as number}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Processing Time</span>
                      <span>{project.results.processing_time_seconds as number}s</span>
                    </div>
                  </div>
                )}

                {project.results?.recommendations && (
                  <div className="mt-4">
                    <h4 className="font-medium mb-2">Recommendations</h4>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {(project.results.recommendations as string[]).map((rec, i) => (
                        <li key={i}>• {rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Error */}
            {project.status === 5 && project.processing_error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center gap-2 text-red-600 font-medium">
                  <AlertCircle size={16} />
                  Analysis Failed
                </div>
                <p className="text-sm text-red-600 mt-1">{project.processing_error}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

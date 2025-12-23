import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { applicationsApi } from '../services/api'
import { FileText, RefreshCw, Loader2, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

export default function PDFIngestion() {
  const queryClient = useQueryClient()

  const { data: statusData, isLoading } = useQuery({
    queryKey: ['ingestion-status'],
    queryFn: () => applicationsApi.ingestionStatus(),
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  const ingestMutation = useMutation({
    mutationFn: (force: boolean) => applicationsApi.ingestPdfs(force),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ingestion-status'] })
      queryClient.invalidateQueries({ queryKey: ['applications'] })
    },
  })

  const status = statusData?.data

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="animate-spin" size={24} />
      </div>
    )
  }

  if (!status) return null

  const pendingCount = status.pending || 0
  const processedCount = status.processed || 0
  const totalCount = status.total_pdfs || 0

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">PDF Ingestion</h1>
        <div className="flex space-x-2">
          <button
            onClick={() => ingestMutation.mutate(false)}
            disabled={ingestMutation.isPending || pendingCount === 0}
            className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {ingestMutation.isPending ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <RefreshCw size={18} />
                <span>Ingest New PDFs</span>
              </>
            )}
          </button>
          <button
            onClick={() => ingestMutation.mutate(true)}
            disabled={ingestMutation.isPending || totalCount === 0}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw size={18} />
            <span>Reprocess All</span>
          </button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-6 rounded-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total PDFs</p>
              <p className="text-3xl font-bold text-gray-900">{totalCount}</p>
            </div>
            <FileText className="text-gray-400" size={40} />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Processed</p>
              <p className="text-3xl font-bold text-green-600">{processedCount}</p>
            </div>
            <CheckCircle className="text-green-400" size={40} />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Pending</p>
              <p className="text-3xl font-bold text-yellow-600">{pendingCount}</p>
            </div>
            <AlertCircle className="text-yellow-400" size={40} />
          </div>
        </div>
      </div>

      {/* Configuration Status */}
      <div className="bg-white rounded-lg border p-4 mb-6">
        <div className="flex items-center space-x-2">
          {status.pdf_parser_available ? (
            <>
              <CheckCircle className="text-green-600" size={20} />
              <span className="text-sm text-green-600">PDF Parser Configured ({status.ai_provider?.toUpperCase() || 'Gemini'})</span>
            </>
          ) : (
            <>
              <XCircle className="text-red-600" size={20} />
              <span className="text-sm text-red-600">PDF Parser Not Configured - Add API Key</span>
            </>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-1">PDFs Directory: {status.pdfs_directory}</p>
      </div>

      {/* PDF Files List */}
      <div className="bg-white rounded-lg border">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">PDF Files</h2>
        </div>
        {status.files && status.files.length > 0 ? (
          <div className="divide-y">
            {status.files.map((file: any, index: number) => (
              <div key={index} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex items-center space-x-3">
                  <FileText className={file.processed ? "text-green-600" : "text-gray-400"} size={24} />
                  <div>
                    <p className="font-medium text-gray-900">{file.filename}</p>
                    <p className="text-sm text-gray-500">{file.size_kb.toFixed(1)} KB</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {file.processed ? (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                      <CheckCircle size={14} className="mr-1" />
                      Processed
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                      <AlertCircle size={14} className="mr-1" />
                      Pending
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-6 py-12 text-center text-gray-500">
            <FileText className="mx-auto mb-4 text-gray-400" size={48} />
            <p>No PDF files found in the pdfs directory</p>
            <p className="text-sm mt-2">Add PDF files to: {status.pdfs_directory}</p>
          </div>
        )}
      </div>

      {/* Ingestion Result */}
      {ingestMutation.isSuccess && ingestMutation.data && (
        <div className="mt-6 bg-white rounded-lg border p-4">
          <h3 className="font-semibold mb-2">Ingestion Result</h3>
          <div className="space-y-1 text-sm">
            <p>✓ Processed: {ingestMutation.data.data.processed}</p>
            <p>− Skipped: {ingestMutation.data.data.skipped}</p>
            {ingestMutation.data.data.errors > 0 && (
              <p className="text-red-600">✗ Errors: {ingestMutation.data.data.errors}</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { applicationsApi } from '../services/api'
import { Plus, AlertCircle, RefreshCw, Loader2 } from 'lucide-react'

export default function Applications() {
  const { data, isLoading, error, refetch, isRefetching } = useQuery({
    queryKey: ['applications'],
    queryFn: () => applicationsApi.list(1, 100), // Fetch up to 100 applications
    refetchOnWindowFocus: true, // Refetch when window regains focus
    staleTime: 30000, // Consider data stale after 30 seconds
  })

  const applications = data?.data?.applications || []
  const total = data?.data?.total || 0

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Applications</h1>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <AlertCircle className="text-red-500 flex-shrink-0" size={24} />
            <div>
              <h3 className="font-semibold text-red-800">Failed to Load Applications</h3>
              <p className="text-sm text-red-600 mt-1">
                {(error as any)?.message || 'Unable to connect to the server. Please check if the backend is running.'}
              </p>
              <button
                onClick={() => refetch()}
                className="mt-3 flex items-center space-x-2 px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200"
              >
                <RefreshCw size={16} />
                <span>Try Again</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Applications</h1>
            {!isLoading && total > 0 && (
              <p className="text-sm text-gray-500 mt-1">Showing {applications.length} of {total} applications</p>
            )}
          </div>
          {isRefetching && <Loader2 className="animate-spin text-gray-400" size={20} />}
        </div>
        <Link to="/applications/new"
          className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
          <Plus size={20} />
          <span>New Application</span>
        </Link>
      </div>

      {isLoading ? (
        <div className="text-center py-12">Loading...</div>
      ) : applications.length === 0 ? (
        <div className="bg-white rounded-lg border p-12 text-center">
          <p className="text-gray-500">No applications yet</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reference ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Business</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {applications.map((app: any) => (
                <tr key={app.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <Link to={`/applications/${app.id}`} className="text-indigo-600 hover:underline">
                      {app.reference_id}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">{app.business_name || 'N/A'}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    ${app.requested_amount?.toLocaleString() || 'N/A'}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      app.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                      app.status === 'PROCESSING' ? 'bg-blue-100 text-blue-800' :
                      app.status === 'SUBMITTED' ? 'bg-purple-100 text-purple-800' :
                      app.status === 'DRAFT' ? 'bg-yellow-100 text-yellow-800' :
                      app.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                      app.status === 'ERROR' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {app.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(app.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { lendersApi } from '../services/api'
import { Building2, ChevronRight, FileText } from 'lucide-react'

export default function Lenders() {
  const { data, isLoading } = useQuery({
    queryKey: ['lenders'],
    queryFn: () => lendersApi.list(1, 50),
  })

  const lenders = data?.data?.lenders || []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Lenders</h1>
          <p className="mt-1 text-gray-600">Manage lender policies and criteria</p>
        </div>
        <Link
          to="/pdf-ingestion"
          className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          <FileText size={20} />
          <span>Import from PDF</span>
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow-sm border">
        {lenders.length === 0 ? (
          <div className="p-12 text-center">
            <Building2 className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">No lenders configured</h3>
            <p className="mt-2 text-gray-500">Import lender policies from PDF files to get started.</p>
            <Link
              to="/pdf-ingestion"
              className="mt-4 inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              <FileText size={20} className="mr-2" />
              Import from PDF
            </Link>
          </div>
        ) : (
          <div className="divide-y">
            {lenders.map((lender: any) => (
              <Link
                key={lender.id}
                to={`/lenders/${lender.id}`}
                className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                    <Building2 className="text-indigo-600" size={20} />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{lender.display_name}</h3>
                    <p className="text-sm text-gray-500">
                      {lender.program_count} program{lender.program_count !== 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    lender.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {lender.is_active ? 'Active' : 'Inactive'}
                  </span>
                  <ChevronRight className="text-gray-400" size={20} />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { applicationsApi, lendersApi } from '../services/api'
import { FileText, Building2, Plus, ArrowRight } from 'lucide-react'

export default function Dashboard() {
  const { data: applicationsData } = useQuery({
    queryKey: ['applications'],
    queryFn: () => applicationsApi.list(1, 5),
  })

  const { data: lendersData } = useQuery({
    queryKey: ['lenders'],
    queryFn: () => lendersApi.list(1, 5),
  })

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-gray-600">Loan underwriting and lender matching system</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link to="/applications/new"
          className="flex items-center justify-between p-6 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
          <div className="flex items-center space-x-3">
            <Plus size={24} />
            <span className="text-lg font-medium">New Application</span>
          </div>
          <ArrowRight size={20} />
        </Link>
        <Link to="/lenders"
          className="flex items-center justify-between p-6 bg-white border rounded-lg hover:border-indigo-300">
          <div className="flex items-center space-x-3">
            <Building2 size={24} className="text-indigo-600" />
            <span className="text-lg font-medium text-gray-900">Manage Lenders</span>
          </div>
          <ArrowRight size={20} className="text-gray-400" />
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Applications</p>
              <p className="text-2xl font-bold text-gray-900">
                {applicationsData?.data?.total || 0}
              </p>
            </div>
            <FileText className="text-indigo-600" size={32} />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Active Lenders</p>
              <p className="text-2xl font-bold text-gray-900">
                {lendersData?.data?.total || 0}
              </p>
            </div>
            <Building2 className="text-indigo-600" size={32} />
          </div>
        </div>
      </div>
    </div>
  )
}

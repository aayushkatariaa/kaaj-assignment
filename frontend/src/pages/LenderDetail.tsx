import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { lendersApi } from '../services/api'
import { ArrowLeft, Edit, Trash2, Plus, Check, X } from 'lucide-react'
import { useState } from 'react'
import type { Lender, LenderProgram, PolicyCriteria } from '../types'

export default function LenderDetail() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  const [editingCriteria, setEditingCriteria] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['lender', id],
    queryFn: () => lendersApi.get(Number(id)),
    enabled: !!id,
  })

  const deleteCriteriaMutation = useMutation({
    mutationFn: ({ programId, criteriaId }: { programId: number; criteriaId: number }) =>
      lendersApi.deleteCriteria(Number(id), programId, criteriaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lender', id] })
    },
  })

  const lender: Lender | undefined = data?.data

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  if (!lender) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Lender not found</p>
        <Link to="/lenders" className="text-indigo-600 hover:underline mt-2 inline-block">
          Back to Lenders
        </Link>
      </div>
    )
  }

  const getOperatorDisplay = (op: string) => {
    const operators: Record<string, string> = {
      gte: '≥',
      gt: '>',
      lte: '≤',
      lt: '<',
      eq: '=',
      neq: '≠',
      in: 'in',
      not_in: 'not in',
      between: 'between',
    }
    return operators[op] || op
  }

  const formatValue = (criteria: PolicyCriteria) => {
    if (criteria.list_values && criteria.list_values.length > 0) {
      return criteria.list_values.join(', ')
    }
    if (criteria.numeric_value_min !== null && criteria.numeric_value_max !== null) {
      return `${criteria.numeric_value_min} - ${criteria.numeric_value_max}`
    }
    if (criteria.numeric_value !== null && criteria.numeric_value !== undefined) {
      return criteria.numeric_value.toLocaleString()
    }
    if (criteria.numeric_value_min !== null && criteria.numeric_value_min !== undefined) {
      return criteria.numeric_value_min.toLocaleString()
    }
    if (criteria.numeric_value_max !== null && criteria.numeric_value_max !== undefined) {
      return criteria.numeric_value_max.toLocaleString()
    }
    return criteria.string_value || '-'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/lenders"
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{lender.display_name}</h1>
            <p className="text-gray-500">{lender.description}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-3 py-1 text-sm font-medium rounded-full ${
            lender.is_active 
              ? 'bg-green-100 text-green-800' 
              : 'bg-gray-100 text-gray-800'
          }`}>
            {lender.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>
      </div>

      {/* Lender Info */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Lender Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-500">Name</label>
            <p className="font-medium">{lender.name}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">Display Name</label>
            <p className="font-medium">{lender.display_name}</p>
          </div>
          {lender.website && (
            <div>
              <label className="text-sm text-gray-500">Website</label>
              <p className="font-medium">
                <a href={lender.website} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
                  {lender.website}
                </a>
              </p>
            </div>
          )}
          {lender.source_pdf_name && (
            <div>
              <label className="text-sm text-gray-500">Source PDF</label>
              <p className="font-medium">{lender.source_pdf_name}</p>
            </div>
          )}
        </div>
      </div>

      {/* Programs */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Programs & Criteria</h2>
          <button className="flex items-center space-x-2 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
            <Plus size={16} />
            <span>Add Program</span>
          </button>
        </div>

        {lender.programs.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
            <p className="text-gray-500">No programs configured for this lender.</p>
          </div>
        ) : (
          lender.programs.map((program: LenderProgram) => (
            <div key={program.id} className="bg-white rounded-lg shadow-sm border overflow-hidden">
              {/* Program Header */}
              <div className="p-4 bg-gray-50 border-b flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{program.name}</h3>
                  {program.description && (
                    <p className="text-sm text-gray-500 mt-1">{program.description}</p>
                  )}
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right text-sm">
                    <p className="text-gray-500">Loan Range</p>
                    <p className="font-medium">
                      ${program.min_loan_amount?.toLocaleString() || 0} - ${program.max_loan_amount?.toLocaleString() || '∞'}
                    </p>
                  </div>
                  <div className="text-right text-sm">
                    <p className="text-gray-500">Min FICO</p>
                    <p className="font-medium">{program.min_fico || '-'}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    program.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {program.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>

              {/* Criteria Table */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Criteria</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Operator</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Required</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Weight</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {program.criteria.map((criteria: PolicyCriteria) => (
                      <tr key={criteria.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div>
                            <p className="font-medium text-gray-900">{criteria.criteria_name}</p>
                            {criteria.description && (
                              <p className="text-xs text-gray-500">{criteria.description}</p>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">
                            {criteria.criteria_type}
                          </code>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className="font-mono">{getOperatorDisplay(criteria.operator)}</span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                          {formatValue(criteria)}
                        </td>
                        <td className="px-4 py-3">
                          {criteria.is_required ? (
                            <Check className="text-green-600" size={18} />
                          ) : (
                            <X className="text-gray-400" size={18} />
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {criteria.weight}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end space-x-2">
                            <button
                              className="p-1 hover:bg-gray-100 rounded"
                              onClick={() => setEditingCriteria(criteria.id)}
                            >
                              <Edit size={16} className="text-gray-400" />
                            </button>
                            <button
                              className="p-1 hover:bg-red-50 rounded"
                              onClick={() => {
                                if (confirm('Delete this criteria?')) {
                                  deleteCriteriaMutation.mutate({
                                    programId: program.id,
                                    criteriaId: criteria.id,
                                  })
                                }
                              }}
                            >
                              <Trash2 size={16} className="text-red-400" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Add Criteria Button */}
              <div className="p-3 bg-gray-50 border-t">
                <button className="flex items-center space-x-1 text-sm text-indigo-600 hover:text-indigo-800">
                  <Plus size={16} />
                  <span>Add Criteria</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

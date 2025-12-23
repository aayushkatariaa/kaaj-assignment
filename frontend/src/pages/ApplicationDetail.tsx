import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { applicationsApi, underwritingApi } from '../services/api'
import { CheckCircle, XCircle, AlertCircle, Play, Loader2, AlertTriangle } from 'lucide-react'
import type { UnderwritingResults, CriteriaEvaluation } from '../types'

// Helper to extract error message from API response
function getErrorMessage(error: any): string[] {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') {
    return [detail]
  }
  if (detail?.errors && Array.isArray(detail.errors)) {
    return detail.errors
  }
  if (detail?.message) {
    return [detail.message]
  }
  return [error.message || 'An unexpected error occurred']
}

export default function ApplicationDetail() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  const [submitErrors, setSubmitErrors] = useState<string[]>([])
  const [underwriteErrors, setUnderwriteErrors] = useState<string[]>([])

  const { data: appData, isLoading, error: loadError } = useQuery({
    queryKey: ['application', id],
    queryFn: () => applicationsApi.get(Number(id)),
  })

  const { data: resultsData } = useQuery({
    queryKey: ['underwriting-results', id],
    queryFn: () => underwritingApi.results(Number(id)),
    enabled: appData?.data?.status === 'COMPLETED',
  })

  const runMutation = useMutation({
    mutationFn: () => underwritingApi.run(Number(id)),
    onSuccess: () => {
      setUnderwriteErrors([])
      queryClient.invalidateQueries({ queryKey: ['application', id] })
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['underwriting-results', id] })
      }, 3000)
    },
    onError: (error: any) => {
      setUnderwriteErrors(getErrorMessage(error))
    }
  })

  const submitMutation = useMutation({
    mutationFn: () => applicationsApi.submit(Number(id)),
    onSuccess: () => {
      setSubmitErrors([])
      queryClient.invalidateQueries({ queryKey: ['application', id] })
    },
    onError: (error: any) => {
      setSubmitErrors(getErrorMessage(error))
    }
  })

  const app = appData?.data
  const results: UnderwritingResults = resultsData?.data

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="animate-spin mr-2" size={24} />
        <span>Loading application...</span>
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <XCircle className="mx-auto text-red-500 mb-2" size={48} />
        <h2 className="text-lg font-semibold text-red-800">Failed to Load Application</h2>
        <p className="text-red-600">{(loadError as any)?.message || 'Unknown error'}</p>
      </div>
    )
  }

  if (!app) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
        <AlertTriangle className="mx-auto text-yellow-500 mb-2" size={48} />
        <h2 className="text-lg font-semibold text-yellow-800">Application Not Found</h2>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{app.reference_id}</h1>
          <p className="text-gray-600">{app.business?.legal_name}</p>
        </div>
        <div className="flex space-x-2">
          {app.status === 'DRAFT' && (
            <button 
              onClick={() => submitMutation.mutate()}
              disabled={submitMutation.isPending}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 flex items-center space-x-2">
              {submitMutation.isPending ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  <span>Submitting...</span>
                </>
              ) : (
                <span>Submit Application</span>
              )}
            </button>
          )}
          {app.status === 'SUBMITTED' && (
            <button 
              onClick={() => runMutation.mutate()}
              disabled={runMutation.isPending}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50">
              {runMutation.isPending ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  <span>Running...</span>
                </>
              ) : (
                <>
                  <Play size={18} />
                  <span>Run Underwriting</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Validation Errors Display */}
      {submitErrors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="text-red-500 mt-0.5 flex-shrink-0" size={20} />
            <div>
              <h3 className="font-semibold text-red-800">Cannot Submit Application</h3>
              <p className="text-sm text-red-600 mb-2">Please fix the following issues:</p>
              <ul className="list-disc list-inside space-y-1">
                {submitErrors.map((err, idx) => (
                  <li key={idx} className="text-sm text-red-700">{err}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {underwriteErrors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="text-red-500 mt-0.5 flex-shrink-0" size={20} />
            <div>
              <h3 className="font-semibold text-red-800">Underwriting Failed</h3>
              <ul className="list-disc list-inside space-y-1">
                {underwriteErrors.map((err, idx) => (
                  <li key={idx} className="text-sm text-red-700">{err}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Missing Required Fields Warning for DRAFT */}
      {app.status === 'DRAFT' && (
        <div className="space-y-3">
          {/* Required fields check */}
          {(!app.guarantor?.fico_score || !app.business?.legal_name || !app.loan_request?.requested_amount) && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="text-yellow-500 mt-0.5 flex-shrink-0" size={20} />
                <div>
                  <h3 className="font-semibold text-yellow-800">Missing Required Information</h3>
                  <ul className="text-sm text-yellow-700 mt-1 list-disc list-inside">
                    {!app.guarantor?.fico_score && <li>FICO score is required</li>}
                    {!app.business?.legal_name && <li>Business name is required</li>}
                    {!app.loan_request?.requested_amount && <li>Loan amount is required</li>}
                  </ul>
                </div>
              </div>
            </div>
          )}
          
          {/* Eligibility warnings based on provided values */}
          {app.guarantor?.fico_score && (
            <div className={`border rounded-lg p-4 ${
              app.guarantor.fico_score < 680 
                ? 'bg-red-50 border-red-200' 
                : app.guarantor.fico_score < 720 
                  ? 'bg-yellow-50 border-yellow-200'
                  : 'bg-green-50 border-green-200'
            }`}>
              <div className="flex items-start space-x-3">
                {app.guarantor.fico_score < 680 ? (
                  <XCircle className="text-red-500 mt-0.5 flex-shrink-0" size={20} />
                ) : app.guarantor.fico_score < 720 ? (
                  <AlertTriangle className="text-yellow-500 mt-0.5 flex-shrink-0" size={20} />
                ) : (
                  <CheckCircle className="text-green-500 mt-0.5 flex-shrink-0" size={20} />
                )}
                <div>
                  <h3 className={`font-semibold ${
                    app.guarantor.fico_score < 680 
                      ? 'text-red-800' 
                      : app.guarantor.fico_score < 720 
                        ? 'text-yellow-800'
                        : 'text-green-800'
                  }`}>
                    FICO Score: {app.guarantor.fico_score}
                  </h3>
                  <p className={`text-sm ${
                    app.guarantor.fico_score < 680 
                      ? 'text-red-700' 
                      : app.guarantor.fico_score < 720 
                        ? 'text-yellow-700'
                        : 'text-green-700'
                  }`}>
                    {app.guarantor.fico_score < 680 
                      ? 'Likely ineligible for most programs. Minimum FICO of 680 is typically required.'
                      : app.guarantor.fico_score < 720 
                        ? 'May qualify for some programs with higher rates (Tier B/C).'
                        : 'Good credit score. Likely eligible for best rates (Tier A).'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Business time check */}
          {app.business?.months_in_business !== undefined && app.business.months_in_business < 12 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="text-yellow-500 mt-0.5 flex-shrink-0" size={20} />
                <div>
                  <h3 className="font-semibold text-yellow-800">
                    Time in Business: {app.business.months_in_business} months
                  </h3>
                  <p className="text-sm text-yellow-700">
                    Startup business. May only qualify for startup-specific programs with stricter requirements.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Bankruptcy check */}
          {app.guarantor?.has_bankruptcy && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <XCircle className="text-red-500 mt-0.5 flex-shrink-0" size={20} />
                <div>
                  <h3 className="font-semibold text-red-800">Bankruptcy History</h3>
                  <p className="text-sm text-red-700">
                    Bankruptcy on record may disqualify from many programs. Most lenders require 4+ years since discharge.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Ready to submit */}
          {app.guarantor?.fico_score && app.business?.legal_name && app.loan_request?.requested_amount && 
           app.guarantor.fico_score >= 680 && !app.guarantor.has_bankruptcy && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <CheckCircle className="text-green-500 mt-0.5 flex-shrink-0" size={20} />
                <div>
                  <h3 className="font-semibold text-green-800">Ready to Submit</h3>
                  <p className="text-sm text-green-700">
                    Application appears complete. Click "Submit Application" to run underwriting.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Failed Status Display */}
      {app.status === 'FAILED' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <XCircle className="text-red-500 mt-0.5 flex-shrink-0" size={20} />
            <div>
              <h3 className="font-semibold text-red-800">Underwriting Failed</h3>
              <p className="text-sm text-red-700">
                An error occurred during underwriting. Please try again or contact support.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border">
          <p className="text-sm text-gray-500">Status</p>
          <p className="text-lg font-semibold">{app.status}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <p className="text-sm text-gray-500">Requested Amount</p>
          <p className="text-lg font-semibold">${app.loan_request?.requested_amount?.toLocaleString()}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <p className="text-sm text-gray-500">FICO Score</p>
          <p className="text-lg font-semibold">{app.guarantor?.fico_score || 'N/A'}</p>
        </div>
      </div>

      {results && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">Matching Results</h2>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="text-center">
                <p className="text-3xl font-bold text-green-600">{results.eligible_lenders}</p>
                <p className="text-sm text-gray-500">Eligible</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-yellow-600">{results.needs_review_lenders}</p>
                <p className="text-sm text-gray-500">Needs Review</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-red-600">{results.ineligible_lenders}</p>
                <p className="text-sm text-gray-500">Ineligible</p>
              </div>
            </div>

            {results.best_match && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-green-900">🎯 Best Match</h3>
                  <span className="text-2xl font-bold text-green-600">{results.best_match.fit_score}%</span>
                </div>
                <p className="text-lg font-medium">{results.best_match.lender_display_name}</p>
                {results.best_match.program_name && (
                  <p className="text-sm text-gray-600">{results.best_match.program_name}</p>
                )}
                <p className="text-sm text-gray-700 mt-2">{results.best_match.recommendation}</p>
              </div>
            )}
          </div>

          {results.eligible_matches.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Eligible Lenders</h2>
              {results.eligible_matches.map((match) => (
                <LenderMatchCard key={match.lender_id} match={match} />
              ))}
            </div>
          )}

          {results.needs_review_matches && results.needs_review_matches.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Needs Review Lenders</h2>
              {results.needs_review_matches.map((match) => (
                <LenderMatchCard key={match.lender_id} match={match} />
              ))}
            </div>
          )}

          {results.ineligible_matches.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Ineligible Lenders</h2>
              {results.ineligible_matches.map((match) => (
                <LenderMatchCard key={match.lender_id} match={match} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function LenderMatchCard({ match }: { match: any }) {
  return (
    <div className="bg-white rounded-lg border p-4">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-semibold text-lg">{match.lender_display_name}</h3>
          {match.program_name && <p className="text-sm text-gray-600">{match.program_name}</p>}
        </div>
        <div className="flex items-center space-x-2">
          {match.fit_score && (
            <span className="text-xl font-bold text-gray-900">{match.fit_score}%</span>
          )}
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
            match.status === 'ELIGIBLE' ? 'bg-green-100 text-green-800' :
            match.status === 'NEEDS_REVIEW' ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>
            {match.status}
          </span>
        </div>
      </div>
      <p className="text-sm text-gray-700 mb-3">{match.summary}</p>
      
      <details className="mt-3">
        <summary className="cursor-pointer text-sm font-medium text-indigo-600">
          View Criteria Details ({match.criteria_met}/{match.criteria_total} met)
        </summary>
        <div className="mt-3 space-y-2">
          {match.criteria_details.map((crit: CriteriaEvaluation, idx: number) => (
            <div key={idx} className={`flex items-start space-x-2 p-2 rounded ${
              crit.passed ? 'bg-green-50' : 'bg-red-50'
            }`}>
              {crit.passed ? (
                <CheckCircle size={18} className="text-green-600 mt-0.5" />
              ) : (
                <XCircle size={18} className="text-red-600 mt-0.5" />
              )}
              <div className="flex-1">
                <p className="text-sm font-medium">{crit.criteria_name}</p>
                <p className="text-xs text-gray-600">{crit.explanation}</p>
                <div className="flex space-x-4 text-xs text-gray-500 mt-1">
                  <span>Expected: {crit.expected_value}</span>
                  <span>Actual: {crit.actual_value}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </details>
    </div>
  )
}

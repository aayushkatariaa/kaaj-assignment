import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { applicationsApi } from '../services/api'
import { useForm } from 'react-hook-form'
import { Upload, AlertCircle, Loader2, XCircle } from 'lucide-react'

// US States for dropdown
const US_STATES = [
  { code: 'AL', name: 'Alabama' }, { code: 'AK', name: 'Alaska' }, { code: 'AZ', name: 'Arizona' },
  { code: 'AR', name: 'Arkansas' }, { code: 'CA', name: 'California' }, { code: 'CO', name: 'Colorado' },
  { code: 'CT', name: 'Connecticut' }, { code: 'DE', name: 'Delaware' }, { code: 'FL', name: 'Florida' },
  { code: 'GA', name: 'Georgia' }, { code: 'HI', name: 'Hawaii' }, { code: 'ID', name: 'Idaho' },
  { code: 'IL', name: 'Illinois' }, { code: 'IN', name: 'Indiana' }, { code: 'IA', name: 'Iowa' },
  { code: 'KS', name: 'Kansas' }, { code: 'KY', name: 'Kentucky' }, { code: 'LA', name: 'Louisiana' },
  { code: 'ME', name: 'Maine' }, { code: 'MD', name: 'Maryland' }, { code: 'MA', name: 'Massachusetts' },
  { code: 'MI', name: 'Michigan' }, { code: 'MN', name: 'Minnesota' }, { code: 'MS', name: 'Mississippi' },
  { code: 'MO', name: 'Missouri' }, { code: 'MT', name: 'Montana' }, { code: 'NE', name: 'Nebraska' },
  { code: 'NV', name: 'Nevada' }, { code: 'NH', name: 'New Hampshire' }, { code: 'NJ', name: 'New Jersey' },
  { code: 'NM', name: 'New Mexico' }, { code: 'NY', name: 'New York' }, { code: 'NC', name: 'North Carolina' },
  { code: 'ND', name: 'North Dakota' }, { code: 'OH', name: 'Ohio' }, { code: 'OK', name: 'Oklahoma' },
  { code: 'OR', name: 'Oregon' }, { code: 'PA', name: 'Pennsylvania' }, { code: 'RI', name: 'Rhode Island' },
  { code: 'SC', name: 'South Carolina' }, { code: 'SD', name: 'South Dakota' }, { code: 'TN', name: 'Tennessee' },
  { code: 'TX', name: 'Texas' }, { code: 'UT', name: 'Utah' }, { code: 'VT', name: 'Vermont' },
  { code: 'VA', name: 'Virginia' }, { code: 'WA', name: 'Washington' }, { code: 'WV', name: 'West Virginia' },
  { code: 'WI', name: 'Wisconsin' }, { code: 'WY', name: 'Wyoming' }, { code: 'DC', name: 'Washington DC' }
]

// Helper to extract error message from API response
function getErrorMessages(error: any): string[] {
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

export default function ApplicationForm() {
  const navigate = useNavigate()
  const { register, handleSubmit, formState: { errors } } = useForm()
  const [step, setStep] = useState(1)
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [createErrors, setCreateErrors] = useState<string[]>([])

  const createMutation = useMutation({
    mutationFn: (data: any) => applicationsApi.create(data),
    onSuccess: (response) => {
      navigate(`/applications/${response.data.id}`)
    },
    onError: (error: any) => {
      console.error('Error creating application:', error)
      setCreateErrors(getErrorMessages(error))
    }
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => applicationsApi.uploadPdf(file),
    onSuccess: (response) => {
      navigate(`/applications/${response.data.id}`)
    },
    onError: (error: any) => {
      console.error('Error uploading PDF:', error)
      const messages = getErrorMessages(error)
      setUploadError(messages.join(', '))
    }
  })

  const handlePdfUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.type !== 'application/pdf') {
        setUploadError('Only PDF files are supported')
        return
      }
      setPdfFile(file)
      setUploadError(null)
    }
  }

  const submitPdf = () => {
    if (pdfFile) {
      uploadMutation.mutate(pdfFile)
    }
  }

  const onSubmit = (data: any) => {
    setCreateErrors([]) // Clear previous errors
    const payload = {
      business: {
        legal_name: data.legal_name,
        state: data.state,
        city: data.city,
        industry: data.industry,
        years_in_business: parseFloat(data.years_in_business) || undefined,
        annual_revenue: parseFloat(data.annual_revenue) || undefined,
      },
      guarantor: {
        first_name: data.first_name,
        last_name: data.last_name,
        email: data.email,
        fico_score: parseInt(data.fico_score) || undefined,
        has_bankruptcy: data.has_bankruptcy === 'true',
      },
      business_credit: data.paynet_score ? {
        paynet_score: parseInt(data.paynet_score) || undefined,
      } : undefined,
      loan_request: {
        requested_amount: parseFloat(data.requested_amount),
        equipment_type: data.equipment_type,
        equipment_year: parseInt(data.equipment_year) || undefined,
        term_months: parseInt(data.term_months) || undefined,
      },
    }
    createMutation.mutate(payload)
  }

  const isLoading = createMutation.isPending || uploadMutation.isPending

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">New Loan Application</h1>

      {/* PDF Upload Option - Disabled */}
      <div className="bg-gray-100 rounded-lg shadow-sm border border-gray-300 p-6 mb-6 opacity-60">
        <div className="flex items-start space-x-3">
          <Upload className="text-gray-400 mt-1" size={24} />
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-600 mb-2">Upload PDF Application (Coming Soon)</h2>
            <p className="text-sm text-gray-500 mb-4">
              PDF upload feature is temporarily disabled. Please use the manual form below.
            </p>
            <div className="flex items-center space-x-3">
              <input
                type="file"
                accept=".pdf"
                onChange={handlePdfUpload}
                disabled={true}
                className="block w-full text-sm text-gray-500 border border-gray-300 rounded-lg cursor-not-allowed bg-gray-200 focus:outline-none disabled:opacity-50"
              />
              <button
                disabled={true}
                className="px-4 py-2 bg-gray-400 text-white rounded-md cursor-not-allowed opacity-50"
              >
                <span>Disabled</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="text-center mb-4">
        <span className="text-gray-500">Manual Entry</span>
      </div>

      {/* Display create errors */}
      {createErrors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-start space-x-3">
            <XCircle className="text-red-500 mt-0.5 flex-shrink-0" size={20} />
            <div>
              <h3 className="font-semibold text-red-800">Failed to Create Application</h3>
              <ul className="list-disc list-inside mt-1">
                {createErrors.map((err, idx) => (
                  <li key={idx} className="text-sm text-red-700">{err}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border p-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Business Information</h2>
              <div>
                <label className="block text-sm font-medium text-gray-700">Legal Name *</label>
                <input {...register('legal_name', { required: true })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500" />
                {errors.legal_name && <span className="text-red-500 text-sm">Required</span>}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">State *</label>
                  <select {...register('state', { required: true })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
                    <option value="">Select State</option>
                    {US_STATES.map(s => (
                      <option key={s.code} value={s.code}>{s.name} ({s.code})</option>
                    ))}
                  </select>
                  {errors.state && <span className="text-red-500 text-sm">Required</span>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">City</label>
                  <input {...register('city')}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Industry</label>
                  <input {...register('industry')}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Years in Business</label>
                  <input {...register('years_in_business', { 
                    min: { value: 0, message: 'Must be 0 or greater' },
                    max: { value: 100, message: 'Must be 100 or less' }
                  })} type="number" step="0.1" min="0" max="100"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
                  {errors.years_in_business && <span className="text-red-500 text-sm">{errors.years_in_business.message as string}</span>}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Annual Revenue</label>
                <input {...register('annual_revenue', {
                  min: { value: 0, message: 'Must be 0 or greater' }
                })} type="number" min="0"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm" placeholder="500000" />
                {errors.annual_revenue && <span className="text-red-500 text-sm">{errors.annual_revenue.message as string}</span>}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Personal Guarantor</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">First Name *</label>
                  <input {...register('first_name', { required: 'First name is required' })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
                  {errors.first_name && <span className="text-red-500 text-sm">{errors.first_name.message as string}</span>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Last Name *</label>
                  <input {...register('last_name', { required: 'Last name is required' })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
                  {errors.last_name && <span className="text-red-500 text-sm">{errors.last_name.message as string}</span>}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <input {...register('email', {
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address'
                  }
                })} type="email"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm" placeholder="john@example.com" />
                {errors.email && <span className="text-red-500 text-sm">{errors.email.message as string}</span>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">FICO Score *</label>
                <input {...register('fico_score', { 
                  required: 'FICO score is required',
                  min: { value: 300, message: 'FICO score must be at least 300' },
                  max: { value: 850, message: 'FICO score must be at most 850' }
                })} type="number" min="300" max="850"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm" placeholder="680" />
                {errors.fico_score && <span className="text-red-500 text-sm">{errors.fico_score.message as string}</span>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Has Bankruptcy?</label>
                <select {...register('has_bankruptcy')}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                  <option value="false">No</option>
                  <option value="true">Yes</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">PayNet Score</label>
                <input {...register('paynet_score')} type="number"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm" placeholder="70" />
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Loan Request</h2>
              <div>
                <label className="block text-sm font-medium text-gray-700">Requested Amount *</label>
                <input {...register('requested_amount', { 
                  required: 'Requested amount is required',
                  min: { value: 1000, message: 'Minimum loan amount is $1,000' },
                  max: { value: 10000000, message: 'Maximum loan amount is $10,000,000' }
                })} type="number" min="1000" max="10000000"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm" placeholder="100000" />
                {errors.requested_amount && <span className="text-red-500 text-sm">{errors.requested_amount.message as string}</span>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Equipment Type</label>
                <input {...register('equipment_type')}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm" placeholder="construction" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Equipment Year</label>
                  <input {...register('equipment_year', {
                    min: { value: 1990, message: 'Year must be 1990 or later' },
                    max: { value: new Date().getFullYear() + 1, message: `Year cannot exceed ${new Date().getFullYear() + 1}` }
                  })} type="number" min="1990" max={new Date().getFullYear() + 1}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm" placeholder="2020" />
                  {errors.equipment_year && <span className="text-red-500 text-sm">{errors.equipment_year.message as string}</span>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Term (months)</label>
                  <input {...register('term_months', {
                    min: { value: 12, message: 'Minimum term is 12 months' },
                    max: { value: 84, message: 'Maximum term is 84 months' }
                  })} type="number" min="12" max="84"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm" placeholder="60" />
                  {errors.term_months && <span className="text-red-500 text-sm">{errors.term_months.message as string}</span>}
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-between pt-4 border-t">
            <button type="button" onClick={() => setStep(Math.max(1, step - 1))}
              disabled={step === 1 || isLoading}
              className="px-4 py-2 border rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50">
              Previous
            </button>
            {step < 3 ? (
              <button type="button" onClick={() => setStep(step + 1)}
                disabled={isLoading}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50">
                Next
              </button>
            ) : (
              <button type="submit"
                disabled={isLoading}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 flex items-center space-x-2">
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    <span>Submitting...</span>
                  </>
                ) : (
                  <span>Submit Application</span>
                )}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}

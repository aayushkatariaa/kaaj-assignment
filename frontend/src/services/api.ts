import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Applications API
export const applicationsApi = {
  list: (page = 1, pageSize = 20) =>
    api.get(`/applications/?page=${page}&page_size=${pageSize}`),
  get: (id: number) => api.get(`/applications/${id}`),
  create: (data: any) => api.post('/applications/', data),
  update: (id: number, data: any) => api.put(`/applications/${id}`, data),
  submit: (id: number) => api.post(`/applications/${id}/submit`),
  delete: (id: number) => api.delete(`/applications/${id}`),
  uploadPdf: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/applications/upload-pdf/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
  listPdfs: () => api.get('/applications/pdfs/'),
  ingestPdfs: (force = false) => api.post(`/applications/ingest-pdfs/?force=${force}`),
  ingestionStatus: () => api.get('/applications/ingestion-status/'),
}

// Underwriting API
export const underwritingApi = {
  run: (applicationId: number) => api.post(`/underwriting/${applicationId}/run`),
  status: (applicationId: number) => api.get(`/underwriting/${applicationId}/status`),
  results: (applicationId: number) => api.get(`/underwriting/${applicationId}/results`),
}

// Lenders API
export const lendersApi = {
  list: (page = 1, pageSize = 20) =>
    api.get(`/lenders/?page=${page}&page_size=${pageSize}`),
  get: (id: number) => api.get(`/lenders/${id}`),
  create: (data: any) => api.post('/lenders/', data),
  update: (id: number, data: any) => api.put(`/lenders/${id}`, data),
  delete: (id: number) => api.delete(`/lenders/${id}`),
  
  // Programs
  createProgram: (lenderId: number, data: any) =>
    api.post(`/lenders/${lenderId}/programs/`, data),
  updateProgram: (lenderId: number, programId: number, data: any) =>
    api.put(`/lenders/${lenderId}/programs/${programId}`, data),
  deleteProgram: (lenderId: number, programId: number) =>
    api.delete(`/lenders/${lenderId}/programs/${programId}`),
  
  // Criteria
  createCriteria: (lenderId: number, programId: number, data: any) =>
    api.post(`/lenders/${lenderId}/programs/${programId}/criteria/`, data),
  updateCriteria: (lenderId: number, programId: number, criteriaId: number, data: any) =>
    api.put(`/lenders/${lenderId}/programs/${programId}/criteria/${criteriaId}`, data),
  deleteCriteria: (lenderId: number, programId: number, criteriaId: number) =>
    api.delete(`/lenders/${lenderId}/programs/${programId}/criteria/${criteriaId}`),
}

export default api

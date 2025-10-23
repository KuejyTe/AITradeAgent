import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

const apiService = {
  async healthCheck() {
    const response = await apiClient.get('/api/v1/health')
    return response.data
  },

  async getRoot() {
    const response = await apiClient.get('/')
    return response.data
  },
}

export default apiService

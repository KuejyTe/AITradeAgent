import axios, { AxiosInstance } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const apiService = {
  async healthCheck(): Promise<{ status: string; message: string }> {
    const response = await apiClient.get('/api/v1/health')
    return response.data
  },

  async getRoot<T = unknown>(): Promise<T> {
    const response = await apiClient.get<T>('/')
    return response.data
  },
}

export default apiClient

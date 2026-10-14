import axios from 'axios'
import router from '../router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
})

export function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('skillswap_user') || 'null')
  } catch {
    localStorage.removeItem('skillswap_user')
    return null
  }
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('skillswap_token')
  if (token) config.headers.Authorization = token
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('skillswap_token')
      localStorage.removeItem('skillswap_user')
      if (router.currentRoute.value.meta.auth || router.currentRoute.value.meta.admin) {
        router.replace('/login')
      }
    }
    return Promise.reject(error)
  },
)

export function getErrorMessage(error) {
  if (error.response) {
    return error.response.data?.error
      || error.response.data?.message
      || `The server returned an unexpected response (${error.response.status}). Please try again.`
  }
  if (error.request) {
    return 'Could not reach the SkillSwap API. Check that the backend is running and try again.'
  }
  return error.message || 'Something went wrong. Please try again.'
}

export default api

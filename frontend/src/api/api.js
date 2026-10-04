import axios from 'axios'

const apiBaseUrl = import.meta.env.VITE_API_URL
  || `${window.location.protocol}//${window.location.hostname}:8000`

const api = axios.create({
  baseURL: apiBaseUrl,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  register: (data) => api.post("/auth/register", data),
  login: (credentials) =>
    api.post('/auth/login',
    new URLSearchParams(credentials),
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded'}}
    ),
  logout: () => api.post('/api/auth/logout'),
  me: () => api.get('/users/me')
}

export const userApi = {
  create: (data) => api.post('/users/create/', data),
  get: (id) => api.get(`/users/${id}`),
  getAll: () => api.get('/users/'),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.post(`/users/delete/${id}`)
}

export const notesApi = {
  create: (data) => api.post('/notes/', data),
  getOne: (id) => api.get(`/notes/${id}`),
  getAll: () => api.get(`/notes`),
  update: (id, data) => api.put(`/notes/${id}`, data),
  delete: (id) => api.delete(`/notes/${id}`),
  query: (query) => api.get(`/notes/search?q=${query}`),
}

export const aiApi = {
  // All actions operate on a note the authenticated user owns.
  summarize: (noteId, provider) =>
    api.post('/ai/summarize', { note_id: noteId, provider }),
  ask: (noteId, question, provider) =>
    api.post('/ai/ask', { note_id: noteId, question, provider }),
  enhance: (noteId, provider) =>
    api.post('/ai/enhance', { note_id: noteId, provider }),
  generateQuestions: (noteId, provider) =>
    api.post('/ai/questions', { note_id: noteId, provider }),
}

export const chatApi = {
  createSession: (data) => api.post('/chat/sessions/', data),
  getOneSession: (id) => api.get(`/chat/sessions/${id}`),
  getAllSessions: () => api.get('/chat/sessions'),
  updateSession: (id, data) => api.put(`/chat/sessions/${id}`, data),
  deleteSession: (id) => api.delete(`/chat/sessions/${id}`),
  createMessage: (data) => api.post('/chat/messages', data),
  getAllMessages: (id) => api.get(`/chat/messages/${id}`),
}

export default api 




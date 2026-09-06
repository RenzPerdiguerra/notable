import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (credentials) =>
    api.post('api/auth/login',
    new URLSearchParams(credentials),
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded'}}
    ),
  logout: () => api.post('/api/auth/logout'),
  me: () => api.get('/users/me')
}
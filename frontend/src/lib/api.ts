import axios from 'axios';

// Create an Axios instance
const api = axios.create({
    baseURL: (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api',
    withCredentials: true, // Important for cookies/sessions
    headers: {
        'Content-Type': 'application/json',
    },
});

// Response interceptor
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // Handle common errors (e.g., global error logging)
        console.error('API Error:', error.response?.data?.detail || error.message);
        return Promise.reject(error);
    }
);

export default api;

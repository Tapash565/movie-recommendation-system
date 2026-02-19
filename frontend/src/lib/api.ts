import axios from 'axios';
import { signOut } from 'firebase/auth';
import { auth } from './firebase';

// Create an Axios instance
const api = axios.create({
    baseURL: (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api',
    // Remove withCredentials as we move from session cookies to JWT tokens
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add Firebase ID token
api.interceptors.request.use(
    async (config) => {
        if (!auth) return config;
        const user = auth.currentUser;

        if (user) {
            try {
                // Get the current ID token (cache-respecting)
                const token = await user.getIdToken();
                config.headers.Authorization = `Bearer ${token}`;
            } catch (error) {
                console.error('Error getting Firebase token:', error);
                // Fail the request instead of proceeding unauthenticated
                throw error;
            }
        }

        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        // Handle common errors (e.g., 401 Unauthorized)
        if (error.response?.status === 401) {
            console.warn('Unauthorized request detected - signing out');
            try {
                if (auth) {
                    await signOut(auth);
                }
                // Only redirect in the browser
                if (typeof window !== 'undefined') {
                    window.location.href = '/login';
                }
            } catch (signOutError) {
                console.error('Error during auto-signout:', signOutError);
            }
        }
        console.error('API Error:', error.response?.data?.detail || error.message);
        return Promise.reject(error);
    }
);

export default api;

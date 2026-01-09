/**
 * Movie Recommendation API Client
 * Handles all API interactions for the MovieRec application
 */

const API_BASE = '';

/**
 * Search for movies
 * @param {string} query - Search query
 * @returns {Promise<Object>} Search results
 */
async function searchMovies(query) {
    const formData = new FormData();
    formData.append('search_movie', query);
    
    const response = await fetch(`${API_BASE}/api/search`, {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
    }
    
    return await response.json();
}

/**
 * Get movie recommendations
 * @param {string} movie - Movie title
 * @returns {Promise<Object>} Recommendations
 */
async function getRecommendations(movie) {
    const formData = new FormData();
    formData.append('movie', movie);
    
    const response = await fetch(`${API_BASE}/api/recommend`, {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        throw new Error(`Recommendations failed: ${response.statusText}`);
    }
    
    return await response.json();
}

/**
 * Get movie details (JSON API)
 * @param {string} title - Movie title
 * @returns {Promise<Object>} Movie details
 */
async function getMovieDetails(title) {
    const encodedTitle = encodeURIComponent(title);
    const response = await fetch(`${API_BASE}/api/movie/${encodedTitle}`);
    
    if (!response.ok) {
        if (response.status === 404) {
            throw new Error('Movie not found');
        }
        throw new Error(`Failed to fetch movie: ${response.statusText}`);
    }
    
    return await response.json();
}

/**
 * Authenticate user
 * @param {string} username - Username
 * @param {string} password - Password
 * @returns {Promise<Object>} Authentication result
 */
async function authenticate(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${API_BASE}/api/authenticate`, {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        throw new Error(`Authentication failed: ${response.statusText}`);
    }
    
    return await response.json();
}

/**
 * Logout user
 * @returns {Promise<void>}
 */
async function logout() {
    const response = await fetch(`${API_BASE}/logout`, {
        method: 'GET',
        credentials: 'include'
    });
    
    if (!response.ok) {
        throw new Error(`Logout failed: ${response.statusText}`);
    }
    
    return await response.json();
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        searchMovies,
        getRecommendations,
        getMovieDetails,
        authenticate,
        logout
    };
}

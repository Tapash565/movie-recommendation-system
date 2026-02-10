'use client';

import { Suspense, useEffect, useState, useMemo } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import MovieCard from '@/components/MovieCard';

interface Movie {
    id: number;
    title: string;
    year: string;
    poster_url: string;
    vote_average: number;
    overview?: string;
}

interface PaginatedResponse {
    movies: Movie[];
    total_count: number;
    page: number;
    limit: number;
    total_pages: number;
    order_by: string;
}

function SearchContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const currentPage = parseInt(searchParams.get('page') || '1');
    const orderBy = searchParams.get('order_by') || 'rating';

    const [allMovies, setAllMovies] = useState<Movie[]>([]);
    const [loading, setLoading] = useState(true);
    const [query, setQuery] = useState('');
    const [totalCount, setTotalCount] = useState(0);
    const [totalPages, setTotalPages] = useState(0);

    // Fetch movies from API when page or order_by changes
    useEffect(() => {
        setLoading(true);
        api.get<PaginatedResponse>('/movies/all', {
            params: {
                page: currentPage,
                limit: 50,
                order_by: orderBy
            }
        })
            .then((res) => {
                setAllMovies(res.data.movies);
                setTotalCount(res.data.total_count);
                setTotalPages(res.data.total_pages);
            })
            .catch((err) => console.error(err))
            .finally(() => setLoading(false));
    }, [currentPage, orderBy]);

    // Filter movies client-side based on search query
    const filteredMovies = useMemo(() => {
        if (!query.trim()) {
            return allMovies;
        }
        const lowerQuery = query.toLowerCase();
        return allMovies.filter(movie =>
            movie.title.toLowerCase().includes(lowerQuery) ||
            (movie.overview && movie.overview.toLowerCase().includes(lowerQuery))
        );
    }, [allMovies, query]);

    // Update URL params when sorting changes
    const handleSortChange = (newOrderBy: string) => {
        const params = new URLSearchParams(searchParams.toString());
        params.set('order_by', newOrderBy);
        params.set('page', '1'); // Reset to page 1 when sorting changes
        router.push(`/search?${params.toString()}`);
    };

    // Update URL params when page changes
    const handlePageChange = (newPage: number) => {
        const params = new URLSearchParams(searchParams.toString());
        params.set('page', newPage.toString());
        router.push(`/search?${params.toString()}`);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    return (
        <div className="max-w-7xl mx-auto px-6 py-10 min-h-screen">
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-6">Browse Movies</h1>

                <div className="flex flex-col md:flex-row gap-4 mb-6">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search movies..."
                        className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 focus:outline-none focus:border-purple-500 transition-colors"
                    />
                    <select
                        value={orderBy}
                        onChange={(e) => handleSortChange(e.target.value)}
                        className="bg-gray-800 border border-gray-700 rounded-xl px-6 py-3 focus:outline-none focus:border-purple-500 transition-colors appearance-none cursor-pointer"
                    >
                        <option value="rating">Top Rated</option>
                        <option value="name">Alphabetical</option>
                        <option value="date">Recently Added</option>
                    </select>
                </div>

                <p className="text-gray-400 mb-6">
                    Showing {filteredMovies.length} of {totalCount} movies
                    {query && ` matching "${query}"`}
                </p>
            </div>

            {loading ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                    {[...Array(10)].map((_, i) => (
                        <div key={i} className="aspect-[2/3] bg-gray-800/50 rounded-xl animate-pulse"></div>
                    ))}
                </div>
            ) : (
                <>
                    {filteredMovies.length > 0 ? (
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                            {filteredMovies.map((movie) => (
                                <MovieCard key={movie.id} movie={movie} />
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-20 text-gray-500">
                            {query ? `No movies found matching "${query}"` : 'No movies available'}
                        </div>
                    )}

                    {/* Pagination Controls */}
                    {!query && totalPages > 1 && (
                        <div className="flex justify-center items-center gap-2 mt-12">
                            <button
                                onClick={() => handlePageChange(currentPage - 1)}
                                disabled={currentPage === 1}
                                className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                Previous
                            </button>

                            <div className="flex gap-2">
                                {/* Show first page */}
                                {currentPage > 3 && (
                                    <>
                                        <button
                                            onClick={() => handlePageChange(1)}
                                            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:bg-gray-700 transition-colors"
                                        >
                                            1
                                        </button>
                                        {currentPage > 4 && (
                                            <span className="px-2 py-2 text-gray-500">...</span>
                                        )}
                                    </>
                                )}

                                {/* Show pages around current page */}
                                {Array.from({ length: totalPages }, (_, i) => i + 1)
                                    .filter(page =>
                                        page === currentPage ||
                                        page === currentPage - 1 ||
                                        page === currentPage + 1 ||
                                        page === currentPage - 2 ||
                                        page === currentPage + 2
                                    )
                                    .map(page => (
                                        <button
                                            key={page}
                                            onClick={() => handlePageChange(page)}
                                            className={`px-4 py-2 rounded-lg border transition-colors ${currentPage === page
                                                ? 'bg-purple-600 border-purple-600 text-white'
                                                : 'bg-gray-800 border-gray-700 hover:bg-gray-700'
                                                }`}
                                        >
                                            {page}
                                        </button>
                                    ))}

                                {/* Show last page */}
                                {currentPage < totalPages - 2 && (
                                    <>
                                        {currentPage < totalPages - 3 && (
                                            <span className="px-2 py-2 text-gray-500">...</span>
                                        )}
                                        <button
                                            onClick={() => handlePageChange(totalPages)}
                                            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:bg-gray-700 transition-colors"
                                        >
                                            {totalPages}
                                        </button>
                                    </>
                                )}
                            </div>

                            <button
                                onClick={() => handlePageChange(currentPage + 1)}
                                disabled={currentPage === totalPages}
                                className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                Next
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

export default function SearchPage() {
    return (
        <Suspense fallback={<div className="p-10 text-center">Loading search...</div>}>
            <SearchContent />
        </Suspense>
    );
}

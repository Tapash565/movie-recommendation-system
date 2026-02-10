'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import api from '@/lib/api';
import MovieCard from '@/components/MovieCard';

interface Movie {
    id: number;
    title: string;
    year: string;
    poster_url: string;
    vote_average: number;
}

function SearchContent() {
    const searchParams = useSearchParams();
    const q = searchParams.get('q') || '';
    const orderBy = searchParams.get('order_by') || '';

    const [movies, setMovies] = useState<Movie[]>([]);
    const [loading, setLoading] = useState(false);
    const [query, setQuery] = useState(q);

    useEffect(() => {
        if (q) {
            setLoading(true);
            api.get('/movies/search', { params: { q, order_by: orderBy } })
                .then((res) => setMovies(res.data.movies))
                .catch((err) => console.error(err))
                .finally(() => setLoading(false));
        } else {
            setMovies([]); // Clear if no query
        }
        setQuery(q);
    }, [q, orderBy]);

    return (
        <div className="max-w-7xl mx-auto px-6 py-10 min-h-screen">
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-6">Search Results</h1>

                <form action="/search" className="flex flex-col md:flex-row gap-4 mb-8">
                    <input
                        type="text"
                        name="q"
                        defaultValue={query}
                        placeholder="Search..."
                        className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 focus:outline-none focus:border-purple-500 transition-colors"
                    />
                    <select
                        name="order_by"
                        defaultValue={orderBy}
                        className="bg-gray-800 border border-gray-700 rounded-xl px-6 py-3 focus:outline-none focus:border-purple-500 transition-colors appearance-none cursor-pointer"
                    >
                        <option value="">Sort by Relevance</option>
                        <option value="rating">Top Rated</option>
                        <option value="name">Alphabetical</option>
                    </select>
                    <button
                        type="submit"
                        className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-8 py-3 rounded-xl transition-colors"
                    >
                        Search
                    </button>
                </form>

                {query && (
                    <p className="text-gray-400 mb-6">
                        Found {movies.length} results for "<span className="text-white">{query}</span>"
                    </p>
                )}
            </div>

            {loading ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                    {[...Array(10)].map((_, i) => (
                        <div key={i} className="aspect-[2/3] bg-gray-800/50 rounded-xl animate-pulse"></div>
                    ))}
                </div>
            ) : (
                <>
                    {movies.length > 0 ? (
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                            {movies.map((movie) => (
                                <MovieCard key={movie.id} movie={movie} />
                            ))}
                        </div>
                    ) : (
                        query && <div className="text-center py-20 text-gray-500">No movies found matching your search.</div>
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

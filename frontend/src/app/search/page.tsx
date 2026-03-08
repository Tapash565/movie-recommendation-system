'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import api from '@/lib/api';
import MovieCard from '@/components/MovieCard';
import MovieSkeleton from '@/components/MovieSkeleton';

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
    const page = parseInt(searchParams.get('page') || '1');

    const [movies, setMovies] = useState<Movie[]>([]);
    const [totalResults, setTotalResults] = useState(0);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (q) {
            setLoading(true);
            const filterAdult = typeof window !== 'undefined' && localStorage.getItem('filter_adult') === 'true';
            api.get('/movies/search', { params: { q, order_by: orderBy, page, filter_adult: filterAdult } })
                .then((res) => {
                    setMovies(res.data.movies);
                    setTotalResults(res.data.total_results || 0);
                })
                .catch((err) => console.error(err))
                .finally(() => setLoading(false));
        } else {
            setMovies([]);
            setTotalResults(0);
        }
    }, [q, orderBy, page]);

    return (
        <main className="max-w-7xl mx-auto px-6 py-10 min-h-screen">
            <section aria-labelledby="search-heading">
                <div className="mb-8">
                    <h1 id="search-heading" className="text-3xl font-bold mb-6">Search Results</h1>

                    <form action="/search" className="flex flex-col md:flex-row gap-4 mb-8" role="search">
                        <div className="flex-1">
                            <label htmlFor="q" className="sr-only">Search Movies</label>
                            <input
                                id="q"
                                type="text"
                                name="q"
                                defaultValue={q}
                                placeholder="Search movies..."
                                className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 focus:outline-none focus:border-purple-500 transition-colors"
                            />
                        </div>
                        <div>
                            <label htmlFor="order_by" className="sr-only">Sort By</label>
                            <select
                                id="order_by"
                                name="order_by"
                                defaultValue={orderBy}
                                className="bg-gray-800 border border-gray-700 rounded-xl px-6 py-3 focus:outline-none focus:border-purple-500 transition-colors appearance-none cursor-pointer w-full"
                            >
                                <option value="">Sort by Relevance</option>
                                <option value="rating">Top Rated</option>
                                <option value="name">Alphabetical</option>
                            </select>
                        </div>
                        <button
                            type="submit"
                            className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-8 py-3 rounded-xl transition-colors"
                        >
                            Search
                        </button>
                    </form>

                    {q && !loading && (
                        <p className="text-gray-400 mb-6" aria-live="polite">
                            Found {totalResults} results for &quot;<span className="text-white">{q}</span>&quot;
                        </p>
                    )}
                </div>

                {loading ? (
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                        {[...Array(10)].map((_, i) => (
                            <MovieSkeleton key={i} />
                        ))}
                    </div>
                ) : (
                    <>
                        {movies.length > 0 ? (
                            <>
                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                                    {movies.map((movie) => (
                                        <MovieCard key={movie.id} movie={movie} />
                                    ))}
                                </div>

                                {totalResults > 24 && (
                                    <nav className="flex justify-center mt-12 gap-2" aria-label="Pagination">
                                        {page > 1 && (
                                            <a
                                                href={`/search?q=${q}&order_by=${orderBy}&page=${page - 1}`}
                                                className="px-4 py-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
                                            >
                                                Previous
                                            </a>
                                        )}
                                        <span className="px-4 py-2 bg-purple-600 rounded-lg">
                                            Page {page}
                                        </span>
                                        {totalResults > page * 24 && (
                                            <a
                                                href={`/search?q=${q}&order_by=${orderBy}&page=${page + 1}`}
                                                className="px-4 py-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
                                            >
                                                Next
                                            </a>
                                        )}
                                    </nav>
                                )}
                            </>
                        ) : (
                            q && <div className="text-center py-20 text-gray-500">No movies found matching your search.</div>
                        )}
                    </>
                )}
            </section>
        </main>
    );
}

export default function SearchPage() {
    return (
        <Suspense fallback={<div className="p-10 text-center">Loading search...</div>}>
            <SearchContent />
        </Suspense>
    );
}

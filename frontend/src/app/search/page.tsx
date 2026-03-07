'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import api from '@/lib/api';
import MovieRow from '@/components/MovieRow';

const PAGE_SIZE = 24;

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
            api.get('/movies/search', { 
                params: { q, order_by: orderBy, page , page_size: PAGE_SIZE} 
            })
                .then((res) => {
                    setMovies(res.data.movies || []);
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
        <main className="min-h-screen pb-10 pt-16 sm:pt-20 md:pt-24">
            <div className="px-4 sm:px-6 md:px-8 mb-6 sm:mb-8">
                <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-5 sm:mb-6">Search</h1>

                {/* Search Form */}
                <form action="/search" className="flex flex-col sm:flex-row gap-3 mb-6">
                    <div className="flex-1">
                        <input
                            type="text"
                            name="q"
                            defaultValue={q}
                            placeholder="Search for movies..."
                            className="w-full bg-white/10 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-[#E50914] focus:bg-white/15 transition-all"
                        />
                    </div>
                    <div className="sm:w-40">
                        <select
                            name="order_by"
                            defaultValue={orderBy}
                            className="w-full bg-white/10 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-[#E50914] appearance-none cursor-pointer"
                        >
                            <option value="" className="bg-[#14141D]">Relevance</option>
                            <option value="rating" className="bg-[#14141D]">Top Rated</option>
                            <option value="name" className="bg-[#14141D]">A-Z</option>
                        </select>
                    </div>
                    <button
                        type="submit"
                        className="bg-[#E50914] hover:bg-[#b2070f] text-white font-semibold px-6 py-3 rounded-lg transition-all duration-200 hover:scale-105"
                    >
                        Search
                    </button>
                </form>

                {/* Results Count */}
                {q && !loading && (
                    <p className="text-gray-400 text-sm sm:text-base">
                        {totalResults} result{totalResults !== 1 ? 's' : ''} for &quot;<span className="text-white">{q}</span>&quot;
                    </p>
                )}
            </div>

            {/* Results */}
            <div className="px-4 sm:px-0">
                {loading ? (
                    <div className="flex gap-2 sm:gap-3 overflow-hidden px-4 sm:px-0">
                        {[...Array(7)].map((_, i) => (
                            <div key={i} className="flex-shrink-0 w-[100px] xs:w-[120px] sm:w-[140px] md:w-[160px] lg:w-[180px]">
                                <div className="aspect-[2/3] bg-white/10 rounded-md animate-pulse" />
                                <div className="mt-2 space-y-2">
                                    <div className="h-3 sm:h-4 bg-white/10 rounded w-3/4 animate-pulse" />
                                    <div className="h-2 sm:h-3 bg-white/10 rounded w-1/4 animate-pulse" />
                                </div>
                            </div>
                        ))}
                    </div>
                ) : movies.length > 0 ? (
                    <>
                        <MovieRow title="Results" movies={movies} />

                        {/* Pagination */}
                        {totalResults > PAGE_SIZE && (
                            <div className="flex justify-center gap-3 mt-8 sm:mt-10">
                                {page > 1 && (
                                    <a
                                        href={`/search?q=${q}&order_by=${orderBy}&page=${page - 1}`}
                                        className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg transition-colors"
                                    >
                                        Previous
                                    </a>
                                )}
                                <span className="bg-[#E50914] text-white px-4 py-2 rounded-lg">
                                    Page {page}
                                </span>
                                {totalResults > page * PAGE_SIZE && (
                                    <a
                                        href={`/search?q=${q}&order_by=${orderBy}&page=${page + 1}`}
                                        className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg transition-colors"
                                    >
                                        Next
                                    </a>
                                )}
                            </div>
                        )}
                    </>
                ) : q ? (
                    <div className="text-center py-16 sm:py-20 text-gray-500 px-4">
                        No movies found matching your search.
                    </div>
                ) : null}
            </div>
        </main>
    );
}

export default function SearchPage() {
    return (
        <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-white pt-20">Loading...</div>}>
            <SearchContent />
        </Suspense>
    );
}

'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import MovieCard from '@/components/MovieCard';
import MovieSkeleton from '@/components/MovieSkeleton';

interface Movie {
    id: number;
    title: string;
    year: string;
    poster_url: string;
    vote_average: number;
    user_status?: string;
    user_rating?: number;
}

interface LibraryData {
    user: string;
    to_watch: Movie[];
    watched: Movie[];
    rated_movies: Movie[];
    pagination: {
        page: number;
        page_size: number;
        total_to_watch: number;
        total_watched: number;
        total_rated: number;
    };
}

const TabButton = ({ id, label, count, activeTab, onClick }: {
    id: 'watchlist' | 'watched' | 'rated',
    label: string,
    count: number,
    activeTab: 'watchlist' | 'watched' | 'rated',
    onClick: (id: 'watchlist' | 'watched' | 'rated') => void
}) => (
    <button
        onClick={() => onClick(id)}
        aria-selected={activeTab === id}
        role="tab"
        aria-controls={`${id}-panel`}
        className={`px-6 py-3 rounded-full font-semibold transition-all ${activeTab === id
            ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/30'
            : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
    >
        {label} <span className="ml-2 text-xs bg-black/20 px-2 py-0.5 rounded-full" aria-hidden="true">{count}</span>
    </button>
);

export default function LibraryPage() {
    const [data, setData] = useState<LibraryData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'watchlist' | 'watched' | 'rated'>('watchlist');

    useEffect(() => {
        let ignore = false;

        api.get('/library')
            .then((res) => {
                if (!ignore) {
                    setData(res.data);
                }
            })
            .catch((err) => {
                if (ignore) return;

                console.error(err);
                const status = err?.response?.status;

                if (status === 401 || status === 403) {
                    setError('Please log in to view your library.');
                } else {
                    setError('Failed to load your library. Please try again.');
                }
            })
            .finally(() => {
                if (!ignore) {
                    setLoading(false);
                }
            });

        return () => {
            ignore = true;
        };
    }, []);

    const counts = {
        watchlist: data?.pagination.total_to_watch || 0,
        watched: data?.pagination.total_watched || 0,
        rated: data?.pagination.total_rated || 0
    };

    return (
        <main className="min-h-screen pb-20 max-w-7xl mx-auto px-6 py-10">
            <header className="mb-8">
                <h1 className="text-3xl font-bold">My Library</h1>
            </header>

            {error ? (
                <div className="text-center py-20 bg-red-900/20 rounded-2xl border border-red-500/30">
                    <p className="text-red-400 text-lg">{error}</p>
                </div>
            ) : (
                <>
                    <div className="flex flex-wrap gap-4 mb-10" role="tablist" aria-label="Library Folders">
                        <TabButton id="watchlist" label="Watchlist" count={counts.watchlist} activeTab={activeTab} onClick={setActiveTab} />
                        <TabButton id="watched" label="Watched" count={counts.watched} activeTab={activeTab} onClick={setActiveTab} />
                        <TabButton id="rated" label="Rated" count={counts.rated} activeTab={activeTab} onClick={setActiveTab} />
                    </div>

                    <div
                        id={`${activeTab}-panel`}
                        role="tabpanel"
                        aria-labelledby={activeTab}
                        className="min-h-[400px]"
                    >
                        {loading ? (
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                                {[...Array(10)].map((_, i) => (
                                    <MovieSkeleton key={i} />
                                ))}
                            </div>
                        ) : (
                            <>
                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                                    {activeTab === 'watchlist' && data?.to_watch.map(movie => (
                                        <MovieCard key={movie.id} movie={movie} />
                                    ))}
                                    {activeTab === 'watched' && data?.watched.map(movie => (
                                        <MovieCard key={movie.id} movie={movie} />
                                    ))}
                                    {activeTab === 'rated' && data?.rated_movies.map(movie => (
                                        <div key={movie.id} className="relative group">
                                            <MovieCard movie={movie} />
                                            <div className="absolute top-2 right-2 bg-yellow-500 text-black font-bold px-2 py-1 rounded-md text-xs shadow-md">
                                                Your rating: {movie.user_rating}
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                {((activeTab === 'watchlist' && data?.to_watch.length === 0) ||
                                    (activeTab === 'watched' && data?.watched.length === 0) ||
                                    (activeTab === 'rated' && data?.rated_movies.length === 0)) && (
                                    <div className="text-center py-20 text-gray-500" aria-live="polite">
                                        No movies in this list yet.
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </>
            )}
        </main>
    );
}
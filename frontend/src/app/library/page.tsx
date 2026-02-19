'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import MovieCard from '@/components/MovieCard';

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
    to_watch: Movie[];
    watched: Movie[];
    rated_movies: Movie[];
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
        className={`px-6 py-3 rounded-full font-semibold transition-all ${activeTab === id
            ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/30'
            : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
    >
        {label} <span className="ml-2 text-xs bg-black/20 px-2 py-0.5 rounded-full">{count}</span>
    </button>
);

export default function LibraryPage() {
    const [data, setData] = useState<LibraryData>({ to_watch: [], watched: [], rated_movies: [] });
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'watchlist' | 'watched' | 'rated'>('watchlist');

    useEffect(() => {
        api.get('/library')
            .then((res) => setData(res.data))
            .catch((err) => console.error(err))
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="min-h-screen pb-20 max-w-7xl mx-auto px-6 py-10">
            <h1 className="text-3xl font-bold mb-8">My Library</h1>

            {loading ? (
                <div className="text-center py-20">Loading library...</div>
            ) : (
                <>
                    <div className="flex flex-wrap gap-4 mb-10">
                        <TabButton id="watchlist" label="Watchlist" count={data.to_watch.length} activeTab={activeTab} onClick={setActiveTab} />
                        <TabButton id="watched" label="Watched" count={data.watched.length} activeTab={activeTab} onClick={setActiveTab} />
                        <TabButton id="rated" label="Rated" count={data.rated_movies.length} activeTab={activeTab} onClick={setActiveTab} />
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                        {activeTab === 'watchlist' && data.to_watch.map(movie => (
                            <MovieCard key={movie.id} movie={movie} />
                        ))}

                        {activeTab === 'watched' && data.watched.map(movie => (
                            <MovieCard key={movie.id} movie={movie} />
                        ))}

                        {activeTab === 'rated' && data.rated_movies.map(movie => (
                            <div key={movie.id} className="relative group">
                                <MovieCard movie={movie} />
                                <div className="absolute top-2 right-2 bg-yellow-500 text-black font-bold px-2 py-1 rounded-md text-xs shadow-md">
                                    You&apos;re rated: {movie.user_rating}
                                </div>
                            </div>
                        ))}
                    </div>

                    {((activeTab === 'watchlist' && data.to_watch.length === 0) ||
                        (activeTab === 'watched' && data.watched.length === 0) ||
                        (activeTab === 'rated' && data.rated_movies.length === 0)) && (
                            <div className="text-center py-20 text-gray-500">
                                No movies in this list yet.
                            </div>
                        )}
                </>
            )}
        </div>
    );
}

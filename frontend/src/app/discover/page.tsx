'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import MovieCard from '@/components/MovieCard';
import Link from 'next/link';

interface Movie {
    id: number;
    title: string;
    year: string;
    poster_url: string;
    vote_average: number;
}

export default function DiscoverPage() {
    const [movies, setMovies] = useState<Movie[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get('/discover')
            .then((res) => setMovies(res.data))
            .catch((err) => {
                console.error(err);
                // If 401, redirect? Middleware handles it usually in robust apps, here we just show empty
            })
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="min-h-screen pb-20 max-w-7xl mx-auto px-6 py-10">
            <h1 className="text-3xl font-bold mb-2">Recommended for You</h1>
            <p className="text-gray-400 mb-8">Based on your library and ratings</p>

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
                        <div className="text-center py-20 bg-white/5 rounded-2xl border border-white/10">
                            <p className="text-xl mb-4">No recommendations yet.</p>
                            <p className="text-gray-400 mb-6">Start rating movies or adding them to your library to get suggestions!</p>
                            <Link href="/" className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-full font-semibold transition-colors">
                                Browse Movies
                            </Link>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

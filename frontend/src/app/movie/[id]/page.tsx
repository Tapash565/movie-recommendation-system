'use client';

import { useEffect, useState, use } from 'react';
import api from '@/lib/api';
import MovieCard from '@/components/MovieCard';
import Image from 'next/image';

interface MovieDetail {
    id: number;
    title: string;
    year: string;
    poster_url: string;
    vote_average: number;
    vote_count: number;
    overview: string;
    genres: string[];
    cast: string[];
    crew: string[];
    keywords: string[];
    runtime: number;
    recommendations: MovieDetail[];
    bookmark_status: string | null;
    user_rating: number | null;
}

export default function MoviePage({ params }: { params: Promise<{ id: string }> }) {
    // Unwrap params using React.use()
    const { id } = use(params);
    const [movie, setMovie] = useState<MovieDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [localRating, setLocalRating] = useState<number>(0);

    useEffect(() => {
        api.get(`/movies/${id}`)
            .then((res) => {
                setMovie(res.data);
                setLocalRating(res.data.user_rating || 0);
            })
            .catch((err) => console.error(err))
            .finally(() => setLoading(false));
    }, [id]);


    const handleBookmark = async (status: string) => {
        if (!movie) return;
        // Optimistic update
        const oldStatus = movie.bookmark_status;
        setMovie({ ...movie, bookmark_status: status });

        try {
            if (status === 'remove') {
                await api.post('/remove_bookmark', { movie_id: movie.id });
                setMovie(prev => prev ? { ...prev, bookmark_status: null } : null);
            } else {
                await api.post('/bookmark', { movie_id: movie.id, movie_title: movie.title, status });
            }
        } catch (error) {
            console.error('Bookmark failed', error);
            setMovie(prev => prev ? { ...prev, bookmark_status: oldStatus } : null);
            alert("Please login to bookmark movies");
        }
    };

    const handleRate = async (rating: number) => {
        if (!movie) return;
        const oldRating = movie.user_rating;
        setMovie({ ...movie, user_rating: rating });
        try {
            await api.post('/rate', { movie_id: movie.id, movie_title: movie.title, rating });
        } catch (error) {
            console.error('Rating failed', error);
            setMovie(prev => prev ? { ...prev, user_rating: oldRating } : null);
            alert("Please login to rate movies");
        }
    };

    if (loading) return <div className="min-h-screen text-center pt-20">Loading...</div>;
    if (!movie) return <div className="min-h-screen text-center pt-20">Movie not found</div>;

    return (
        <div className="min-h-screen pb-20">
            {/* Backdrop / Header */}
            <div className="relative w-full h-[40vh] md:h-[50vh] lg:h-[60vh]">
                <div className="absolute inset-0 bg-linear-to-t from-background via-background/80 to-transparent z-10"></div>
                {/* We use poster as backdrop for now (blurred) */}
                <Image
                    src={movie.poster_url}
                    alt={movie.title}
                    fill
                    className="object-cover opacity-50 blur-sm"
                />

                <div className="absolute bottom-0 left-0 w-full z-20 p-6 md:p-10 max-w-7xl mx-auto flex flex-col md:flex-row gap-8 items-end">
                    <div className="relative w-48 h-72 rounded-xl overflow-hidden shadow-2xl border-4 border-white/10 hidden md:block">
                        <Image src={movie.poster_url} alt={movie.title} fill className="object-cover" />
                    </div>
                    <div className="flex-1 mb-4">
                        <h1 className="text-4xl md:text-6xl font-bold text-white mb-2">{movie.title}</h1>
                        <div className="flex flex-wrap items-center gap-4 text-gray-300 text-lg">
                            <span>{movie.year}</span>
                            <span>•</span>
                            <span>{movie.runtime} min</span>
                            <span>•</span>
                            <span className="flex items-center text-yellow-400 font-bold">★ {movie.vote_average.toFixed(1)}</span>
                        </div>
                        <div className="flex gap-2 mt-4 flex-wrap">
                            {movie.genres.slice(0, 3).map(g => (
                                <span key={g} className="px-3 py-1 bg-white/10 rounded-full text-sm backdrop-blur-md">{g}</span>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-6 py-10 grid grid-cols-1 md:grid-cols-3 gap-10">
                <div className="md:col-span-2 space-y-10">
                    <section>
                        <h2 className="text-2xl font-bold mb-4">Overview</h2>
                        <p className="text-gray-300 leading-relaxed text-lg">{movie.overview}</p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold mb-4">Cast</h2>
                        <div className="flex gap-4 overflow-x-auto pb-4">
                            {movie.cast.slice(0, 10).map((actor, i) => (
                                <div key={i} className="min-w-[120px] bg-white/5 p-3 rounded-xl text-center">
                                    <p className="text-sm font-medium">{actor}</p>
                                </div>
                            ))}
                        </div>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold mb-6">Recommendations</h2>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                            {movie.recommendations.map(rec => (
                                <MovieCard key={rec.id} movie={rec} />
                            ))}
                        </div>
                    </section>
                </div>

                <div className="md:col-span-1 space-y-6">
                    <div className="glass-panel p-6">
                        <h3 className="text-xl font-bold mb-4">Your Action</h3>
                        <div className="flex flex-col gap-3">
                            <button
                                onClick={() => handleBookmark('watched')}
                                className={`w-full py-3 rounded-xl font-semibold transition-colors touch-target ${movie.bookmark_status === 'watched' ? 'bg-green-600 text-white' : 'bg-gray-700 hover:bg-gray-600'}`}
                            >
                                {movie.bookmark_status === 'watched' ? '✓ Watched' : 'Mark as Watched'}
                            </button>
                            <button
                                onClick={() => handleBookmark('to_watch')}
                                className={`w-full py-3 rounded-xl font-semibold transition-colors ${movie.bookmark_status === 'to_watch' ? 'bg-blue-600 text-white' : 'bg-gray-700 hover:bg-gray-600'}`}
                            >
                                {movie.bookmark_status === 'to_watch' ? '✓ Watchlist' : 'Add to Watchlist'}
                            </button>
                            {movie.bookmark_status && (
                                <button
                                    onClick={() => handleBookmark('remove')}
                                    className="text-red-400 text-sm hover:underline mt-2 text-center"
                                >
                                    Remove from Library
                                </button>
                            )}
                        </div>
                    </div>

                    <div className="glass-panel p-6">
                        <h3 className="text-xl font-bold mb-4">Rate this Movie</h3>

                        <div className="space-y-4">
                            {/* Visual Rating Display */}
                            <div className="text-center">
                                <div className="text-5xl font-bold text-yellow-400">
                                    {localRating}
                                </div>
                                <div className="text-gray-400 text-sm">out of 10</div>
                            </div>

                            {/* Slider Input */}
                            <div className="relative">
                                <input
                                    type="range"
                                    min="0"
                                    max="10"
                                    step="0.5"
                                    value={localRating}
                                    onChange={(e) => setLocalRating(parseFloat(e.target.value))}
                                    onPointerUp={(e) => handleRate(parseFloat((e.target as HTMLInputElement).value))}
                                    onMouseUp={(e) => handleRate(parseFloat((e.target as HTMLInputElement).value))}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                                    style={{
                                        background: `linear-gradient(to right, #facc15 0%, #facc15 ${(localRating / 10) * 100}%, #374151 ${(localRating / 10) * 100}%, #374151 100%)`
                                    }}
                                />

                                {/* Scale Labels */}
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>0</span>
                                    <span>2.5</span>
                                    <span>5</span>
                                    <span>7.5</span>
                                    <span>10</span>
                                </div>
                            </div>

                            {/* Helper Text */}
                            <p className="text-center text-gray-400 text-sm">
                                {localRating > 0 ?
                                    `You rated this movie ${localRating}/10` :
                                    'Slide to rate'
                                }
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

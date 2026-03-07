'use client';

import { useEffect, useState, use } from 'react';
import api from '@/lib/api';
import MovieRow from '@/components/MovieRow';
import Image from 'next/image';
import { motion } from 'framer-motion';

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
    backdrop_url?: string;
}

export default function MoviePage({ params }: { params: Promise<{ id: string }> }) {
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

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-pulse text-white">Loading...</div>
            </div>
        );
    }

    if (!movie) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-white">Movie not found</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen pb-10">
            {/* Hero/Backdrop Section - Netflix Style */}
            <div className="relative w-full h-[40vh] sm:h-[45vh] md:h-[50vh] lg:h-[60vh]">
                {/* Backdrop Image */}
                <div className="absolute inset-0">
                    <Image
                        src={movie.backdrop_url || movie.poster_url}
                        alt={movie.title}
                        fill
                        priority
                        className="object-cover"
                        sizes="100vw"
                    />
                    <div className="absolute inset-0 hero-gradient" />
                </div>

                {/* Content Overlay */}
                <div className="absolute bottom-0 left-0 right-0 p-4 sm:p-6 md:p-8 max-w-7xl mx-auto">
                    <div className="flex flex-col md:flex-row gap-4 sm:gap-6 md:gap-8 lg:gap-10 items-end">
                        {/* Poster - Hidden on mobile */}
                        <div className="hidden md:block relative w-32 lg:w-40 flex-shrink-0">
                            <div className="aspect-[2/3] rounded-lg overflow-hidden card-shadow">
                                <Image
                                    src={movie.poster_url}
                                    alt={movie.title}
                                    fill
                                    className="object-cover"
                                />
                            </div>
                        </div>

                        {/* Info */}
                        <div className="flex-1">
                            <motion.h1
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-2 sm:mb-3"
                            >
                                {movie.title}
                            </motion.h1>

                            <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-gray-300 text-sm mb-3 sm:mb-4">
                                <span className="bg-white/20 backdrop-blur-sm px-2 py-0.5 rounded text-xs sm:text-sm">{movie.year}</span>
                                <span className="text-xs sm:text-sm">{movie.runtime} min</span>
                                <span className="flex items-center text-yellow-400 font-bold text-sm">
                                    ★ {movie.vote_average.toFixed(1)}
                                </span>
                            </div>

                            <div className="flex flex-wrap gap-2 mb-4 sm:mb-6">
                                {movie.genres.slice(0, 3).map((genre) => (
                                    <span
                                        key={genre}
                                        className="bg-white/10 backdrop-blur-sm px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm text-gray-300"
                                    >
                                        {genre}
                                    </span>
                                ))}
                            </div>

                            {/* Action Buttons - Netflix Style */}
                            <div className="flex flex-wrap gap-2 sm:gap-3">
                                <button
                                    onClick={() => handleBookmark(movie.bookmark_status === 'watched' ? 'remove' : 'watched')}
                                    className={`px-4 sm:px-6 py-2 sm:py-2.5 rounded font-semibold flex items-center gap-2 transition-all duration-200 ${
                                        movie.bookmark_status === 'watched'
                                            ? 'bg-green-600 text-white'
                                            : 'bg-white text-black hover:bg-gray-200 hover:scale-105'
                                    }`}
                                >
                                    {movie.bookmark_status === 'watched' ? (
                                        <>
                                            <svg className="w-4 sm:w-5 h-4 sm:h-5" fill="currentColor" viewBox="0 0 24 24">
                                                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                                            </svg>
                                            <span className="text-sm sm:text-base">Watched</span>
                                        </>
                                    ) : (
                                        <>
                                            <svg className="w-4 sm:w-5 h-4 sm:h-5" fill="currentColor" viewBox="0 0 24 24">
                                                <path d="M8 5v14l11-7z" />
                                            </svg>
                                            <span className="text-sm sm:text-base">Play</span>
                                        </>
                                    )}
                                </button>
                                <button
                                    onClick={() => handleBookmark(movie.bookmark_status === 'to_watch' ? 'remove' : 'to_watch')}
                                    className={`px-4 sm:px-6 py-2 sm:py-2.5 rounded font-semibold flex items-center gap-2 transition-all duration-200 ${
                                        movie.bookmark_status === 'to_watch'
                                            ? 'bg-[#E50914] text-white'
                                            : 'bg-white/20 backdrop-blur-sm text-white hover:bg-white/30'
                                    }`}
                                >
                                    <svg className="w-4 sm:w-5 h-4 sm:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                                    </svg>
                                    <span className="text-sm sm:text-base">{movie.bookmark_status === 'to_watch' ? 'In My List' : 'My List'}</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
                    {/* Left Column - Overview & Details */}
                    <div className="lg:col-span-2 space-y-6 sm:space-y-8">
                        {/* Overview */}
                        <section>
                            <h2 className="text-lg sm:text-xl font-bold mb-3 sm:mb-4 text-white">Overview</h2>
                            <p className="text-gray-300 leading-relaxed text-sm sm:text-base">{movie.overview}</p>
                        </section>

                        {/* Quick Info */}
                        {movie.cast.length > 0 && (
                            <section className="text-sm text-gray-400">
                                <span className="text-gray-500">Cast:</span>{' '}
                                <span className="text-gray-300">{movie.cast.slice(0, 3).join(', ')}</span>
                            </section>
                        )}

                        {/* Recommendations - Horizontal Row */}
                        {movie.recommendations && movie.recommendations.length > 0 && (
                            <MovieRow title="More Like This" movies={movie.recommendations} />
                        )}
                    </div>

                    {/* Right Column - Actions */}
                    <div className="space-y-4 sm:space-y-6">
                        {/* Rating Card */}
                        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-4 sm:p-6">
                            <h3 className="text-base sm:text-lg font-bold mb-3 sm:mb-4 text-white">Rate this movie</h3>

                            <div className="text-center mb-3 sm:mb-4">
                                <div className="text-3 sm:text-4xl font-bold text-yellow-400">
                                    {localRating > 0 ? localRating : '-'}
                                </div>
                                <div className="text-gray-500 text-xs sm:text-sm">out of 10</div>
                            </div>

                            <div className="relative mb-3 sm:mb-4">
                                <input
                                    type="range"
                                    min="0"
                                    max="10"
                                    step="0.5"
                                    value={localRating}
                                    onChange={(e) => setLocalRating(parseFloat(e.target.value))}
                                    onPointerUp={(e) => handleRate(parseFloat((e.target as HTMLInputElement).value))}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                                    style={{
                                        background: `linear-gradient(to right, #facc15 0%, #facc15 ${(localRating / 10) * 100}%, #374151 ${(localRating / 10) * 100}%, #374151 100%)`
                                    }}
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>0</span>
                                    <span>5</span>
                                    <span>10</span>
                                </div>
                            </div>

                            <p className="text-center text-gray-400 text-xs sm:text-sm">
                                {localRating > 0 ? `You rated: ${localRating}/10` : 'Slide to rate'}
                            </p>
                        </div>

                        {/* Bookmark Actions */}
                        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-4 sm:p-6 space-y-3">
                            <button
                                onClick={() => handleBookmark('watched')}
                                className={`w-full py-2.5 sm:py-3 rounded-lg font-semibold transition-colors text-sm sm:text-base ${
                                    movie.bookmark_status === 'watched'
                                        ? 'bg-green-600 text-white'
                                        : 'bg-white/10 hover:bg-white/20 text-white'
                                }`}
                            >
                                {movie.bookmark_status === 'watched' ? '✓ Watched' : 'Mark as Watched'}
                            </button>
                            <button
                                onClick={() => handleBookmark('to_watch')}
                                className={`w-full py-2.5 sm:py-3 rounded-lg font-semibold transition-colors text-sm sm:text-base ${
                                    movie.bookmark_status === 'to_watch'
                                        ? 'bg-[#E50914] text-white'
                                        : 'bg-white/10 hover:bg-white/20 text-white'
                                }`}
                            >
                                {movie.bookmark_status === 'to_watch' ? '✓ In My List' : 'Add to My List'}
                            </button>
                            {movie.bookmark_status && (
                                <button
                                    onClick={() => handleBookmark('remove')}
                                    className="w-full text-red-400 text-xs sm:text-sm hover:underline py-2"
                                >
                                    Remove from library
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

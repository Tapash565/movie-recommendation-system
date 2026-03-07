'use client';

import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { useState, useCallback } from 'react';

interface Movie {
    id: number;
    title: string;
    year: string;
    poster_url: string;
    vote_average: number;
}

interface MovieCardProps {
    movie: Movie;
    showAIMatch?: boolean;
    priority?: boolean;
}

export default function MovieCard({ movie, showAIMatch = false, priority = false }: MovieCardProps) {
    const [isLoaded, setIsLoaded] = useState(false);
    const [isHovered, setIsHovered] = useState(false);

    const handleImageLoad = useCallback(() => {
        setIsLoaded(true);
    }, []);

    const handleImageError = useCallback(() => {
        setIsLoaded(true);
    }, []);

    return (
        <motion.article
            className="group relative flex-shrink-0 w-[100px] xs:w-[120px] sm:w-[140px] md:w-[160px] lg:w-[180px] xl:w-[200px] cursor-pointer"
            whileHover={{ scale: 1.08, zIndex: 10 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            <Link
                href={`/movie/${movie.id}`}
                aria-label={`View details for ${movie.title} (${movie.year})`}
                className="block"
            >
                {/* Poster Container */}
                <div className="relative aspect-[2/3] w-full overflow-hidden rounded-md card-shadow group-hover:card-shadow-hover transition-shadow duration-300">
                    {/* Placeholder/Loading state */}
                    {!isLoaded && (
                        <div className="absolute inset-0 bg-white/10 animate-pulse" />
                    )}

                    <Image
                        src={movie.poster_url}
                        alt={movie.title}
                        fill
                        className={`object-cover transition-all duration-300 ${
                            isLoaded ? 'opacity-100' : 'opacity-0'
                        } ${isHovered ? 'scale-105' : 'scale-100'}`}
                        sizes="(max-width: 480px) 100px, (max-width: 640px) 120px, (max-width: 768px) 140px, (max-width: 1024px) 160px, (max-width: 1280px) 180px, 200px"
                        loading={priority ? 'eager' : 'lazy'}
                        priority={priority}
                        onLoad={handleImageLoad}
                        onError={handleImageError}
                    />

                    {/* Gradient Overlay */}
                    <div className={`absolute inset-0 card-gradient transition-opacity duration-300 ${isHovered ? 'opacity-100' : 'opacity-0'}`} />

                    {/* Rating Badge - Always visible */}
                    <div className="absolute top-2 left-2 bg-black/70 backdrop-blur-sm px-1.5 py-0.5 rounded text-[10px] xs:text-xs font-semibold text-yellow-400 flex items-center gap-0.5">
                        <span>★</span>
                        <span>{movie.vote_average.toFixed(1)}</span>
                    </div>

                    {/* AI Match Badge */}
                    {showAIMatch && (
                        <div className="absolute top-2 right-2 bg-gradient-to-r from-purple-600 to-pink-600 px-1.5 py-0.5 rounded text-[10px] xs:text-xs font-semibold text-white flex items-center gap-0.5">
                            <svg className="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" />
                            </svg>
                            <span className="hidden xs:inline">AI</span>
                        </div>
                    )}

                    {/* Hover Content */}
                    <div className={`absolute inset-0 flex flex-col items-center justify-center transition-opacity duration-300 bg-black/50 ${isHovered ? 'opacity-100' : 'opacity-0'}`}>
                        <span className="bg-white/20 backdrop-blur-md px-3 xs:px-4 py-1.5 xs:py-2 rounded-full text-xs font-semibold text-white border border-white/30">
                            View Details
                        </span>
                    </div>
                </div>

                {/* Movie Title */}
                <div className="mt-2 px-1">
                    <h3 className="text-white text-xs xs:text-sm font-medium truncate group-hover:text-gray-300 transition-colors" title={movie.title}>
                        {movie.title}
                    </h3>
                    <p className="text-gray-500 text-[10px] xs:text-xs">{movie.year}</p>
                </div>
            </Link>
        </motion.article>
    );
}

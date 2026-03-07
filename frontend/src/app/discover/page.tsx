'use client';

import { useEffect, useState, useMemo } from 'react';
import api from '@/lib/api';
import MovieRow from '@/components/MovieRow';
import Link from 'next/link';
import { motion } from 'framer-motion';

interface Movie {
    id: number;
    title: string;
    year: string;
    poster_url: string;
    vote_average: number;
}

function DiscoverSkeleton() {
    const skeleton = useMemo(() => (
        <div className="flex gap-2 sm:gap-3 overflow-hidden px-4 sm:px-0">
            {[...Array(7)].map((_, j) => (
                <div key={j} className="flex-shrink-0 w-[100px] xs:w-[120px] sm:w-[140px] md:w-[160px] lg:w-[180px]">
                    <div className="aspect-[2/3] bg-white/10 rounded-md animate-pulse" />
                    <div className="mt-2 space-y-2">
                        <div className="h-3 sm:h-4 bg-white/10 rounded w-3/4 animate-pulse" />
                        <div className="h-2 sm:h-3 bg-white/10 rounded w-1/4 animate-pulse" />
                    </div>
                </div>
            ))}
        </div>
    ), []);

    return (
        <div className="px-4 sm:px-0 space-y-6 sm:space-y-8">
            <div className="h-6 sm:h-8 w-40 sm:w-48 bg-white/10 rounded animate-pulse" />
            {skeleton}
        </div>
    );
}

export default function DiscoverPage() {
    const [recommended, setRecommended] = useState<Movie[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get('/discover')
            .then((res) => setRecommended(res.data || []))
            .catch((err) => console.error(err))
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="min-h-screen pb-10 pt-16 sm:pt-20 md:pt-24">
            {/* Page Header */}
            <div className="px-4 sm:px-6 md:px-8 mb-6 sm:mb-8">
                <motion.h1
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-2"
                >
                    Discover
                </motion.h1>
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.1 }}
                    className="text-gray-400 text-sm sm:text-base"
                >
                    Based on your library and ratings
                </motion.p>
            </div>

            {loading ? (
                <DiscoverSkeleton />
            ) : recommended.length > 0 ? (
                <div className="px-4 sm:px-0">
                    <MovieRow title="Recommended For You" movies={recommended} showAIMatch={true} />
                </div>
            ) : (
                <div className="px-4 sm:px-6 md:px-8">
                    <div className="text-center py-16 sm:py-20 bg-white/5 rounded-2xl border border-white/10 mx-4 sm:mx-0">
                        <p className="text-lg sm:text-xl mb-4 text-white">No recommendations yet.</p>
                        <p className="text-gray-400 mb-6 max-w-md mx-auto text-sm sm:text-base">
                            Start rating movies or adding them to your library to get personalized suggestions!
                        </p>
                        <Link
                            href="/"
                            className="bg-[#E50914] hover:bg-[#b2070f] text-white px-6 py-3 rounded font-semibold transition-all duration-200 hover:scale-105 inline-block"
                        >
                            Browse Movies
                        </Link>
                    </div>
                </div>
            )}
        </div>
    );
}

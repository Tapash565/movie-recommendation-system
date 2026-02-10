'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';
import Link from 'next/link';

interface Movie {
    id: number;
    title: string;
    poster_url: string;
}

export default function InfiniteMarquee({ movies }: { movies: Movie[] }) {
    // Duplicate movies to create a seamless loop
    const marqueeMovies = [...movies, ...movies, ...movies];

    return (
        <div className="w-full overflow-hidden py-10 bg-black/20 backdrop-blur-sm border-y border-white/5 relative z-20">
            <div className="absolute inset-y-0 left-0 w-32 bg-gradient-to-r from-[#0f172a] to-transparent z-10"></div>
            <div className="absolute inset-y-0 right-0 w-32 bg-gradient-to-l from-[#0f172a] to-transparent z-10"></div>

            <motion.div
                className="flex gap-8 w-max"
                animate={{ x: ["0%", "-33.33%"] }}
                transition={{
                    duration: 30,
                    ease: "linear",
                    repeat: Infinity
                }}
            >
                {marqueeMovies.map((movie, index) => (
                    <Link key={`${movie.id}-${index}`} href={`/movie/${movie.id}`} className="group relative w-48 aspect-[2/3] flex-shrink-0 rounded-xl overflow-hidden border border-white/10 hover:border-cyan-500/50 transition-colors">
                        <Image
                            src={movie.poster_url}
                            alt={movie.title}
                            fill
                            className="object-cover group-hover:scale-110 transition-transform duration-500"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4">
                            <p className="text-white text-sm font-bold truncate">{movie.title}</p>
                        </div>
                    </Link>
                ))}
            </motion.div>
        </div>
    );
}

'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import MovieCard from '@/components/MovieCard';
import { motion } from 'framer-motion';
import StarField from '@/components/StarField';
import TiltCard from '@/components/TiltCard';
import InfiniteMarquee from '@/components/InfiniteMarquee';

interface Movie {
  id: number;
  title: string;
  year: string;
  poster_url: string;
  vote_average: number;
}

export default function Home() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    api.get('/movies/trending')
      .then((res) => setMovies(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1
    }
  };

  return (
    <div className="min-h-screen pb-20 overflow-hidden relative">
      {/* Dynamic Background Elements */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-600/20 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-pink-600/20 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-32 left-1/3 w-96 h-96 bg-blue-600/20 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>
      </div>

      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="relative z-10 m-6 rounded-3xl overflow-hidden shadow-2xl border border-white/10"
      >
        <div className="absolute inset-0 bg-[url('https://image.tmdb.org/t/p/original/uDgy6hyPd82kOHh6I95FLtLnj6p.jpg')] bg-cover bg-center opacity-40"></div>
        <div className="absolute inset-0 bg-gradient-to-t from-[#0f172a] via-[#0f172a]/80 to-transparent"></div>

        <div className="relative z-10 p-10 md:p-24 flex flex-col items-center text-center">
          <motion.h1
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="text-5xl md:text-7xl font-extrabold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 drop-shadow-lg"
          >
            Cinematic Universe
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-xl md:text-2xl text-gray-300 mb-10 max-w-2xl leading-relaxed"
          >
            Dive into a world of endless entertainment. Discover your next obsession with AI-powered recommendations.
          </motion.p>

          <motion.form
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.6 }}
            action="/search"
            className="relative group w-full max-w-xl"
          >
            <div className="absolute -inset-1 bg-gradient-to-r from-pink-600 to-purple-600 rounded-2xl blur opacity-25 group-hover:opacity-75 transition duration-1000 group-hover:duration-200"></div>
            <input
              type="text"
              name="q"
              placeholder="Search for movies..."
              className="relative w-full bg-[#1e293b] border border-white/10 rounded-2xl px-8 py-4 md:py-5 text-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all shadow-xl touch-target"
              value={searchQuery}}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button
              type="submit"
              className="absolute right-4 top-1/2 -translate-y-1/2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white p-3 rounded-xl transition-all shadow-lg hover:shadow-purple-500/25"
              aria-label="Search"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
            </button>
          </motion.form>
        </div>
      </motion.div>


      {/* Marquee Section */}
      {!loading && movies.length > 0 && (
        <div className="mb-16">
          <InfiniteMarquee movies={movies} />
        </div>
      )}

      {/* Trending Section */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 mt-16">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400">
            Trending Now
          </h2>
          <div className="h-1 flex-1 mx-6 bg-gradient-to-r from-white/10 to-transparent rounded-full"></div>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-8">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="aspect-[2/3] bg-gray-800/50 rounded-2xl animate-pulse"></div>
            ))}
          </div>
        ) : (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-8"
          >
            {movies.map((movie) => (
              <motion.div key={movie.id} variants={itemVariants}>
                <MovieCard movie={movie} />
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
}

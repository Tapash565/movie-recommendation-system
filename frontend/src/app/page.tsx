'use client';

import { useEffect, useState, useMemo} from 'react';
import api from '@/lib/api';
import MovieRow from '@/components/MovieRow';
import Image from 'next/image';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';

interface Movie {
  id: number;
  title: string;
  year: string;
  poster_url: string;
  vote_average: number;
  overview?: string;
  backdrop_url?: string;
}

interface FeaturedMovie extends Movie {
  overview: string;
  backdrop_url: string;
  genres?: string[];
}

// Skeleton for hero section
function HeroSkeleton() {
  return (
    <div className="relative h-[60vh] sm:h-[65vh] md:h-[75vh] lg:h-[80vh] w-full overflow-hidden">
      <div className="absolute inset-0 bg-white/5 animate-pulse" />
      <div className="absolute inset-0 hero-gradient" />
      <div className="relative z-10 h-full flex flex-col justify-end pb-12 sm:pb-16 md:pb-20 lg:pb-24 px-section max-w-7xl mx-auto">
        <div className="max-w-lg lg:max-w-xl space-y-4 sm:space-y-5">
          <div className="h-8 sm:h-10 md:h-12 lg:h-14 w-3/4 bg-white/10 rounded animate-pulse" />
          <div className="h-4 sm:h-5 w-full bg-white/10 rounded animate-pulse" />
          <div className="h-4 sm:h-5 w-2/3 bg-white/10 rounded animate-pulse" />
          <div className="flex gap-3 pt-2 sm:pt-4">
            <div className="h-10 sm:h-12 w-28 sm:w-32 bg-white/10 rounded animate-pulse" />
            <div className="h-10 sm:h-12 w-28 sm:w-32 bg-white/10 rounded animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
}

// Contextual row for movies from user's library genres
function GenreBasedRow({ title, genre, excludeIds = [] }: { title: string; genre: string; excludeIds?: number[] }) {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/movies/search', { params: { q: genre, page: 1 } })
      .then((res) => {
        const results = (res.data.movies || []).filter(
          (m: Movie) => !excludeIds.includes(m.id)
        ).slice(0, 12);
        setMovies(results);
      })
      .catch(() => setMovies([]))
      .finally(() => setLoading(false));
  }, [genre, excludeIds.join(',')]);

  if (loading) return null;
  if (movies.length === 0) return null;

  return <MovieRow title={title} movies={movies} />;
}

export default function Home() {
  const [featuredMovie, setFeaturedMovie] = useState<FeaturedMovie | null>(null);
  const [trending, setTrending] = useState<Movie[]>([]);
  const [topRated, setTopRated] = useState<Movie[]>([]);
  const [popular, setPopular] = useState<Movie[]>([]);
  const [recommended, setRecommended] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [showControls, setShowControls] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get('/movies/trending'),
      api.get('/discover').catch(() => ({ data: [] }))
    ])
      .then(([trendingRes, topRatedRes]) => {
        const trendingData = trendingRes.data || [];
        const topRatedData = topRatedRes.data || [];

        setTrending(trendingData);
        setTopRated(topRatedData);

        if (trendingData.length > 0) {
          const sortedByRating = [...trendingData].sort((a, b) => b.vote_average - a.vote_average);
          const featured = sortedByRating[Math.floor(Math.random() * Math.min(5, sortedByRating.length))];
          setFeaturedMovie({
            ...featured,
            overview: featured.overview || 'Discover amazing movies tailored just for you. Start exploring your next favorite film today.',
            backdrop_url: featured.backdrop_url || featured.poster_url
          });
        }
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  // Memoize skeleton rows
  const skeletonRows = useMemo(() => (
    <div className="space-y-8 pt-8">
      {[1, 2, 3].map((i) => (
        <div key={i}>
          <div className="h-6 sm:h-8 w-40 sm:w-48 bg-white/10 rounded mb-3 sm:mb-4 animate-pulse ml-4 sm:ml-0" />
          <div className="flex gap-2 sm:gap-3 overflow-hidden px-4 sm:px-0">
            {[...Array(7)].map((_, j) => (
              <div key={j} className="flex-shrink-0 w-[100px] xs:w-[120px] sm:w-[140px] md:w-[160px] lg:w-[180px]">
                <div className="aspect-[2/3] bg-white/10 rounded-md animate-pulse" />
                <div className="h-3 sm:h-4 w-20 sm:w-24 bg-white/10 rounded mt-2 animate-pulse" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  ), []);

  // Get all movie IDs to exclude from genre recommendations
  const allMovieIds = useMemo(() => {
    return [trending, topRated, popular, recommended].flatMap(list => list.map(m => m.id));
  }, [trending, topRated, popular, recommended]);

  return (
    <div className="min-h-screen pb-10">
      {/* Hero Section - Netflix Style */}
      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div
            key="hero-skeleton"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <HeroSkeleton />
          </motion.div>
        ) : featuredMovie ? (
          <motion.section
            key="hero-content"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6 }}
            className="relative h-[60vh] sm:h-[65vh] md:h-[75vh] lg:h-[80vh] w-full overflow-hidden"
            onMouseEnter={() => setShowControls(true)}
            onMouseLeave={() => setShowControls(false)}
          >
            {/* Background Image */}
            <div className="absolute inset-0">
              <Image
                src={featuredMovie.backdrop_url}
                alt={featuredMovie.title}
                fill
                priority
                className="object-cover"
                sizes="100vw"
              />
              <div className="absolute inset-0 hero-gradient" />
            </div>

            {/* Hero Content */}
            <div className="relative z-10 h-full flex flex-col justify-end pb-12 sm:pb-16 md:pb-20 lg:pb-24 px-section max-w-7xl mx-auto">
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 }}
                className="max-w-lg lg:max-w-xl"
              >
                <h1 className="text-hero font-bold text-white mb-3 sm:mb-4 drop-shadow-lg leading-tight">
                  {featuredMovie.title}
                </h1>
                <p className="text-gray-300 text-sm sm:text-base md:text-lg mb-5 sm:mb-6 line-clamp-2 sm:line-clamp-3">
                  {featuredMovie.overview}
                </p>
                <div className="flex flex-wrap gap-2 sm:gap-3">
                  <Link
                    href={`/movie/${featuredMovie.id}`}
                    className="bg-white text-black hover:bg-gray-200 px-5 sm:px-6 py-2.5 sm:py-3 rounded font-semibold flex items-center gap-2 transition-all duration-200 hover:scale-105"
                  >
                    <svg className="w-4 sm:w-5 h-4 sm:h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                    <span className="text-sm sm:text-base">Play</span>
                  </Link>
                  <Link
                    href={`/movie/${featuredMovie.id}`}
                    className="bg-white/20 backdrop-blur-sm text-white hover:bg-white/30 px-5 sm:px-6 py-2.5 sm:py-3 rounded font-semibold flex items-center gap-2 transition-all duration-200"
                  >
                    <svg className="w-4 sm:w-5 h-4 sm:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                    </svg>
                    <span className="text-sm sm:text-base">More Info</span>
                  </Link>
                </div>
              </motion.div>
            </div>
          </motion.section>
        ) : null}
      </AnimatePresence>

      {/* Movie Rows */}
      <div className="relative z-10 -mt-20 sm:-mt-24 md:-mt-32 lg:-mt-40 px-0 pb-6 sm:pb-8">
        {loading ? (
          skeletonRows
        ) : (
          <div className="space-y-2 sm:space-y-4">
            {/* Personalized Recommendations - AI Match */}
            {recommended.length > 0 && (
              <MovieRow title="Recommended For You" movies={recommended} showAIMatch={true} />
            )}

            {/* Trending */}
            {trending.length > 0 && (
              <MovieRow title="Trending Now" movies={trending} />
            )}

            {/* Genre-based contextual rows */}
            <GenreBasedRow title="Action & Adventure" genre="action" excludeIds={allMovieIds} />
            <GenreBasedRow title="Drama Films" genre="drama" excludeIds={allMovieIds} />

            {/* Top Rated */}
            {topRated.length > 0 && (
              <MovieRow title="Top Rated" movies={topRated} />
            )}

            {/* Popular */}
            {popular.length > 0 && (
              <MovieRow title="Popular on MovieMind" movies={popular} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

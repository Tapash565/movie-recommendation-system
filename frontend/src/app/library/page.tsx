'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import MovieRow from '@/components/MovieRow';

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

const TabButton = ({ id, label, activeTab, onClick }: {
    id: 'watchlist' | 'watched' | 'rated',
    label: string,
    activeTab: 'watchlist' | 'watched' | 'rated',
    onClick: (id: 'watchlist' | 'watched' | 'rated') => void
}) => (
    <button
        onClick={() => onClick(id)}
        className={`px-4 sm:px-5 py-2 rounded-full font-medium text-sm transition-all duration-200 ${
            activeTab === id
                ? 'bg-[#E50914] text-white shadow-lg shadow-red-900/30'
                : 'bg-white/10 text-gray-400 hover:bg-white/20 hover:text-white'
        }`}
    >
        {label}
    </button>
);

export default function LibraryPage() {
    const [data, setData] = useState<LibraryData | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'watchlist' | 'watched' | 'rated'>('watchlist');
    const [watchlistPage, setWatchlistPage] = useState(1);
    const [watchedPage, setWatchedPage] = useState(1);
    const [ratedPage, setRatedPage] = useState(1);

    const getCurrentPage = (): number => {
        switch (activeTab) {
            case 'watchlist':
                return watchlistPage;
            case 'watched':
                return watchedPage;
            case 'rated':
                return ratedPage;
            default:
                return 1;
        }
    };

    const setCurrentPage = (page: number) => {
        switch (activeTab) {
            case 'watchlist':
                setWatchlistPage(page);
                break;
            case 'watched':
                setWatchedPage(page);
                break;
            case 'rated':
                setRatedPage(page);
                break;
        }
    };

    const getTotalItems = (): number => {
        if (!data) return 0;

        switch (activeTab) {
            case 'watchlist':
                return data.pagination.total_to_watch;
            case 'watched':
                return data.pagination.total_watched;
            case 'rated':
                return data.pagination.total_rated;
            default:
                return 0;
        }
    };

    useEffect(() => {
        const currentPage = getCurrentPage();

        setLoading(true);
        api.get(`/library?page=${currentPage}`)
            .then((res) => setData(res.data))
            .catch((err) => console.error(err))
            .finally(() => setLoading(false));
    }, [activeTab, watchlistPage, watchedPage, ratedPage]);

    const getMovies = (): Movie[] => {
        if (!data) return [];
        switch (activeTab) {
            case 'watchlist': return data.to_watch;
            case 'watched': return data.watched;
            case 'rated': return data.rated_movies;
            default: return [];
        }
    };

    const getTitle = (): string => {
        switch (activeTab) {
            case 'watchlist': return 'My Watchlist';
            case 'watched': return 'Watched';
            case 'rated': return 'My Ratings';
            default: return '';
        }
    };

    const currentPage = getCurrentPage();
    const totalItems = getTotalItems();
    const pageSize = data?.pagination.page_size ?? 1;
    const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

    return (
        <main className="min-h-screen pb-10 pt-16 sm:pt-20 md:pt-24">
            {/* Header */}
            <div className="px-4 sm:px-6 md:px-8 mb-6 sm:mb-8">
                <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-4 sm:mb-6">My List</h1>

                {/* Tabs */}
                <div className="flex flex-wrap gap-2 sm:gap-3">
                    <TabButton
                        id="watchlist"
                        label={`Watchlist (${data?.pagination.total_to_watch || 0})`}
                        activeTab={activeTab}
                        onClick={setActiveTab}
                    />
                    <TabButton
                        id="watched"
                        label={`Watched (${data?.pagination.total_watched || 0})`}
                        activeTab={activeTab}
                        onClick={setActiveTab}
                    />
                    <TabButton
                        id="rated"
                        label={`Rated (${data?.pagination.total_rated || 0})`}
                        activeTab={activeTab}
                        onClick={setActiveTab}
                    />
                </div>
            </div>

            {/* Content */}
            <div className="px-4 sm:px-0">
                {loading ? (
                    <div className="flex gap-2 sm:gap-3 overflow-hidden px-4 sm:px-0">
                        {[...Array(7)].map((_, i) => (
                            <div key={i} className="flex-shrink-0 w-[100px] xs:w-[120px] sm:w-[140px] md:w-[160px] lg:w-[180px]">
                                <div className="aspect-[2/3] bg-white/10 rounded-md animate-pulse" />
                                <div className="mt-2 space-y-2">
                                    <div className="h-3 sm:h-4 bg-white/10 rounded w-3/4 animate-pulse" />
                                    <div className="h-2 sm:h-3 bg-white/10 rounded w-1/4 animate-pulse" />
                                </div>
                            </div>
                        ))}
                    </div>
                ) : getMovies().length > 0 ? (
                    <div className="space-y-6">
                        <MovieRow title={getTitle()} movies={getMovies()} />

                        {totalPages > 1 && (
                            <div className="flex items-center justify-center gap-3 px-4">
                                <button
                                    onClick={() => setCurrentPage(currentPage - 1)}
                                    disabled={currentPage === 1}
                                    className="px-4 py-2 rounded-full bg-white/10 text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-white/20 transition"
                                >
                                    Previous
                                </button>

                                <span className="text-sm text-gray-300">
                                    Page {currentPage} of {totalPages}
                                </span>

                                <button
                                    onClick={() => setCurrentPage(currentPage + 1)}
                                    disabled={currentPage === totalPages}
                                    className="px-4 py-2 rounded-full bg-white/10 text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-white/20 transition"
                                >
                                    Next
                                </button>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="text-center py-16 sm:py-20 text-gray-500 px-4">
                        No movies in this list yet.
                    </div>
                )}
            </div>
        </main>
    );
}

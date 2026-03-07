'use client';

import { useRef, useState, useEffect, useCallback, useMemo } from 'react';
import MovieCard from './MovieCard';

interface Movie {
    id: number;
    title: string;
    year: string;
    poster_url: string;
    vote_average: number;
}

interface MovieRowProps {
    title: string;
    movies: Movie[];
    showAIMatch?: boolean;
}

export default function MovieRow({ title, movies, showAIMatch = false }: MovieRowProps) {
    const scrollRef = useRef<HTMLDivElement>(null);
    const sectionRef = useRef<HTMLDivElement>(null);
    const [isVisible, setIsVisible] = useState(false);
    const [hasLoaded, setHasLoaded] = useState(false);
    const [canScrollLeft, setCanScrollLeft] = useState(false);
    const [canScrollRight, setCanScrollRight] = useState(true);

    // Intersection Observer to lazy load when row comes into view
    useEffect(() => {
        if (!sectionRef.current) return;

        const observer = new IntersectionObserver(
            (entries) => {
                const [entry] = entries;
                if (entry.isIntersecting && !hasLoaded) {
                    setIsVisible(true);
                    setHasLoaded(true);
                    observer.unobserve(entry.target);
                }
            },
            {
                rootMargin: '150px',
                threshold: 0.1
            }
        );

        observer.observe(sectionRef.current);

        return () => observer.disconnect();
    }, [hasLoaded]);

    // Handle scroll position for arrow visibility
    const updateScrollButtons = useCallback(() => {
        if (!scrollRef.current) return;
        const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
        setCanScrollLeft(scrollLeft > 0);
        setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 20);
    }, []);

    useEffect(() => {
        const el = scrollRef.current;
        if (!el) return;

        el.addEventListener('scroll', updateScrollButtons);
        // Initial check
        setTimeout(updateScrollButtons, 100);

        return () => el.removeEventListener('scroll', updateScrollButtons);
    }, [updateScrollButtons]);

    // Smooth scroll
    const scroll = useCallback((direction: 'left' | 'right') => {
        if (!scrollRef.current) return;

        const cardWidth = 220;
        const scrollAmount = cardWidth * 2;

        scrollRef.current.scrollBy({
            left: direction === 'left' ? -scrollAmount : scrollAmount,
            behavior: 'smooth'
        });
    }, []);

    // Keyboard navigation
    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (e.key === 'ArrowLeft') {
            scroll('left');
        } else if (e.key === 'ArrowRight') {
            scroll('right');
        }
    }, [scroll]);
    
    // Memoize skeleton items
    const skeletonItems = useMemo(() => (
        [...Array(7)].map((_, i) => (
            <div
            key={`skeleton-${i}`}
            className="flex-shrink-0 w-[100px] xs:w-[120px] sm:w-[140px] md:w-[160px] lg:w-[180px] xl:w-[200px]"
            >
                <div className="aspect-[2/3] bg-white/10 rounded-md animate-pulse" />
                <div className="mt-2 space-y-2 px-1">
                    <div className="h-3 xs:h-4 bg-white/10 rounded w-3/4 animate-pulse" />
                    <div className="h-2 xs:h-3 bg-white/10 rounded w-1/4 animate-pulse" />
                </div>
            </div>
        ))
    ), []);

    if (movies.length === 0) return null;

    const rowId = title.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');

    return (
        <section
            ref={sectionRef}
            className="section-spacing"
            aria-labelledby={`row-${rowId}`}
        >
            {/* Section Header */}
            <div className="flex items-center gap-3 sm:gap-4 mb-3 sm:mb-4 px-4 sm:px-0">
                <h2 id={`row-${rowId}`} className="text-section-title font-bold text-white whitespace-nowrap">
                    {title}
                </h2>
                <div className="h-px flex-1 bg-gradient-to-r from-white/20 to-transparent min-w-[20px]" />
            </div>

            {/* Scrollable Row */}
            <div
                className="relative group"
                onKeyDown={handleKeyDown}
                tabIndex={0}
                role="region"
                aria-label={`${title} movies, use arrow keys to scroll`}
            >
                {/* Left Navigation Button */}
                {canScrollLeft && (
                    <button
                        onClick={() => scroll('left')}
                        className="absolute left-0 top-0 bottom-0 z-10 w-10 sm:w-12 bg-black/60 hover:bg-black/80 transition-all duration-300 flex items-center justify-center opacity-100"
                        aria-label={`Scroll ${title} left`}
                        type="button"
                    >
                    <svg className="w-5 sm:w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
                    </svg>
                </button>
                )}

                {/* Movies Container with scroll snapping */}
                <div
                    ref={scrollRef}
                    className="flex gap-2 sm:gap-3 overflow-x-auto scroll-row no-scrollbar px-4 sm:px-0"
                    style={{ scrollBehavior: 'smooth' }}
                >
                    {/* Show skeleton if not yet visible */}
                    {!isVisible ? skeletonItems : (
                        movies.map((movie, index) => (
                            <MovieCard
                                key={movie.id}
                                movie={movie}
                                showAIMatch={showAIMatch}
                                priority={index < 4}
                            />
                        ))
                    )}
                </div>

                {/* Right Navigation Button */}
                {canScrollRight && (
                    <button
                        onClick={() => scroll('right')}
                        className="absolute right-0 top-0 bottom-0 z-10 w-10 sm:w-12 bg-black/60 hover:bg-black/80 transition-all duration-300 flex items-center justify-center opacity-100"
                        aria-label={`Scroll ${title} right`}
                        type="button"
                    >
                    <svg className="w-5 sm:w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                    </svg>
                </button>
                )}
            </div>
        </section>
    );
}

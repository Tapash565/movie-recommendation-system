'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState, useCallback } from 'react';
import { useAuth, signOut } from '@/lib/auth';
import MobileSidebar from './MobileSidebar';

export default function Navbar() {
    const pathname = usePathname();
    const { user, loading } = useAuth();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isScrolled, setIsScrolled] = useState(false);

    const displayName = user?.email?.split('@')[0] || user?.displayName || 'Guest';

    // Handle scroll state for blur effect
    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 30);
        };

        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    useEffect(() => {
        if (isSidebarOpen) {
            document.body.classList.add('sidebar-open');
        } else {
            document.body.classList.remove('sidebar-open');
        }
        return () => document.body.classList.remove('sidebar-open');
    }, [isSidebarOpen]);

    const handleLogout = async () => {
        const result = await signOut();
        if (result.error) {
            console.error('Logout failed', result.error);
        } else {
            window.location.href = '/';
        }
    };

    const handleCloseSidebar = useCallback(() => {
        setIsSidebarOpen(false);
    }, []);

    const navLinkClass = (path: string) =>
        `text-sm font-medium transition-all duration-200 ${
            pathname === path
                ? 'text-white font-semibold'
                : 'text-gray-300 hover:text-white'
        }`;

    return (
        <>
            <MobileSidebar
                isOpen={isSidebarOpen}
                onClose={handleCloseSidebar}
                user={user}
                onLogout={handleLogout}
            />

            <nav
                className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
                    isScrolled
                        ? 'bg-black/90 backdrop-blur-lg border-b border-white/5 shadow-lg'
                        : 'bg-gradient-to-b from-black/95 via-black/80 to-transparent'
                }`}
            >
                <div className="px-3 sm:px-4 md:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-14 sm:h-16 md:h-20">
                        {/* Left - Logo & Nav Links */}
                        <div className="flex items-center gap-4 sm:gap-6 md:gap-8 lg:gap-10">
                            {/* Hamburger - Mobile */}
                            <button
                                onClick={() => setIsSidebarOpen(true)}
                                className="md:hidden p-2 hover:bg-white/10 rounded-lg transition-colors"
                                aria-label="Open menu"
                            >
                                <svg className="w-5 h-5 sm:w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                </svg>
                            </button>

                            {/* Logo */}
                            <Link href="/" className="text-lg sm:text-xl md:text-2xl font-bold text-[#E50914] tracking-tight">
                                MovieMind
                            </Link>

                            {/* Desktop Nav Links */}
                            <div className="hidden md:flex items-center gap-5 lg:gap-6">
                                <Link href="/" className={navLinkClass('/')}>
                                    Home
                                </Link>
                                <Link href="/search" className={navLinkClass('/search')}>
                                    Search
                                </Link>
                                {user && (
                                    <>
                                        <Link href="/discover" className={navLinkClass('/discover')}>
                                            Discover
                                        </Link>
                                        <Link href="/library" className={navLinkClass('/library')}>
                                            My List
                                        </Link>
                                    </>
                                )}
                            </div>
                        </div>

                        {/* Right - Search & User */}
                        <div className="flex items-center gap-2 sm:gap-3 md:gap-4">
                            {/* Search Icon */}
                            <Link
                                href="/search"
                                className="p-2 sm:p-2.5 hover:bg-white/10 rounded-full transition-all duration-200"
                                aria-label="Search"
                            >
                                <svg className="w-4 sm:w-5 h-4 sm:h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </Link>

                            {/* User Menu */}
                            {!loading && (
                                user ? (
                                    <div className="flex items-center gap-2 sm:gap-3 md:gap-4">
                                        <Link
                                            href="/profile"
                                            className="w-7 sm:w-8 h-7 sm:h-8 bg-[#E50914] rounded-full flex items-center justify-center text-white font-semibold text-xs sm:text-sm hover:ring-2 hover:ring-white/50 hover:ring-offset-2 hover:ring-offset-black transition-all"
                                        >
                                            {displayName.charAt(0).toUpperCase()}
                                        </Link>
                                        <button
                                            onClick={handleLogout}
                                            className="hidden lg:block text-gray-400 hover:text-white text-sm transition-colors"
                                        >
                                            Sign Out
                                        </button>
                                    </div>
                                ) : (
                                    <div className="flex items-center gap-2 sm:gap-3">
                                        <Link
                                            href="/login"
                                            className="text-gray-300 hover:text-white text-sm font-medium transition-colors px-2 sm:px-3 py-1.5"
                                        >
                                            Sign In
                                        </Link>
                                        <Link
                                            href="/signup"
                                            className="bg-[#E50914] hover:bg-[#b2070f] text-white px-3 sm:px-4 py-1.5 sm:py-2 rounded text-sm font-medium transition-all duration-200 hover:scale-105"
                                        >
                                            Sign Up
                                        </Link>
                                    </div>
                                )
                            )}
                        </div>
                    </div>
                </div>
            </nav>
        </>
    );
}

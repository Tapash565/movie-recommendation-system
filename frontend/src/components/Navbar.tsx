'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState, useCallback } from 'react';
import { useAuth, signOut } from '@/lib/auth';
import { cn } from '@/lib/utils';
import MobileSidebar from './MobileSidebar';

export default function Navbar() {
    const pathname = usePathname();
    const { user, loading } = useAuth();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    // Compute a safe display name for the user
    const displayName = user?.email?.split('@')[0] || user?.displayName || 'Guest';

    // Prevent body scroll when sidebar is open
    useEffect(() => {
        if (isSidebarOpen) {
            document.body.classList.add('sidebar-open');
        } else {
            document.body.classList.remove('sidebar-open');
        }
        return () => document.body.classList.remove('sidebar-open');
    }, [isSidebarOpen]);

    const handleLogout = async () => {
        try {
            await signOut();
            window.location.href = '/'; // Hard reload to clear internal state
        } catch (error) {
            console.error('Logout failed', error);
        }
    };

    // Stabilize onClose callback to prevent unnecessary re-renders
    const handleCloseSidebar = useCallback(() => {
        setIsSidebarOpen(false);
    }, []);

    const navLinkClass = (path: string) =>
        cn(
            "text-gray-300 hover:text-white transition-colors duration-200 px-3 py-2 rounded-md text-sm font-medium",
            pathname === path && "text-white bg-white/10"
        );

    return (
        <>
            <MobileSidebar
                isOpen={isSidebarOpen}
                onClose={handleCloseSidebar}
                user={user}
                onLogout={handleLogout}
            />

            <nav className="bg-black/80 backdrop-blur-md border-b border-white/10 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center gap-4">
                            {/* Hamburger Menu - Mobile Only */}
                            <button
                                onClick={() => setIsSidebarOpen(true)}
                                className="block md:hidden p-2 hover:bg-white/10 rounded-lg transition-colors"
                                aria-label="Open menu"
                                aria-expanded={isSidebarOpen}
                            >
                                <svg
                                    className="w-6 h-6 text-white"
                                    fill="none"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path d="M4 6h16M4 12h16M4 18h16" />
                                </svg>
                            </button>

                            <Link href="/" className="text-xl md:text-2xl font-bold bg-linear-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
                                Movie Recommender
                            </Link>

                            {/* Desktop Navigation */}
                            <div className="hidden md:block ml-10">
                                <div className="flex items-baseline space-x-4">
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
                                                My Library
                                            </Link>
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Desktop Auth Buttons */}
                        <div className="hidden md:block">
                            {!loading && user ? (
                                <div className="flex items-center gap-4">
                                    <span className="text-gray-400 text-sm">Welcome, {displayName}</span>
                                    <button
                                        onClick={handleLogout}
                                        className="text-red-400 hover:text-red-300 text-sm font-medium transition-colors"
                                    >
                                        Logout
                                    </button>
                                </div>
                            ) : (
                                <div className="flex items-center gap-4">
                                    <Link href="/login" className={navLinkClass('/login')}>
                                        Login
                                    </Link>
                                    <Link
                                        href="/signup"
                                        className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-full text-sm font-medium transition-colors"
                                    >
                                        Sign Up
                                    </Link>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </nav>
        </>
    );
}

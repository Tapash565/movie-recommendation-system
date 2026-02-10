'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

interface MobileSidebarProps {
    isOpen: boolean;
    onClose: () => void;
    user: { username: string; id: number } | null;
    onLogout: () => void;
}

export default function MobileSidebar({ isOpen, onClose, user, onLogout }: MobileSidebarProps) {
    const pathname = usePathname();

    // Close sidebar on ESC key
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) {
                onClose();
            }
        };
        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [isOpen, onClose]);

    // Close sidebar on route change
    useEffect(() => {
        onClose();
    }, [pathname]);

    const navLinkClass = (path: string) =>
        cn(
            "flex items-center gap-3 px-6 py-4 rounded-lg transition-all text-base font-medium",
            pathname === path
                ? "text-white bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-l-4 border-purple-500"
                : "text-gray-300 hover:text-white hover:bg-white/10"
        );

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
                        onClick={onClose}
                        aria-hidden="true"
                    />

                    {/* Sidebar Panel */}
                    <motion.div
                        initial={{ x: "-100%" }}
                        animate={{ x: 0 }}
                        exit={{ x: "-100%" }}
                        transition={{ type: "spring", damping: 25, stiffness: 200 }}
                        className="fixed top-0 left-0 h-full w-[280px] bg-black/95 backdrop-blur-xl border-r border-white/10 z-50 overflow-y-auto"
                        role="dialog"
                        aria-modal="true"
                        aria-label="Mobile navigation"
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between p-6 border-b border-white/10">
                            <Link 
                                href="/" 
                                className="text-xl font-bold bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent"
                                onClick={onClose}
                            >
                                Movie Recommender
                            </Link>
                            <button
                                onClick={onClose}
                                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                                aria-label="Close menu"
                            >
                                <svg
                                    className="w-6 h-6 text-gray-300"
                                    fill="none"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        {/* Navigation Links */}
                        <div className="py-6 space-y-2">
                            <Link href="/" className={navLinkClass('/')}>
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                                </svg>
                                Home
                            </Link>
                            
                            <Link href="/search" className={navLinkClass('/search')}>
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                                Search
                            </Link>

                            {user && (
                                <>
                                    <Link href="/discover" className={navLinkClass('/discover')}>
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                                        </svg>
                                        Discover
                                    </Link>
                                    
                                    <Link href="/library" className={navLinkClass('/library')}>
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                                        </svg>
                                        My Library
                                    </Link>
                                </>
                            )}
                        </div>

                        {/* Divider */}
                        <div className="border-t border-white/10 mx-4" />

                        {/* Auth Section */}
                        <div className="py-6 px-4 space-y-3">
                            {user ? (
                                <>
                                    <div className="px-4 py-3 bg-white/5 rounded-lg">
                                        <p className="text-xs text-gray-400">Signed in as</p>
                                        <p className="text-sm font-medium text-white mt-1">{user.username}</p>
                                    </div>
                                    <button
                                        onClick={() => {
                                            onLogout();
                                            onClose();
                                        }}
                                        className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition-colors font-medium"
                                    >
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                                        </svg>
                                        Logout
                                    </button>
                                </>
                            ) : (
                                <>
                                    <Link
                                        href="/login"
                                        className="block w-full px-6 py-3 text-center bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors font-medium"
                                    >
                                        Login
                                    </Link>
                                    <Link
                                        href="/signup"
                                        className="block w-full px-6 py-3 text-center bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-lg transition-colors font-medium"
                                    >
                                        Sign Up
                                    </Link>
                                </>
                            )}
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}

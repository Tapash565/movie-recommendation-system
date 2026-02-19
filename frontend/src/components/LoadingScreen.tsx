'use client';

import { motion } from 'framer-motion';

interface LoadingScreenProps {
    attempts: number;
    onRetry?: () => void;
}

export default function LoadingScreen({ attempts, onRetry }: LoadingScreenProps) {
    const showRetry = attempts > 5;

    return (
        <div className="fixed inset-0 z-9999 flex flex-col items-center justify-center bg-background overflow-hidden">
            {/* Dynamic Background */}
            <div className="absolute inset-0 z-0">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-600/20 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-pink-600/20 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
            </div>

            <div className="relative z-10 flex flex-col items-center max-w-md px-6 text-center">
                {/* Animated Icon/Logo Area */}
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="relative mb-12"
                >
                    {/* Pulsing rings */}
                    <div className="absolute inset-0 -m-4 border-2 border-purple-500/20 rounded-full animate-ping"></div>
                    <div className="absolute inset-0 -m-8 border border-cyan-500/10 rounded-full animate-ping [animation-delay:1s]"></div>

                    <div className="relative w-32 h-32 flex items-center justify-center bg-linear-to-br from-purple-600 to-pink-600 rounded-2xl shadow-2xl shadow-purple-500/20 rotate-12">
                        <svg
                            className="w-16 h-16 text-white -rotate-12"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
                            />
                        </svg>
                    </div>
                </motion.div>

                {/* Text Content */}
                <motion.div
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.3, duration: 0.6 }}
                    className="space-y-4"
                >
                    <h1 className="text-3xl font-bold text-white tracking-tight">
                        Initializing <span className="text-transparent bg-clip-text bg-linear-to-r from-cyan-400 to-purple-500">Cinematic Universe</span>
                    </h1>
                    <p className="text-gray-400 text-lg">
                        {attempts > 3 ? "The server is taking a moment to wake up..." : "Connecting to our secure database..."}
                    </p>

                    {/* Progress Bar */}
                    <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden mt-8">
                        <motion.div
                            className="bg-linear-to-r from-cyan-500 to-purple-600 h-full"
                            animate={{
                                width: ["0%", "30%", "45%", "60%", "75%", "90%", "95%"],
                            }}
                            transition={{
                                duration: 20,
                                ease: "linear",
                            }}
                        />
                    </div>

                    <div className="flex items-center justify-center space-x-4 pt-4">
                        <span className="text-xs font-mono uppercase tracking-widest text-gray-500">
                            Attempt {attempts}
                        </span>
                        <div className="flex space-x-1">
                            {[0, 1, 2].map((i) => (
                                <motion.div
                                    key={i}
                                    className="w-1.5 h-1.5 bg-purple-500 rounded-full"
                                    animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
                                    transition={{ repeat: Infinity, duration: 1, delay: i * 0.2 }}
                                />
                            ))}
                        </div>
                    </div>
                </motion.div>

                {/* Retry Button */}
                {showRetry && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-12"
                    >
                        <button
                            onClick={onRetry}
                            className="px-8 py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl border border-white/10 transition-all backdrop-blur-sm"
                        >
                            Force Retry
                        </button>
                    </motion.div>
                )}
            </div>
        </div>
    );
}

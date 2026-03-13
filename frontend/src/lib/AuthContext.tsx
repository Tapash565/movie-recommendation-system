'use client';

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { onAuthStateChanged, User } from 'firebase/auth';
import { auth } from './firebase';
import api from './api';

interface AuthContextValue {
    user: User | null;
    loading: boolean;
    /** The user's server-side adult content filter preference. null = not yet loaded. */
    filterAdult: boolean | null;
    /** Call after saving a new preference so the context stays in sync. */
    setFilterAdult: (value: boolean) => void;
}

const AuthContext = createContext<AuthContextValue>({
    user: null,
    loading: !!auth,
    filterAdult: null,
    setFilterAdult: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(() => !!auth);
    const [filterAdult, setFilterAdult] = useState<boolean | null>(null);

    // Fetch preferences from the server once when a user logs in.
    // Cleared back to null on logout so stale data never leaks between accounts.
    const fetchPreferences = useCallback(async () => {
        try {
            const res = await api.get('/preferences');
            setFilterAdult(res.data.filter_adult ?? false);
        } catch {
            // Non-fatal: default to false if the fetch fails
            setFilterAdult(false);
        }
    }, []);

    useEffect(() => {
        if (!auth) return;

        const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
            setUser(currentUser);
            setLoading(false);

            if (currentUser) {
                fetchPreferences();
            } else {
                // User logged out — clear preference so the next user starts clean
                setFilterAdult(null);
            }
        });

        return () => unsubscribe();
    }, [fetchPreferences]);

    return (
        <AuthContext.Provider value={{ user, loading, filterAdult, setFilterAdult }}>
            {children}
        </AuthContext.Provider>
    );
}

/**
 * Hook to consume auth state and user preferences from the nearest AuthProvider.
 * All components share one Firebase listener and one preference fetch per session.
 */
export function useAuth() {
    return useContext(AuthContext);
}
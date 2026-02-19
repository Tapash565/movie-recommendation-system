import {
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    signOut as firebaseSignOut,
    onAuthStateChanged,
    User
} from "firebase/auth";
import { useState, useEffect } from "react";
import { isAxiosError } from "axios";
import { auth } from "./firebase";
import api from "./api";

/**
 * Hook to manage authentication state across the app.
 */
export function useAuth() {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!auth) {
            setTimeout(() => setLoading(false), 0);
            return;
        }
        const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
            setUser(currentUser);
            setLoading(false);
        });
        return () => unsubscribe();
    }, []);

    return { user, loading };
}

/**
 * Safely extracts an error message from any caught error.
 */
function extractErrorMessage(error: unknown): string {
    if (error instanceof Error) return error.message;
    if (typeof error === 'string') return error;
    return "An unexpected error occurred.";
}

/**
 * Signs up a new user using Firebase.
 */
export async function signUp(email: string, password: string) {
    if (!auth) return { user: null, error: "Firebase Authentication is not initialized." };
    try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        return { user: userCredential.user, error: null };
    } catch (error) {
        return { user: null, error: extractErrorMessage(error) };
    }
}

/**
 * Signs in an existing user using Firebase.
 */
export async function signIn(email: string, password: string) {
    if (!auth) return { user: null, error: "Firebase Authentication is not initialized." };
    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        return { user: userCredential.user, error: null };
    } catch (error) {
        return { user: null, error: extractErrorMessage(error) };
    }
}

/**
 * Signs out the current user.
 */
export async function signOut() {
    if (!auth) return { error: "Firebase Authentication is not initialized." };
    try {
        await firebaseSignOut(auth);
        return { error: null };
    } catch (error) {
        return { error: extractErrorMessage(error) };
    }
}

/**
 * Fetches current user info from the backend.
 * Uses the Bearer token intercepted by axios.
 */
export async function getBackendUser() {
    try {
        const response = await api.get('/auth/me');
        return { data: response.data, error: null };
    } catch (error) {
        if (isAxiosError(error) && error.response) {
            const status = error.response.status;
            if (status === 401 || status === 403) {
                return { data: null, error: 'unauthenticated' };
            }
            return { data: null, error: `Error ${status}: ${error.response.data?.detail || 'Server error'}` };
        }
        return { data: null, error: 'network_error' };
    }
}

import {
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    signOut as firebaseSignOut,
    onAuthStateChanged,
    User
} from "firebase/auth";
import { useState, useEffect } from "react";
import { auth } from "./firebase";
import api from "./api";

/**
 * Hook to manage authentication state across the app.
 */
export function useAuth() {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
            setUser(currentUser);
            setLoading(false);
        });
        return () => unsubscribe();
    }, []);

    return { user, loading };
}

/**
 * Signs up a new user using Firebase.
 */
export async function signUp(email: string, password: string) {
    try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        return { user: userCredential.user, error: null };
    } catch (error: any) {
        return { user: null, error: error.message };
    }
}

/**
 * Signs in an existing user using Firebase.
 */
export async function signIn(email: string, password: string) {
    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        return { user: userCredential.user, error: null };
    } catch (error: any) {
        return { user: null, error: error.message };
    }
}

/**
 * Signs out the current user.
 */
export async function signOut() {
    try {
        await firebaseSignOut(auth);
        return { error: null };
    } catch (error: any) {
        return { error: error.message };
    }
}

/**
 * Fetches current user info from the backend.
 * Uses the Bearer token intercepted by axios.
 */
export async function getBackendUser() {
    try {
        const response = await api.get('/auth/me');
        return response.data;
    } catch (error) {
        console.error('Failed to fetch backend user:', error);
        return null;
    }
}

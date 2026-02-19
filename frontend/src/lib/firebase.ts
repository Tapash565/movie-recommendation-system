import { initializeApp, getApps, getApp, type FirebaseApp } from "firebase/app";
import { getAuth, type Auth } from "firebase/auth";
import { getAnalytics, isSupported, type Analytics } from "firebase/analytics";

const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
    measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID,
};

// Initialize Firebase gracefully
const isConfigValid = !!firebaseConfig.apiKey;

if (!isConfigValid && typeof window !== 'undefined') {
    console.warn("Firebase configuration is missing. Ensure NEXT_PUBLIC_FIREBASE_API_KEY is set.");
}

export const app: FirebaseApp | null = (isConfigValid && getApps().length === 0)
    ? initializeApp(firebaseConfig)
    : (getApps().length > 0 ? getApp() : null);

export const auth: Auth | null = app ? getAuth(app) : null;

/**
 * Returns a promise that resolves to the Firebase Analytics instance if supported.
 */
export async function getAnalyticsInstance(): Promise<Analytics | null> {
    if (typeof window === "undefined" || !app) return null;
    try {
        const supported = await isSupported();
        return supported ? getAnalytics(app) : null;
    } catch (err) {
        console.warn("Analytics initialization failed:", err);
        return null;
    }
}

import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getAnalytics, isSupported } from "firebase/analytics";

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

const app = (isConfigValid && getApps().length === 0)
    ? initializeApp(firebaseConfig)
    : (getApps().length > 0 ? getApp() : null);

const auth = app ? getAuth(app) : null;

// Initialize Analytics conditionally (only in browser and if app exists)
let analytics;
if (typeof window !== "undefined" && app) {
    isSupported().then((supported) => {
        if (supported) analytics = getAnalytics(app);
    }).catch(err => console.warn("Analytics not supported:", err));
}

export { app, auth, analytics };

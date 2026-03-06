"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signOut } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { useAuth } from "@/lib/auth";

export default function ProfilePage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  const handleDeleteAccount = async () => {
    if (confirmText !== "DELETE") {
      setError('Please type "DELETE" to confirm');
      return;
    }

    setDeleting(true);
    setError("");

    try {
      if (!auth) throw new Error("Auth is not initialized");
      const currentUser = auth.currentUser;
      if (!currentUser) {
        throw new Error("Not authenticated");
      }

      // Get fresh token
      const token = await currentUser.getIdToken(true);

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/users/me`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || "Failed to delete account");
      }

      // Sign out after successful deletion
      await signOut(auth);
      router.push("/signup");
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to delete account";
      setError(errorMessage);
    } finally {
      setDeleting(false);
    }
  };

  const handleSignOut = async () => {
    if (auth) {
      await signOut(auth);
    }
    router.push("/login");
  };

  // Redirect to login if user is not authenticated (useEffect must be before any early returns)
  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-purple-400">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen p-6 relative overflow-hidden">
      {/* Background Elements */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-600/20 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-pink-600/20 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
      </div>

      <div className="relative z-10 max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-linear-to-r from-cyan-400 via-purple-500 to-pink-500 mb-8">
          Profile
        </h1>

        {/* User Info Card */}
        <div className="bg-[#1e293b]/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Account Information</h2>
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-linear-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-xl">
                {user.email?.charAt(0).toUpperCase() || "U"}
              </div>
              <div>
                <p className="text-gray-400 text-sm">Email</p>
                <p className="text-white">{user.email || "No email"}</p>
              </div>
            </div>
            <div className="pt-2">
              <p className="text-gray-400 text-sm">User ID</p>
              <p className="text-white text-sm font-mono truncate">{user.uid}</p>
            </div>
          </div>
        </div>

        {/* Quick Links */}
        <div className="bg-[#1e293b]/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Quick Links</h2>
          <div className="space-y-2">
            <Link
              href="/library"
              className="block w-full text-left px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-white transition-colors"
            >
              My Library
            </Link>
            <Link
              href="/discover"
              className="block w-full text-left px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-white transition-colors"
            >
              Discover Movies
            </Link>
          </div>
        </div>

        {/* Sign Out */}
        <div className="bg-[#1e293b]/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Session</h2>
          <button
            onClick={handleSignOut}
            className="w-full px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-white transition-colors"
          >
            Sign Out
          </button>
        </div>

        {/* Danger Zone */}
        <div className="bg-red-900/20 backdrop-blur-xl border border-red-500/30 rounded-2xl p-6">
          <h2 className="text-xl font-semibold text-red-400 mb-2">Danger Zone</h2>
          <p className="text-gray-400 text-sm mb-4">
            Once you delete your account, there is no going back. All your bookmarks, ratings, and
            personalized data will be permanently removed.
          </p>
          <button
            onClick={() => setShowDeleteModal(true)}
            className="px-4 py-3 rounded-xl bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/50 transition-colors"
          >
            Delete Account
          </button>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => !deleting && setShowDeleteModal(false)}
          ></div>
          <div className="relative bg-[#1e293b] border border-red-500/30 rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="text-xl font-bold text-red-400 mb-4">Delete Account</h3>
            <p className="text-gray-300 mb-4">
              This action is <span className="text-red-400 font-semibold">irreversible</span>. All
              your data including bookmarks, ratings, and recommendations will be permanently
              deleted.
            </p>
            <p className="text-gray-400 text-sm mb-4">
              Type <span className="text-white font-mono bg-white/10 px-1 rounded">DELETE</span> to
              confirm:
            </p>
            <input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder='Type "DELETE"'
              disabled={deleting}
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-red-500/50 disabled:opacity-50 mb-4"
            />
            {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                disabled={deleting}
                className="flex-1 px-4 py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleting || confirmText !== "DELETE"}
                className="flex-1 px-4 py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleting ? "Deleting..." : "Delete Account"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

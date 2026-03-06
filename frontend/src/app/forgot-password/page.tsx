"use client";

import { useState } from "react";
import { sendPasswordResetEmail } from "firebase/auth";
import { auth } from "@/lib/firebase";
import Link from "next/link";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<{ type: "idle" | "ok" | "err"; msg: string }>({
    type: "idle",
    msg: "",
  });
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus({ type: "idle", msg: "" });
    setLoading(true);
    try {
      if (!auth) throw new Error("Auth is not initialized");
      await sendPasswordResetEmail(auth, email.trim());
      setStatus({
        type: "ok",
        msg: "Password reset email sent. Check your inbox (and spam).",
      });
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to send reset email.";
      setStatus({
        type: "err",
        msg: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background Elements */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-600/20 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-pink-600/20 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-32 left-1/3 w-96 h-96 bg-blue-600/20 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>
      </div>

      <form
        onSubmit={onSubmit}
        className="relative z-10 w-full max-w-md rounded-2xl border border-white/10 bg-[#1e293b]/80 backdrop-blur-xl p-8 shadow-2xl"
      >
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-linear-to-r from-cyan-400 via-purple-500 to-pink-500">
            Reset Password
          </h1>
          <p className="text-sm text-gray-400 mt-2">
            Enter your email and we&apos;ll send a reset link.
          </p>
        </div>

        <label className="block text-sm text-gray-300 mb-2">Email</label>
        <input
          className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          required
        />

        <button
          disabled={loading}
          className="mt-6 w-full rounded-xl bg-linear-to-r from-purple-600 to-pink-600 px-4 py-3 font-semibold text-white hover:from-purple-500 hover:to-pink-500 disabled:opacity-60 transition-all shadow-lg hover:shadow-purple-500/25"
          type="submit"
        >
          {loading ? "Sending..." : "Send reset link"}
        </button>

        {status.type !== "idle" && (
          <div
            className={`mt-4 text-sm text-center ${status.type === "ok" ? "text-green-400" : "text-red-400"
              }`}
          >
            {status.msg}
          </div>
        )}

        <div className="mt-6 text-center text-sm text-gray-400">
          Remember your password?{" "}
          <Link href="/login" className="text-purple-400 hover:text-purple-300 underline">
            Sign in
          </Link>
        </div>
      </form>
    </div>
  );
}

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Navbar from '@/components/Navbar';
import DatabaseLoader from '@/components/DatabaseLoader';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'MovieMind - AI Powered Movie Recommendations',
  description: 'Discover your next favorite movie using our intelligent AI recommendation engine. Explore thousands of movies personalized for you.',
  keywords: ['movie recommendations', 'AI movies', 'film discovery', 'personalized movies'],
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <DatabaseLoader>
          <Navbar />
          <main>{children}</main>
        </DatabaseLoader>
      </body>
    </html>
  );
}

import Link from 'next/link';
import Image from 'next/image';

interface Movie {
    id: number;
    title: string;
    year: string;
    poster_url: string;
    vote_average: number;
}

export default function MovieCard({ movie }: { movie: Movie }) {
    return (
        <div className="group relative bg-gray-900 rounded-xl overflow-hidden shadow-lg transition-transform duration-300 hover:scale-105 hover:shadow-2xl">
            <Link href={`/movie/${movie.id}`}>
                <div className="relative aspect-[2/3] w-full">
                    <Image
                        src={movie.poster_url}
                        alt={movie.title}
                        fill
                        className="object-cover"
                        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
                        <button className="w-full bg-purple-600 text-white py-2 rounded-lg font-semibold hover:bg-purple-700 transition-colors">
                            View Details
                        </button>
                    </div>
                </div>
                <div className="p-4">
                    <h3 className="text-white font-semibold text-lg truncate" title={movie.title}>
                        {movie.title}
                    </h3>
                    <div className="flex justify-between items-center mt-2 text-gray-400 text-sm">
                        <span>{movie.year}</span>
                        <span className="flex items-center text-yellow-400">
                            ★ {movie.vote_average.toFixed(1)}
                        </span>
                    </div>
                </div>
            </Link>
        </div>
    );
}

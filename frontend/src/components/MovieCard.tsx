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
        <article className="group relative bg-gray-900 rounded-xl overflow-hidden shadow-lg transition-transform duration-300 hover:scale-105 hover:shadow-2xl">
            <Link
                href={`/movie/${movie.id}`}
                aria-label={`View details for ${movie.title} (${movie.year})`}
                className="block"
            >
                <div className="relative aspect-2/3 w-full overflow-hidden" aria-hidden="true">
                    <Image
                        src={movie.poster_url}
                        alt=""
                        fill
                        className="object-cover"
                        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    />
                    <div className="absolute inset-0 bg-linear-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
                        <span className="w-full bg-purple-600 text-white py-2 rounded-lg font-semibold text-center pointer-events-none">
                            View Details
                        </span>
                    </div>
                </div>
                <div className="p-4">
                    <h3 className="text-white font-semibold text-lg truncate" title={movie.title}>
                        {movie.title}
                    </h3>
                    <div className="flex justify-between items-center mt-2 text-gray-400 text-sm">
                        <time dateTime={movie.year}>{movie.year}</time>
                        <span className="flex items-center text-yellow-400" aria-label={`Rating: ${movie.vote_average.toFixed(1)} out of 10`}>
                            ★ {movie.vote_average.toFixed(1)}
                        </span>
                    </div>
                </div>
            </Link>
        </article>
    );
}

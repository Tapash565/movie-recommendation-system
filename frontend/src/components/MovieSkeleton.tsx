export default function MovieSkeleton() {
    return (
        <div className="flex-shrink-0 w-[140px] sm:w-[160px] md:w-[180px] lg:w-[200px]">
            <div className="aspect-[2/3] bg-white/10 rounded-md animate-pulse" />
            <div className="mt-2 space-y-2">
                <div className="h-4 bg-white/10 rounded w-3/4 animate-pulse" />
                <div className="h-3 bg-white/10 rounded w-1/4 animate-pulse" />
            </div>
        </div>
    );
}

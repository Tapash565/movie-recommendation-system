export default function MovieSkeleton() {
    return (
        <div className="bg-gray-900 rounded-xl overflow-hidden shadow-lg animate-pulse">
            <div className="aspect-2/3 w-full bg-gray-800"></div>
            <div className="p-4 space-y-3">
                <div className="h-5 bg-gray-800 rounded w-3/4"></div>
                <div className="flex justify-between items-center">
                    <div className="h-4 bg-gray-800 rounded w-1/4"></div>
                    <div className="h-4 bg-gray-800 rounded w-1/4"></div>
                </div>
            </div>
        </div>
    );
}

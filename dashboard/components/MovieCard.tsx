import { Star, Play, Info, Tv } from 'lucide-react';
import { MovieItem } from '@/lib/api';

interface MovieCardProps {
  item: MovieItem;
  onClick: (item: MovieItem) => void;
  onInfoClick?: (item: MovieItem) => void;
}

export const MovieCard: React.FC<MovieCardProps> = ({ item, onClick, onInfoClick }) => {
  const placeholder = "https://images.unsplash.com/photo-1594322436404-5a0526db4d13?q=80&w=500&auto=format&fit=crop";

  return (
    <div 
      className="group relative flex-shrink-0 w-40 md:w-48 bg-zinc-900 rounded-xl overflow-hidden cursor-pointer transition-all duration-300 hover:scale-105 hover:ring-2 hover:ring-red-600"
      onClick={() => onClick(item)}
    >
      <div className="aspect-[2/3] relative">
        <img 
          src={item.cover || item.poster || placeholder} 
          alt={item.title}
          onError={(e) => { (e.target as HTMLImageElement).src = placeholder; }}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60 group-hover:opacity-40 transition-opacity" />
        
        {/* Hover Overlay */}
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-[2px]">
           <div className="p-3 bg-red-600 rounded-full shadow-lg transform translate-y-4 group-hover:translate-y-0 transition-transform">
              <Play className="w-6 h-6 fill-white" />
           </div>
        </div>

        {/* Rating/Info Badge */}
        <div className="absolute top-2 right-2 flex flex-col gap-1 items-end">
           {item.score && item.score !== 'N/A' && (
             <div className="px-2 py-1 bg-black/70 backdrop-blur-md rounded-md flex items-center gap-1 border border-white/10">
               <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
               <span className="text-[10px] font-bold text-white">{item.score}</span>
             </div>
           )}
           {onInfoClick && (
             <button 
               onClick={(e) => { e.stopPropagation(); onInfoClick(item); }}
               className="p-1.5 bg-black/70 backdrop-blur-md rounded-full border border-white/10 hover:bg-zinc-800"
             >
               <Info className="w-3 h-3 text-white" />
             </button>
           )}
        </div>
      </div>
      
      <div className="p-3">
        {item.title && item.title !== "Unknown" && (
           <h3 className="text-sm font-semibold text-zinc-100 truncate group-hover:text-red-500 transition-colors">
              {item.title}
           </h3>
        )}
        <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] text-zinc-500 font-medium">
              {item.title !== "Unknown" && (
                item.subjectType === 2 ? (
                  <span className="flex items-center gap-1">
                    <Tv className="w-2.5 h-2.5 text-red-500" />
                    Series {item.season && `• S${item.season} E${item.episode || 1}`}
                  </span>
                ) : 'Movie'
              )}
            </span>
            {item.title !== "Unknown" && item.releaseTime && (
              <span className="text-[10px] text-zinc-600">
                • {item.releaseTime.length > 4 ? new Date(item.releaseTime).getFullYear() : item.releaseTime}
              </span>
            )}
        </div>
      </div>
    </div>
  );
};

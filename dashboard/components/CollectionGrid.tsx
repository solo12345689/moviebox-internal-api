import React from 'react';
import { useRouter } from 'next/navigation';
import { Film } from 'lucide-react';

interface CollectionGridProps {
  items: any[];
}

export const CollectionGrid = ({ items }: CollectionGridProps) => {
  const router = useRouter();

  if (!items || items.length === 0) return null;

  return (
    <div className="space-y-6 pt-10">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-black uppercase italic tracking-tighter flex items-center gap-3">
          <Film className="w-6 h-6 text-red-600" />
          Collection Content
        </h2>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {items.map((item: any) => (
          <div 
            key={String(item.subjectId || item.id)}
            onClick={() => router.push(`/detail/${item.subjectId || item.id}`)}
            className="group cursor-pointer space-y-2"
          >
            <div className="aspect-[2/3] relative rounded-xl overflow-hidden border border-white/10 group-hover:border-red-600 transition-all group-hover:scale-[1.03]">
              <img 
                src={item.poster || item.cover} 
                className="w-full h-full object-cover" 
                loading="lazy"
              />
              <div className="absolute inset-x-0 bottom-0 p-2 bg-gradient-to-t from-black to-transparent">
                <p className="text-[10px] font-black uppercase truncate">{item.title}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

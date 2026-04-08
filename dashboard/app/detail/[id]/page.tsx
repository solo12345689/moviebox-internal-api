'use client';

import React, { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { movieApi, MovieItem } from '../../../lib/api';
import { 
  Play, Plus, Star, ChevronLeft, Info, 
  Clock, Calendar, Languages, Film, X, Zap, 
  User, Tv, ChevronRight, Pause, RotateCcw, 
  RotateCw, Settings, Subtitles, Download,
  Volume2, Maximize, Loader2
} from 'lucide-react';
import { CollectionGrid } from '../../../components/CollectionGrid';
import Artplayer from 'artplayer';
import Hls from 'hls.js';

function ArtPlayer({ option, getInstance, className, ...rest }: any) {
  const artRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const art = new Artplayer({
      ...option,
      container: artRef.current!,
    });

    if (getInstance && typeof getInstance === 'function') {
      getInstance(art);
    }

    return () => {
      if (art && art.destroy) {
        art.destroy(false);
      }
    };
  }, []);

  return <div ref={artRef} className={className} {...rest}></div>;
}

export default function MovieDetail() {
  const { id } = useParams();
  const router = useRouter();
  const [movie, setMovie] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [watchlistActive, setWatchlistActive] = useState(false);
  const [seasons, setSeasons] = useState<any[]>([]);
  const [selectedSeasonIdx, setSelectedSeasonIdx] = useState(0);
  const [episodes, setEpisodes] = useState<any[]>([]);
  const [streamInfo, setStreamInfo] = useState<any>(null);
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<any>(null); // {id, subjectId, name, type}
  
  const artInstance = useRef<any>(null);

  useEffect(() => {
    if (id) {
       fetchDetail();
    }
  }, [id]);

  const fetchDetail = async () => {
    try {
      const res = await movieApi.getDetail(id as string);
      const data = res.data;
      setMovie(data);
      
      if (data.subjectType === 2 || data.isCollection) {
         const epRes = await movieApi.getEpisodes(id as string);
         const list = epRes.data?.seasons || epRes.data || [];
         setSeasons(list);
         if (list.length > 0) {
            setEpisodes(list[0].episodes || []);
         }
      }
      setLoading(false);
    } catch (e) {
      setLoading(false);
    }
  };

  const selectSeason = (idx: number) => {
     setSelectedSeasonIdx(idx);
     setEpisodes(seasons[idx].episodes || []);
     setStreamInfo(null);
  };

  const getStream = async (seasonNum: number, epNum: number|string, qual?: string) => {
     try {
        const targetId = selectedLanguage?.subjectId || id;
        const resourceId = selectedLanguage?.id;
        
        console.log("Resolving Stream for native launch:", targetId, "S", seasonNum, "E", epNum, "Resource:", resourceId);
        
        // 1. Pre-resolve the video URL via our high-fidelity resolver API
        const streamData = await movieApi.getStream(targetId as string, seasonNum || 1, epNum as any || 1, qual, resourceId || undefined);
        
        if (!streamData?.url) {
           console.error("Could not resolve video URL.");
           return;
        }

        console.log("Launching MPV with resolved URL:", streamData.url.substring(0, 50) + "...");
        
        // 2. Pass the RAW VIDEO URL to the backend launcher
        await movieApi.launchPlayer('mpv', streamData.url, {
           subject_id: selectedLanguage?.subjectId || id,
           resource_id: selectedLanguage?.id,
           season: seasonNum || 1,
           episode: epNum || 1,
           title: movie?.title,
           cookie: streamData.cookie,
           duration: streamData.duration
        });
     } catch (e) {
        console.error("MPV Launch error:", e);
     }
  };

  const handleWatchlist = async () => {
    if (!movie) return;
    try {
      await movieApi.toggleWatchlist(id as string, !watchlistActive, movie.subjectType || 1);
      setWatchlistActive(!watchlistActive);
    } catch (e) {}
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-black">
      <div className="w-12 h-12 border-4 border-red-600 border-t-transparent rounded-full animate-spin"></div>
    </div>
  );

  if (!movie) return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white">
       <h1 className="text-2xl font-bold mb-4">Movie Not Found</h1>
       <button onClick={() => router.back()} className="px-6 py-2 bg-zinc-800 rounded-full">Go Back</button>
    </div>
  );

  return (
    <div className="relative min-h-screen bg-black text-white overflow-x-hidden pb-20">
      {/* Background Hero */}
      <div className="absolute top-0 left-0 w-full h-[70vh] overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent z-10" />
        <div className="absolute inset-0 bg-gradient-to-r from-black via-transparent to-black/20 z-10" />
        <img 
          src={movie.cover || movie.poster} 
          className="w-full h-full object-cover opacity-50 scale-105 blur-[2px]"
          alt=""
        />
      </div>

      {/* Content Container */}
      <div className="relative z-20 pt-10 px-6 md:px-16 container mx-auto">
        <button 
          onClick={() => router.back()}
          className="group mb-12 flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-full border border-white/10 backdrop-blur-md transition-all font-bold tracking-tight"
        >
          <ChevronLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
          Back to Catalog
        </button>

        <div className="flex flex-col lg:flex-row gap-12 items-start mb-20">
          <div className="w-full max-w-[320px] shrink-0 mx-auto lg:mx-0 shadow-2xl shadow-red-900/40 rounded-3xl overflow-hidden border border-white/10 group relative">
             <img src={movie.poster || movie.cover} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" />
             <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
             {movie.score && movie.score !== 'N/A' && (
                <div className="absolute bottom-4 left-4 flex items-center gap-2 bg-yellow-500 text-black px-3 py-1 rounded-lg font-black italic tracking-tighter shadow-lg">
                   <Star className="w-4 h-4 fill-black" />
                   {movie.score}
                </div>
             )}
          </div>

          <div className="flex-1 max-w-3xl">
             <div className="flex flex-wrap items-center gap-3 mb-6">
                <span className="px-3 py-1 bg-red-600 rounded-md text-[10px] font-black uppercase tracking-[0.2em] italic shadow-lg shadow-red-600/20">
                   {movie.subjectType === 2 ? 'TV Series' : 'Movie'}
                </span>
                {movie.quality && (
                  <span className="px-3 py-1 bg-white/10 backdrop-blur-md rounded-md text-[10px] font-bold text-zinc-300 uppercase tracking-widest border border-white/10">
                    {movie.quality}
                  </span>
                )}
                <span className="text-sm font-bold text-zinc-400">{movie.releaseTime?.substring(0, 4)}</span>
             </div>

             <h1 className="text-5xl md:text-7xl font-black italic uppercase tracking-tighter mb-6 leading-none text-white drop-shadow-2xl">
                {movie.title}
             </h1>

             <p className="text-lg md:text-xl text-zinc-400 leading-relaxed max-w-2xl font-medium mb-10 [text-wrap:balance]">
                {movie.description}
             </p>

             {!movie.isCollection && (
                <div className="flex flex-wrap gap-4 mb-12">
                   <button 
                     onClick={() => { if (episodes.length > 0) getStream(seasons[selectedSeasonIdx].seasonNumber, episodes[0].episodeNumber); else if (movie.subjectType !== 2) getStream(0, 0); }}
                     className="flex items-center gap-3 px-10 py-5 bg-red-600 hover:bg-red-700 rounded-2xl font-black italic uppercase tracking-widest shadow-xl shadow-red-600/30 transition-all hover:scale-105 active:scale-95 group"
                   >
                      <Play className="w-6 h-6 fill-white group-hover:scale-110 transition-transform" />
                      Watch Now
                   </button>
                   
                   {movie.languages?.length > 0 && (
                      <button 
                        onClick={() => setShowLanguageModal(true)}
                        className="flex items-center gap-3 px-8 py-5 bg-zinc-900 border-2 border-white/10 hover:border-red-600/50 rounded-2xl font-black italic uppercase tracking-widest transition-all hover:bg-zinc-800 group"
                      >
                         <Languages className="w-6 h-6 text-red-500 group-hover:scale-110 transition-transform" />
                         <span className="max-w-[120px] truncate">
                           {selectedLanguage ? selectedLanguage.name : "Audio / Dub"}
                         </span>
                      </button>
                   )}

                   <button 
                     onClick={handleWatchlist}
                     className={`flex items-center gap-3 px-10 py-5 rounded-2xl font-black italic uppercase tracking-widest transition-all border-2 ${watchlistActive ? 'bg-zinc-800 border-zinc-800 shadow-inner' : 'bg-transparent border-white/20 hover:bg-white/5'}`}
                   >
                      <Plus className={`w-6 h-6 ${watchlistActive ? 'rotate-45' : ''} transition-transform`} />
                      {watchlistActive ? 'Wishlisted' : 'Wishlist'}
                   </button>
                </div>
             )}

             <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                   { icon: Clock, label: 'Duration', value: movie.duration || 'N/A' },
                   { icon: Calendar, label: 'Released', value: movie.releaseTime || 'N/A' },
                   { icon: Languages, label: 'Language', value: movie.language || 'Multi' },
                   { icon: Film, label: 'Source', value: movie.source || 'Premium' }
                ].map((item, i) => (
                   <div key={i} className="p-4 bg-white/5 rounded-2xl border border-white/5 backdrop-blur-md">
                      <item.icon className="w-5 h-5 text-red-500 mb-2" />
                      <div className="text-[10px] uppercase font-bold text-zinc-500 tracking-widest leading-none mb-1">{item.label}</div>
                      <div className="text-sm font-bold truncate">{item.value}</div>
                   </div>
                ))}
             </div>
          </div>
        </div>

        {/* Cast Section */}
        {movie.cast && movie.cast.length > 0 && (
           <div className="mb-20">
              <h2 className="text-2xl font-black italic uppercase tracking-tighter mb-8 flex items-center gap-3">
                 <User className="w-6 h-6 text-red-600" />
                 Cast & Characters
              </h2>
              <div className="flex gap-4 overflow-x-auto pb-6 scrollbar-hide">
                 {movie.cast.map((actor: any, i: number) => (
                    <div key={i} className="flex-shrink-0 w-44 group">
                       <div className="aspect-[4/5] rounded-2xl overflow-hidden border border-white/5 mb-3 bg-zinc-900 group-hover:border-red-600/50 transition-colors">
                          <img 
                            src={actor.avatar || "https://images.unsplash.com/photo-1599566150163-29194dcaad36?q=80&w=200&auto=format&fit=crop"} 
                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" 
                            onError={(e) => { (e.target as HTMLImageElement).src = "https://images.unsplash.com/photo-1599566150163-29194dcaad36?q=80&w=200&auto=format&fit=crop"; }}
                          />
                       </div>
                       <div className="font-bold text-sm truncate group-hover:text-red-500 transition-colors">{actor.name}</div>
                       <div className="text-xs text-zinc-500 truncate">{actor.role}</div>
                    </div>
                 ))}
              </div>
           </div>
        )}

        {/* Series Episodes Selector */}
        {movie.subjectType === 2 && seasons.length > 0 && (
           <div className="mb-20">
              <div className="flex items-center justify-between mb-8">
                 <h2 className="text-2xl font-black italic uppercase tracking-tighter flex items-center gap-3">
                    <Tv className="w-6 h-6 text-red-600" />
                    Episodes
                 </h2>
                 {seasons.length > 1 && (
                    <div className="flex bg-white/5 rounded-full p-1 border border-white/5">
                       {seasons.map((s, i) => (
                          <button 
                            key={i}
                            onClick={() => selectSeason(i)}
                            className={`px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-widest transition-all ${selectedSeasonIdx === i ? 'bg-red-600 text-white shadow-lg' : 'text-zinc-500 hover:text-white'}`}
                          >
                             Season {s.seasonNumber}
                          </button>
                       ))}
                    </div>
                 )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                 {episodes.map((ep, i) => (
                    <button 
                      key={i}
                      onClick={() => getStream(seasons[selectedSeasonIdx].seasonNumber, ep.episodeNumber)}
                      className="group flex flex-col p-4 bg-white/5 hover:bg-white/10 rounded-2xl border border-white/5 transition-all text-left"
                    >
                       <div className="flex items-center justify-between mb-2">
                          <span className="text-[10px] font-black uppercase tracking-widest text-red-500 italic">EPISODE {ep.episodeNumber}</span>
                          <Play className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                       </div>
                       <div className="font-bold text-sm line-clamp-1">{ep.title || `Episode ${ep.episodeNumber}`}</div>
                    </button>
                 ))}
              </div>
           </div>
        )}

        {/* Collection Grid Fallback */}
        {movie.isCollection && movie.collectionItems && (
           <div className="mb-20">
              <CollectionGrid items={movie.collectionItems} />
           </div>
        )}
      </div>

      {/* Fullscreen Video Player Overlay using ArtPlayer */}
      {streamInfo && (
         <div className="fixed inset-0 z-[100] bg-black flex flex-col">
            <div className="absolute top-6 left-6 z-[110]">
                <button 
                  onClick={() => setStreamInfo(null)}
                  className="p-3 bg-black/50 hover:bg-black/80 rounded-full border border-white/10 text-white transition-all backdrop-blur-md"
                >
                   <ChevronLeft className="w-8 h-8" />
                </button>
            </div>

            <ArtPlayer
              getInstance={(art: any) => {
                artInstance.current = art;
                
                // HARD SEEKING: Re-request the stream bridge with new start_time
                art.on('video:seeking', () => {
                   const currentTime = art.video.currentTime;
                   const isProxy = streamInfo.url.includes('/stream-bridge/') || streamInfo.url.includes('/play-compat/');
                   if (isProxy) {
                      const baseUrl = streamInfo.url.split('?')[0];
                      const params = streamInfo.url.split('?')[1].split('&').filter((p:string) => !p.startsWith('start_time')).join('&');
                      const newUrl = `${baseUrl}?${params}&start_time=${currentTime}`;
                      art.switchUrl(newUrl);
                   }
                });

                // DURATION PROTECTION: Force actual duration from metadata
                art.on('video:durationchange', () => {
                   if (streamInfo.duration && Math.abs(art.video.duration - streamInfo.duration) > 5) {
                      Object.defineProperty(art.video, 'duration', {
                         configurable: true,
                         get: () => streamInfo.duration
                      });
                   }
                });
              }}
              option={{
                url: streamInfo.url,
                autoplay: true,
                muted: true,
                autoSize: true,
                type: streamInfo.isHls ? 'm3u8' : 'mp4',
                duration: streamInfo.duration || 3600,
                title: movie.title,
                poster: movie.poster || movie.cover,
                volume: 0.7,
                isLive: false,
                pip: true,
                screenshot: true,
                setting: true,
                loop: false,
                flip: true,
                playbackRate: true,
                aspectRatio: true,
                subtitle: {
                   url: streamInfo.subtitles && streamInfo.subtitles.length > 0 
                        ? `http://localhost:8000/sub-proxy?u=${encodeURIComponent(streamInfo.subtitles[0].filePath)}` 
                        : '',
                   type: 'vtt',
                   style: { color: '#fff', fontSize: '24px' },
                   encoding: 'utf-8'
                },
                fullscreen: true,
                fullscreenWeb: true,
                subtitleOffset: true,
                miniProgressBar: true,
                mutex: true,
                backdrop: true,
                playsInline: true,
                autoPlayback: true,
                airplay: true,
                theme: '#dc2626',
                moreVideoAttr: {
                   crossOrigin: 'anonymous',
                },
                customType: {
                  m3u8: function (video: HTMLVideoElement, url: string, art: any) {
                    if (Hls.isSupported()) {
                      if (art.hls) art.hls.destroy();
                      const hls = new Hls({
                         xhrSetup: function(xhr: any) {
                            xhr.setRequestHeader('User-Agent', 'ExoPlayerLib/2.18.7');
                            if (streamInfo.cookie) {
                               xhr.setRequestHeader('Cookie', streamInfo.cookie);
                            }
                         }
                      });
                      hls.loadSource(url);
                      hls.attachMedia(video);
                      art.hls = hls;
                      art.on('destroy', () => hls.destroy());
                    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
                      video.src = url;
                    }
                  },
                },
              }}
              className="w-full h-full"
            />
         </div>
      )}
      {/* Language Selector Modal */}
      {showLanguageModal && (
        <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/80 backdrop-blur-sm transition-all duration-300">
           <div 
             className="w-full sm:max-w-md bg-zinc-900/90 sm:rounded-3xl border-t sm:border border-white/10 overflow-hidden animate-in slide-in-from-bottom duration-300 shadow-2xl"
             onClick={e => e.stopPropagation()}
           >
              <div className="flex items-center justify-between px-6 py-5 border-b border-white/5">
                 <h3 className="text-xl font-bold flex items-center gap-2">
                    <Languages size={22} className="text-red-500" /> Select Language
                 </h3>
                 <button onClick={() => setShowLanguageModal(false)} className="p-2 hover:bg-white/5 rounded-full">
                    <X size={24} />
                 </button>
              </div>
              <div className="p-4 flex flex-col gap-2 max-h-[60vh] overflow-y-auto custom-scrollbar">
                 <button 
                   onClick={() => { 
                      setSelectedLanguage(null); 
                      setShowLanguageModal(false);
                      // Instant play with default audio
                      if (episodes.length > 0) getStream(seasons[selectedSeasonIdx].seasonNumber, episodes[0].episodeNumber);
                      else getStream(0, 0);
                   }}
                   className={`flex items-center justify-between px-6 py-5 rounded-2xl text-left transition-all ${
                    !selectedLanguage ? 'bg-red-600/10 border border-red-600/30 text-red-500 font-bold' : 'bg-white/5 hover:bg-white/10'
                   }`}
                 >
                    Original Audio
                    {!selectedLanguage && <div className="w-2 h-2 rounded-full bg-red-600 shadow-[0_0_10px_rgba(220,38,38,0.8)]" />}
                 </button>
                 
                 {movie.languages?.map((lang: any, idx: number) => (
                    <button 
                      key={idx}
                      onClick={() => { 
                         setSelectedLanguage(lang); 
                         setShowLanguageModal(false);
                         // Instant play with selected dub
                         // Note: We use the context of current episodes, but the target ID is changed in getStream
                         if (episodes.length > 0) getStream(seasons[selectedSeasonIdx].seasonNumber, episodes[0].episodeNumber);
                         else getStream(0, 0);
                      }}
                      className={`flex items-center justify-between px-6 py-5 rounded-2xl text-left transition-all ${
                        selectedLanguage?.subjectId === lang.subjectId && selectedLanguage?.id === lang.id ? 'bg-red-600/10 border border-red-600/30 text-red-500 font-bold' : 'bg-white/5 hover:bg-white/10'
                      }`}
                    >
                       {lang.name}
                       {selectedLanguage?.subjectId === lang.subjectId && selectedLanguage?.id === lang.id && <div className="w-2 h-2 rounded-full bg-red-600 shadow-[0_0_10px_rgba(220,38,38,0.8)]" />}
                    </button>
                 ))}
              </div>
              <div className="px-6 py-6 text-center text-xs text-zinc-500">
                 Choose your preferred audio track before playing.
              </div>
           </div>
        </div>
      )}
    </div>
  );
}

'use client';

import React, { useEffect, useState } from 'react';
import { movieApi, MovieItem } from '@/lib/api';
import { MovieCard } from '@/components/MovieCard';
import { Search, Play, Info, ExternalLink, X, Film, Tv, Clock, Star, ChevronRight, Zap, Download, User, LogOut, CheckCircle, UserPlus, ArrowLeft, Send, Users, Music, Globe, Map, Palette, Gamepad } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function MovieBoxDashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<MovieItem[]>([]);
  const [selectedMovie, setSelectedMovie] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);
  const [episodes, setEpisodes] = useState<any[]>([]);
  const [streamInfo, setStreamInfo] = useState<any>(null);

  const [seasons, setSeasons] = useState<any[]>([]);
  const [selectedSeasonIdx, setSelectedSeasonIdx] = useState(0);
  const [homeSections, setHomeSections] = useState<any[]>([]);
  const [rankingSections, setRankingSections] = useState<any[]>([]);
  const [animeShows, setAnimeShows] = useState<MovieItem[]>([]);
  const [searchSuggestions, setSearchSuggestions] = useState<string[]>([]);
  const [historyItems, setHistoryItems] = useState<MovieItem[]>([]);
  const [watchlistItems, setWatchlistItems] = useState<MovieItem[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<any>(null);
  const [groupPosts, setGroupPosts] = useState<any[]>([]);
  const [selectedTab, setSelectedTab] = useState('home');
  const [groupLoading, setGroupLoading] = useState(false);

  const NAV_ITEMS = [
    { id: 'home', label: 'Home', icon: Play, api: movieApi.getHome, tabId: 1 },
    { id: 'movies', label: 'Movies', icon: Film, api: movieApi.getMovies, tabId: 2 },
    { id: 'anime', label: 'Anime', icon: Zap, api: movieApi.getAnime, tabId: 8 },
    { id: 'short-tv', label: 'Short TV', icon: Tv, api: movieApi.getShortTv, tabId: 13 },
    { id: 'kids', label: 'Kids', icon: Star, api: movieApi.getKids, tabId: 23 },
    { id: 'education', label: 'Education', icon: Info, api: movieApi.getEducation, tabId: 3 },
    { id: 'music', label: 'Music', icon: Music, api: movieApi.getMusic, tabId: 4 },
    { id: 'asian', label: 'Asian', icon: Globe, api: movieApi.getAsian, tabId: 18 },
    { id: 'western', label: 'Western', icon: Map, api: movieApi.getWestern, tabId: 19 },
    { id: 'nollywood', label: 'Nollywood', icon: Palette, api: movieApi.getNollywood, tabId: 28 },
    { id: 'game', label: 'Games', icon: Gamepad, api: movieApi.getGame, tabId: 11 },
  ];

  // Auth State
  const [userInfo, setUserInfo] = useState<any>(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [loginForm, setLoginForm] = useState({ account: '', password: '', otp: '' });
  const [loginLoading, setLoginLoading] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otpLoading, setOtpLoading] = useState(false);

  useEffect(() => {
    fetchTabContent(selectedTab);
    checkAuth();
  }, [selectedTab]);

  const checkAuth = async () => {
    try {
      const res = await movieApi.getUserInfo();
      if (res.logged_in) {
        setUserInfo(res.user);
      } else {
        setUserInfo(null);
      }
    } catch (e) {}
  };

  const fetchUserActivity = async () => {
    try {
      const h = await movieApi.getHistory();
      setHistoryItems(h.data?.list || []);
      const w = await movieApi.getWatchlist();
      setWatchlistItems(w.data?.list || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (userInfo) {
       fetchUserActivity();
       
       // Refresh when returning to the tab/window
       const onFocus = () => fetchUserActivity();
       window.addEventListener('focus', onFocus);
       return () => window.removeEventListener('focus', onFocus);
    }
  }, [userInfo]);

  const fetchTabContent = async (tabId: string) => {
    try {
      setLoading(true);
      const item = NAV_ITEMS.find(n => n.id === tabId);
      if (!item) return;

      const [res, rankRes, suggRes] = await Promise.all([
        item.api(),
        movieApi.getRankings(item.tabId),
        movieApi.getSearchSuggestions()
      ]);

      if (res.data?.list) setHomeSections(res.data.list);
      if (rankRes.data) setRankingSections(rankRes.data);
      
      if (suggRes.data) {
        setSearchSuggestions(suggRes.data);
      }
    } catch (e) {
      console.error('Fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery) return;
    setLoading(true);
    try {
      const res = await movieApi.search(searchQuery);
      // Backend returns data.items for search
      setSearchResults(res.data?.items || []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      movieApi.getSearchSuggestions(searchQuery).then(res => {
        if (res.data) setSearchSuggestions(res.data);
      }).catch(console.error);
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  const handleRequestOtp = async () => {
     if (!loginForm.account) return alert('Email/Phone is required');
     setOtpLoading(true);
     try {
        const res = await movieApi.requestOtp(loginForm.account, 1, authMode === 'register' ? 1 : 2);
        if (res.status === 'success') {
           setOtpSent(true);
           alert('Verification code sent! Please check your inbox/SMS.');
        }
     } catch (err: any) {
        alert(err.response?.data?.detail || 'Failed to send OTP');
     }
     setOtpLoading(false);
  };

  const handleRemoveWatchlist = async (id: string, subjectType: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await movieApi.toggleWatchlist(id, false, subjectType || 1);
      setWatchlistItems(prev => prev.filter(item => (item.subjectId || item.id) !== id));
    } catch (error) {
      console.error("Remove watchlist fail", error);
    }
  };

  const handleRemoveHistory = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await movieApi.deleteHistory(id);
      setHistoryItems(prev => prev.filter(item => (item.subjectId || item.id) !== id));
    } catch (error) {
      console.error("Remove history fail", error);
    }
  };

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginLoading(true);
    try {
      if (authMode === 'login') {
        const res = await movieApi.login(loginForm.account, loginForm.password);
        if (res.status === 'success') {
          setUserInfo(res.user);
          setShowLoginModal(false);
          setSelectedTab('home');
    fetchTabContent('home'); 
        }
      } else {
        if (!loginForm.otp) return alert('Verification code is required for registration');
        const res = await movieApi.register(loginForm.account, loginForm.password, loginForm.otp);
        if (res.status === 'success') {
          alert('Registration Successful! Please Login.');
          setAuthMode('login');
        }
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Authentication Failed';
      alert(`${authMode === 'login' ? 'Login' : 'Registration'} Failed: ${msg}`);
    }
    setLoginLoading(false);
  };

  const handleLogout = async () => {
    await movieApi.logout();
    setUserInfo(null);
    setSelectedTab('home');
    fetchTabContent('home');
  };

  const openMovie = (movie: MovieItem) => {
    const id = movie.subjectId || movie.id;
    if (!id) return;
    
    // Normal Movie/Series or Collection Navigation
    router.push(`/detail/${id}`);
  };

  const openGroup = async (group: any) => {
    setSelectedGroup(group);
    setGroupLoading(true);
    try {
      const res = await movieApi.getGroupPosts();
      setGroupPosts(res.data?.items || []);
    } catch (e) {
      console.error(e);
    }
    setGroupLoading(false);
  };

  const selectSeason = (idx: number) => {
    setSelectedSeasonIdx(idx);
    setEpisodes(seasons[idx].episodes || []);
    setStreamInfo(null);
  };

  const getStream = async (seasonNum: number, epNum: number) => {
    try {
      const res = await movieApi.getStream(selectedMovie.subjectId, seasonNum, epNum);
      if (res.url) {
        setStreamInfo(res);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <main className="min-h-screen bg-black text-white selection:bg-yellow-500 selection:text-black">
      {/* 1. Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-3xl border-b border-white/5 px-6 py-4">
        <div className="max-w-[1920px] mx-auto flex items-center justify-between gap-8">
           {/* LOGO LEFT */}
           <div className="flex items-center gap-3 cursor-pointer group shrink-0" onClick={() => { setSearchResults([]); setSearchQuery(''); setSelectedTab('home'); }}>
             <div className="w-10 h-10 bg-yellow-500 rounded-xl flex items-center justify-center rotate-3 group-hover:rotate-0 transition-transform">
                <Play className="w-6 h-6 text-black fill-black" />
             </div>
             <h1 className="text-xl font-black italic tracking-tighter uppercase hidden sm:block">MovieBox <span className="text-yellow-500">Pro</span></h1>
           </div>

           {/* SEARCH CENTER */}
           <div className="hidden lg:flex flex-col flex-1 max-w-[800px] relative group">
              <form onSubmit={handleSearch} className="flex items-center w-full bg-white/5 rounded-2xl border border-white/10 px-6 py-3 hover:bg-white/10 hover:border-white/20 transition-all focus-within:border-yellow-500/50 focus-within:bg-white/10">
                <Search className="w-5 h-5 text-white/20 group-focus-within:text-yellow-500 transition-colors" />
                <input 
                  type="text" 
                  placeholder="Explore 100k+ Movies & Series..." 
                  className="bg-transparent border-none outline-none flex-1 px-4 text-sm font-medium placeholder:text-zinc-600 focus:placeholder:text-zinc-400"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onFocus={() => setShowSuggestions(true)}
                  onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                />
              </form>
              {/* Suggestions Dropdown */}
              {showSuggestions && searchSuggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-4 bg-zinc-900/90 backdrop-blur-3xl border border-white/10 rounded-3xl p-6 shadow-2xl opacity-100 translate-y-0 z-[60]">
                   <div className="flex items-center gap-3 mb-4">
                      <Zap className="w-4 h-4 text-yellow-500" />
                      <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40">{searchQuery ? "Search Suggestions" : "Trending Searches"}</span>
                   </div>
                   <div className="flex flex-wrap gap-2">
                      {searchSuggestions.map((s, i) => (
                        <button 
                          key={i}
                          onClick={() => { setSearchQuery(s); setShowSuggestions(false); movieApi.search(s).then(r => setSearchResults(r.data?.items || [])); }}
                          className="px-4 py-2 bg-white/5 hover:bg-yellow-500 hover:text-black rounded-xl text-xs font-bold transition-all border border-white/5"
                        >
                          {s}
                        </button>
                      ))}
                   </div>
                </div>
              )}
           </div>

           {/* AUTH RIGHT */}
           <div className="flex items-center gap-6 shrink-0">
               {userInfo ? (
                <div className="flex items-center gap-4">
                   <div className="flex items-center gap-3 bg-yellow-500/10 border border-yellow-500/20 px-4 py-2 rounded-xl">
                      <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
                      <span className="text-[10px] font-black uppercase tracking-widest text-yellow-500">Active Member</span>
                   </div>
                   <button 
                     onClick={() => router.push('/profile')}
                     className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center hover:bg-yellow-500/10 hover:border-yellow-500/20 hover:text-yellow-500 transition-all"
                     title="User Profile"
                   >
                     <User className="w-5 h-5" />
                   </button>
                   <button 
                    onClick={handleLogout}
                    className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center hover:bg-red-500/10 hover:border-red-500/20 hover:text-red-500 transition-all"
                    title="Logout"
                   >
                     <LogOut className="w-5 h-5" />
                   </button>
                </div>
              ) : (
                <button 
                  onClick={() => setShowLoginModal(true)}
                  className="flex items-center gap-3 bg-yellow-500 text-black px-6 py-2.5 rounded-xl font-black text-xs uppercase tracking-widest hover:scale-105 active:scale-95 transition-all shadow-lg shadow-yellow-500/20"
                >
                  <User className="w-4 h-4" />
                  Sign In
                </button>
              )}
           </div>
        </div>
      </nav>

      <div className="flex pt-24 min-h-screen">
        {/* Sidebar */}
        <aside className="w-64 fixed left-0 top-24 bottom-0 bg-black/50 backdrop-blur-3xl border-r border-white/5 overflow-y-auto no-scrollbar hidden xl:block z-40 p-6 space-y-8">
           <div className="space-y-1">
             <p className="text-[10px] font-black uppercase tracking-[0.3em] text-white/20 mb-4 px-4">Catalog</p>
             {NAV_ITEMS.map((item) => (
               <button 
                 key={item.id}
                 onClick={() => { setSelectedTab(item.id); setSearchResults([]); }}
                 className={cn(
                   "w-full flex items-center gap-4 px-4 py-3 rounded-2xl transition-all group",
                   selectedTab === item.id 
                    ? "bg-yellow-500 text-black font-black" 
                    : "text-zinc-500 hover:bg-white/5 hover:text-white"
                 )}
               >
                 <item.icon className={cn("w-5 h-5", selectedTab === item.id ? "fill-black" : "group-hover:text-yellow-500")} />
                 <span className="text-xs uppercase tracking-widest font-bold">{item.label}</span>
               </button>
             ))}
           </div>

           <div className="pt-8 border-t border-white/5">
              <p className="text-[10px] font-black uppercase tracking-[0.3em] text-white/20 mb-4 px-4">Social</p>
              <button 
                onClick={() => { alert('Community feed integrated to sections automatically.'); }}
                className="w-full flex items-center gap-4 px-4 py-3 rounded-2xl text-zinc-500 hover:bg-white/5 hover:text-white transition-all"
              >
                <Users className="w-5 h-5" />
                <span className="text-xs uppercase tracking-widest font-bold">Groups</span>
              </button>
           </div>
        </aside>

        {/* Main Feed Container */}
        <div className="flex-1 xl:ml-64 px-8 pb-20">
         {searchResults.length > 0 ? (
            <section className="animate-in fade-in slide-in-from-bottom-8 duration-700">
               <div className="flex items-center gap-4 mb-10">
                  <div className="w-1.5 h-8 bg-yellow-500 rounded-full" />
                  <h2 className="text-4xl font-black uppercase tracking-tight">Search Results <span className="text-white/20 font-light ml-4">({searchResults.length})</span></h2>
               </div>
               <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-8">
                  {searchResults.map((movie) => (
                    <div key={movie.subjectId} className="transform transition-all hover:scale-105 duration-500">
                       <MovieCard item={movie} onClick={() => openMovie(movie)} />
                    </div>
                  ))}
               </div>
            </section>
         ) : (
            <div className="space-y-20 mt-10">
              {loading ? (
                <div className="py-40 flex flex-col items-center gap-4 animate-in fade-in duration-1000">
                  <div className="w-12 h-12 border-2 border-yellow-500/10 border-t-yellow-500 rounded-full animate-spin" />
                  <p className="text-[10px] font-black tracking-[0.4em] text-white/10 uppercase">Synchronizing Catalog</p>
                </div>
              ) : (
                <>
                  {/* Active Selection Indicator */}
                  <div className="flex items-center gap-4 animate-in fade-in slide-in-from-left-8 duration-700">
                     <div className="px-6 py-2 bg-yellow-500 rounded-full">
                        <span className="text-[10px] font-black uppercase tracking-widest text-black">
                           Browsing: {NAV_ITEMS.find(n => n.id === selectedTab)?.label}
                        </span>
                     </div>
                     <div className="h-px flex-1 bg-white/5" />
                  </div>
                {/* 1. Continue Watching (History) */}
                {userInfo && selectedTab === 'home' && (
                   <section className="animate-in fade-in slide-in-from-left-8 duration-700">
                      <div className="flex items-center justify-between mb-8">
                         <h2 className="text-3xl font-black flex items-center gap-4">
                            <Clock className="w-8 h-8 text-blue-500" />
                            Continue Watching
                         </h2>
                      </div>
                      {historyItems.length > 0 ? (
                        <div className="flex gap-6 overflow-x-auto no-scrollbar pb-6">
                           {historyItems.map((movie, i) => (
                               <div key={movie.subjectId || movie.id || `history-${i}`} className="relative flex-none w-36 md:w-48 group">
                                 <div onClick={() => openMovie(movie)} className="cursor-pointer">
                                   <MovieCard item={movie} onClick={() => openMovie(movie)} />
                                 </div>
                                 <button 
                                   onClick={(e) => {
                                     e.stopPropagation();
                                     handleRemoveHistory((movie.subjectId || movie.id) as string, e);
                                   }}
                                   className="absolute top-2 right-2 p-1.5 bg-black/60 hover:bg-black/90 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity z-20"
                                   title="Remove from history"
                                 >
                                   <X className="w-4 h-3" />
                                 </button>
                                 {movie.seeTime && (
                                   <div className="absolute bottom-0 left-0 right-0 h-1 bg-zinc-800 z-10">
                                     <div 
                                       className="h-full bg-red-600" 
                                       style={{ width: `${Math.min(100, (movie.seeTime / 3600) * 100)}%` }}
                                     />
                                   </div>
                                 )}
                               </div>
                           ))}
                        </div>
                      ) : (
                        <div className="py-16 bg-white/5 rounded-[2.5rem] border border-dashed border-white/10 flex flex-col items-center justify-center text-center group hover:bg-white/[0.07] transition-all">
                           <div className="w-12 h-12 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                              <Play className="w-6 h-6 text-blue-500/40" />
                           </div>
                           <p className="text-white/20 font-black uppercase tracking-[0.3em] text-[10px]">Your history is empty</p>
                           <p className="text-white/10 text-[9px] mt-2 font-medium">Start watching content to see your progress here</p>
                        </div>
                      )}
                   </section>
                )}

                {/* 2. My Watchlist / Want to Watch */}
                {userInfo && selectedTab === 'home' && (
                   <section className="animate-in fade-in slide-in-from-left-8 duration-700">
                      <div className="flex items-center justify-between mb-8">
                         <h2 className="text-3xl font-black flex items-center gap-4">
                            <Star className="w-8 h-8 text-yellow-500 fill-yellow-500" />
                            My Watchlist
                         </h2>
                      </div>
                      {watchlistItems.length > 0 ? (
                        <div className="flex gap-6 overflow-x-auto no-scrollbar pb-6 scroll-smooth">
                           {watchlistItems.map((movie, i) => (
                              <div key={movie.subjectId || i} className="relative w-[180px] shrink-0 transform transition-all hover:scale-105 group">
                                 <div onClick={() => openMovie(movie)} className="cursor-pointer">
                                   <MovieCard item={movie} onClick={() => openMovie(movie)} />
                                 </div>
                                 <button 
                                   onClick={(e) => {
                                     e.stopPropagation();
                                     handleRemoveWatchlist((movie.subjectId || movie.id) as string, movie.subjectType || 1, e);
                                   }}
                                   className="absolute top-2 right-2 p-1.5 bg-black/60 hover:bg-black/90 text-yellow-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity z-20"
                                   title="Remove from watchlist"
                                 >
                                   <X className="w-4 h-4" />
                                 </button>
                              </div>
                           ))}
                        </div>
                      ) : (
                        <div className="py-16 bg-white/5 rounded-[2.5rem] border border-dashed border-white/10 flex flex-col items-center justify-center text-center group hover:bg-white/[0.07] transition-all">
                           <div className="w-12 h-12 bg-yellow-500/10 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                              <Star className="w-6 h-6 text-yellow-500/40" />
                           </div>
                           <p className="text-white/20 font-black uppercase tracking-[0.3em] text-[10px]">Your cloud watchlist is empty</p>
                           <p className="text-white/10 text-[9px] mt-2 font-medium">Add movies to your "Want to See" list to sync them here</p>
                        </div>
                      )}
                   </section>
                )}

                {/* 3. Browse Content Sections (ALWAYS SHOW FOR GUEST) */}
                {homeSections.map((section, idx) => (
                  <section key={idx} className="animate-in fade-in slide-in-from-bottom-12 duration-1000">
                    <div className="flex items-center justify-between mb-8">
                      <div className="flex items-center gap-4">
                        <div className={`w-1 h-8 ${section.type === 'groups' ? 'bg-blue-500 shadow-blue-500/50' : 'bg-yellow-500'} rounded-full shadow-lg`} />
                        <h2 className="text-4xl font-black uppercase tracking-tight italic flex items-center gap-3">
                           {section.type === 'groups' && <Users className="w-8 h-8 text-blue-500" />}
                           {section.title}
                        </h2>
                      </div>
                      {section.type !== 'groups' && (
                        <button className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-white/20 hover:text-yellow-500 transition-colors group">
                          View Collection <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                        </button>
                      )}
                    </div>
                    
                    <div className="flex gap-8 overflow-x-auto no-scrollbar pb-10">
                      {section.type === 'groups' ? (
                        section.items.map((group: any, i: number) => (
                          <div key={`group-${i}`} onClick={() => openGroup(group)} className="w-[300px] shrink-0 p-6 bg-white/5 rounded-[2rem] border border-white/10 hover:border-blue-500/50 hover:bg-white/10 transition-all group cursor-pointer">
                             <div className="flex items-center gap-4 mb-4">
                               <div className="w-14 h-14 rounded-2xl overflow-hidden border border-white/10 group-hover:scale-110 transition-transform">
                                  <img src={group.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(group.name)}&background=2563eb&color=fff`} className="w-full h-full object-cover" />
                               </div>
                               <div className="flex-1 min-w-0">
                                  <h3 className="font-black italic uppercase text-lg truncate">{group.name}</h3>
                                  <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">
                                    {parseInt(group.postCount).toLocaleString()} Posts
                                  </p>
                                </div>
                             </div>
                             <div className="flex items-center justify-between mt-auto pt-2">
                                <div className="flex -space-x-2">
                                  {[1,2,3].map(j => (
                                    <div key={j} className="w-6 h-6 rounded-full bg-zinc-800 border-2 border-black" />
                                  ))}
                                </div>
                                <button className="px-4 py-1.5 bg-blue-600/20 text-blue-500 text-[10px] font-black rounded-lg uppercase tracking-widest hover:bg-blue-600 hover:text-white transition-all">
                                   Join Group
                                </button>
                             </div>
                          </div>
                        ))
                      ) : (
                        section.items.map((movie: any, i: number) => (
                          <div key={`${movie.subjectId}-${i}`} className="w-[200px] shrink-0 transform transition-all hover:scale-105 duration-500">
                             <MovieCard item={movie} onClick={() => openMovie(movie)} />
                          </div>
                        ))
                      )}
                    </div>
                  </section>
                ))}



                {/* 4. Ranking Sections (NEW) */}
                {rankingSections.map((rank, i) => (
                  <section key={`rank-${i}`} className="animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-300">
                    <div className="flex items-center justify-between mb-8">
                      <div className="flex items-center gap-4">
                        <div className="w-1 h-8 bg-red-600 rounded-full shadow-lg shadow-red-600/50" />
                        <h2 className="text-4xl font-black uppercase tracking-tight italic flex items-center gap-3">
                           <Film className="w-8 h-8 text-red-600" />
                           {rank.title}
                        </h2>
                      </div>
                    </div>
                    <div className="flex gap-8 overflow-x-auto no-scrollbar pb-10">
                      {rank.items.map((movie: any, j: number) => (
                        <div key={j} className="w-[180px] shrink-0 transform transition-all hover:scale-105 duration-500 rounded-3xl overflow-hidden relative border border-white/5 hover:border-red-600/50">
                           <div className="absolute top-2 left-2 z-10 w-8 h-8 bg-black/60 backdrop-blur-md rounded-lg flex items-center justify-center font-black text-red-500 border border-white/10 italic">
                             #{j + 1}
                           </div>
                           <MovieCard item={movie} onClick={() => openMovie(movie)} />
                        </div>
                      ))}
                    </div>
                  </section>
                ))}
              </>
            )}
           </div>
         )}
      </div>

      {/* 3. Auth Modal */}
      {showLoginModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 animate-in fade-in duration-300">
           <div className="absolute inset-0 bg-black/90 backdrop-blur-3xl" onClick={() => setShowLoginModal(false)} />
           <div className="relative w-full max-w-[440px] bg-zinc-950 border border-white/10 rounded-[3rem] p-12 overflow-hidden shadow-2xl">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-yellow-500 to-yellow-600" />
              
              <div className="flex flex-col items-center mb-10">
                 <div className="w-16 h-16 bg-yellow-500 rounded-2xl flex items-center justify-center rotate-6 mb-6 shadow-xl shadow-yellow-500/20">
                    <User className="w-8 h-8 text-black" />
                 </div>
                 <h2 className="text-3xl font-black uppercase tracking-tighter italic">
                   {authMode === 'login' ? 'Welcome Back' : 'Join the Club'}
                 </h2>
                 <p className="text-white/40 text-[10px] font-bold uppercase tracking-[0.3em] mt-2">Personalize Your Cinematic Experience</p>
              </div>

              <form onSubmit={handleAuth} className="space-y-4">
                 <div className="space-y-1.5">
                    <label className="text-[9px] font-black uppercase tracking-widest text-white/30 ml-4">Account ID</label>
                    <div className="relative group">
                       <User className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-yellow-500 transition-colors" />
                       <input 
                        type="text" 
                        placeholder="Email or Phone Number"
                        className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-14 pr-6 text-sm font-bold focus:border-yellow-500/50 focus:bg-white/10 transition-all outline-none"
                        value={loginForm.account}
                        onChange={(e) => setLoginForm({ ...loginForm, account: e.target.value })}
                       />
                    </div>
                 </div>

                 <div className="space-y-1.5">
                    <label className="text-[9px] font-black uppercase tracking-widest text-white/30 ml-4">
                      {authMode === 'login' ? 'Access Key' : 'Create Password'}
                    </label>
                    <div className="relative group">
                       <Zap className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-yellow-500 transition-colors" />
                       <input 
                        type="password" 
                        placeholder={authMode === 'login' ? "••••••••••••" : "Choose a secure password"}
                        className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-14 pr-6 text-sm font-bold focus:border-yellow-500/50 focus:bg-white/10 transition-all outline-none"
                        value={loginForm.password}
                        onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                       />
                    </div>
                 </div>

                 {authMode === 'register' && (
                   <div className="space-y-3 pt-2">
                       <div className="flex items-center gap-2">
                          <div className="h-px flex-1 bg-white/5" />
                          <span className="text-[8px] font-black uppercase tracking-widest text-white/10">Verification Zone</span>
                          <div className="h-px flex-1 bg-white/5" />
                       </div>
                       <div className="flex gap-2">
                         <div className="relative flex-1 group">
                            <Send className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
                            <input 
                              type="text" 
                              placeholder="6-Digit OTP"
                              className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-14 pr-6 text-sm font-bold outline-none"
                              value={loginForm.otp}
                              onChange={(e) => setLoginForm({ ...loginForm, otp: e.target.value })}
                            />
                         </div>
                         <button 
                           type="button"
                           onClick={handleRequestOtp}
                           className="px-6 bg-white/5 border border-white/10 rounded-2xl font-black text-[9px] uppercase tracking-widest hover:bg-yellow-500 hover:text-black transition-all disabled:opacity-50"
                           disabled={otpLoading || otpSent}
                         >
                            {otpLoading ? '...' : otpSent ? 'SENT' : 'SEND'}
                         </button>
                       </div>
                   </div>
                 )}

                 <button 
                  type="submit" 
                  className="w-full bg-yellow-500 text-black py-5 rounded-2xl font-black text-xs uppercase tracking-[0.2em] shadow-xl shadow-yellow-500/20 hover:scale-[1.02] active:scale-[0.98] transition-all mt-6 disabled:opacity-50"
                  disabled={loginLoading}
                 >
                   {loginLoading ? 'Synchronizing...' : authMode === 'login' ? 'Authenticate Account' : 'Create Official Account'}
                 </button>
              </form>

              <div className="mt-8 pt-8 border-t border-white/5 text-center">
                 <button 
                  onClick={() => { setAuthMode(authMode === 'login' ? 'register' : 'login'); setOtpSent(false); }}
                  className="text-[10px] font-black uppercase tracking-widest text-white/20 hover:text-yellow-500 transition-colors"
                 >
                   {authMode === 'login' ? "Don't have an access key? Join now" : "Already a member? Secure Login"}
                 </button>
              </div>
           </div>
        </div>
      )}
      {/* Community Group Modal */}
      {selectedGroup && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 animate-in fade-in duration-300">
           <div className="absolute inset-0 bg-black/90 backdrop-blur-3xl" onClick={() => setSelectedGroup(null)} />
           <div className="relative w-full max-w-4xl bg-zinc-950 border border-white/10 rounded-[3rem] p-10 overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
              <div className="flex items-center gap-6 mb-8">
                 <div className="w-20 h-20 rounded-3xl overflow-hidden border-2 border-blue-500/50 shadow-xl shadow-blue-500/20">
                    <img src={selectedGroup?.avatar} className="w-full h-full object-cover" />
                 </div>
                 <div className="flex-1">
                    <h2 className="text-4xl font-black italic uppercase tracking-tighter">{selectedGroup?.name}</h2>
                    <p className="text-zinc-500 font-bold uppercase tracking-widest text-[10px]">Official Discussion Group • {parseInt(selectedGroup?.postCount || '0').toLocaleString()} Posts</p>
                 </div>
                 <button onClick={() => setSelectedGroup(null)} className="p-3 bg-white/5 rounded-full hover:bg-white/10 transition-all border border-white/10">
                    <X className="w-6 h-6" />
                 </button>
              </div>

              <div className="flex-1 overflow-y-auto pr-4 no-scrollbar space-y-6">
                 {groupLoading ? (
                    <div className="flex flex-col items-center justify-center py-32 space-y-4">
                       <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
                       <p className="text-[10px] font-black uppercase tracking-[0.3em] text-white/20">Syncing Group Feed...</p>
                    </div>
                 ) : groupPosts.length > 0 ? (
                    groupPosts.map((post, i) => (
                      <div key={i} className="p-8 bg-white/5 rounded-[2.5rem] border border-white/5 space-y-4 group hover:bg-white/[0.08] transition-all">
                         <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-2xl bg-zinc-800 border border-white/10" />
                            <div className="flex-1">
                               <p className="font-black italic uppercase text-sm tracking-tight">{post.username || 'Fan User'}</p>
                               <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest leading-none">{post.createTime}</p>
                            </div>
                         </div>
                         <p className="text-zinc-300 text-sm leading-relaxed font-medium">{post.content}</p>
                      </div>
                    ))
                 ) : (
                    <div className="py-32 flex flex-col items-center justify-center text-center">
                       <div className="w-16 h-16 bg-blue-500/10 rounded-3xl flex items-center justify-center mb-6">
                          <Users className="w-8 h-8 text-blue-500" />
                       </div>
                       <p className="text-xl font-black uppercase italic tracking-tighter">Community Sync in Progress</p>
                       <p className="text-zinc-500 text-[10px] uppercase tracking-widest mt-2 font-bold max-w-xs">Connecting to secure community feed. If posts don't appear, try sending a first message to initiate the thread.</p>
                       
                       <div className="mt-10 w-full max-w-md space-y-4">
                          <textarea 
                             placeholder="Write a message to this community..."
                             className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 text-sm font-medium outline-none focus:border-blue-500 transition-all resize-none h-32"
                          />
                          <button className="w-full bg-blue-600 py-4 rounded-xl font-black uppercase tracking-widest text-xs hover:scale-[1.02] active:scale-[0.98] transition-all shadow-xl shadow-blue-600/20">
                             Post to Group
                          </button>
                       </div>
                    </div>
                 )}
              </div>
           </div>
        </div>
      )}
        </div>
    </main>
  );
}

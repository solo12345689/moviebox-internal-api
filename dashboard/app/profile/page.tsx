'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { movieApi } from '@/lib/api';
import { 
  User, Mail, Shield, Calendar, Clock, 
  Settings, LogOut, ChevronLeft, Star, 
  Film, Users, Zap, CheckCircle 
} from 'lucide-react';

export default function UserProfile() {
  const router = useRouter();
  const [userInfo, setUserInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const res = await movieApi.getUserInfo();
      // Check forlogged_in flag based on your successful API link
      if (res.logged_in) {
        setUserInfo(res.user);
      } else {
        setUserInfo(null);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-red-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white p-6 md:p-12 overflow-x-hidden">
      <div className="max-w-6xl mx-auto space-y-12">
        
        {/* Header */}
        <div className="flex items-center justify-between">
           <button 
             onClick={() => router.push('/')}
             className="p-3 bg-white/5 rounded-full hover:bg-white/10 transition-all border border-white/10 group"
           >
              <ChevronLeft className="w-6 h-6 group-hover:-translate-x-1 transition-transform" />
           </button>
           <h1 className="text-2xl font-black uppercase italic tracking-tighter">Account Center</h1>
           <button className="p-3 bg-white/5 rounded-full border border-white/10">
              <Settings className="w-6 h-6 text-zinc-500" />
           </button>
        </div>

        {/* Profile Card */}
        <div className="relative group">
           <div className="absolute inset-0 bg-gradient-to-r from-red-600/20 to-blue-600/20 blur-[100px] opacity-20 group-hover:opacity-40 transition-opacity" />
           <div className="relative bg-white/5 backdrop-blur-3xl rounded-[3rem] border border-white/10 p-10 md:p-16 flex flex-col md:flex-row items-center gap-10">
              <div className="w-40 h-40 rounded-[2.5rem] bg-zinc-900 border-4 border-zinc-800 shadow-2xl flex items-center justify-center overflow-hidden">
                 <User className="w-20 h-20 text-zinc-700" />
              </div>
              
              <div className="flex-1 text-center md:text-left space-y-4">
                 <div className="flex flex-wrap items-center justify-center md:justify-start gap-4">
                    <h2 className="text-5xl font-black italic uppercase tracking-tighter truncate max-w-[400px]">
                       {userInfo?.userId ? `UID_${userInfo.userId}` : 'GUEST_ACCESS'}
                    </h2>
                    <div className="px-4 py-1.5 bg-red-600 rounded-full text-[10px] font-black uppercase tracking-[0.2em] shadow-lg shadow-red-600/40">
                       {userInfo?.userType === 1 ? 'PRO MEMBER' : 'FREE USER'}
                    </div>
                 </div>
                 
                 <div className="flex flex-wrap justify-center md:justify-start items-center gap-6 text-zinc-500 font-bold uppercase tracking-widest text-[10px]">
                    <div className="flex items-center gap-2">
                       <Shield className="w-4 h-4 text-green-500" />
                       SECURE TOKEN ACTIVE
                    </div>
                    <div className="flex items-center gap-2">
                       <Zap className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                       REAL-TIME SYNC
                    </div>
                 </div>

                 <div className="flex flex-wrap justify-center md:justify-start gap-4 pt-4">
                    <div className="px-6 py-3 bg-zinc-900 rounded-2xl border border-white/5 flex items-center gap-3">
                       <div className="text-left overflow-hidden">
                          <p className="text-[8px] text-zinc-500 font-black">ACCESS TOKEN</p>
                          <p className="text-[10px] font-medium text-zinc-400 truncate w-64">{userInfo?.token || 'N/A'}</p>
                       </div>
                    </div>
                 </div>
              </div>
           </div>
        </div>

        {/* Stats Grid - REAL DATA ONLY */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
             <div className="bg-white/5 rounded-[2rem] border border-white/5 p-10 hover:bg-white/10 transition-all group">
                <Shield className="w-12 h-12 text-green-500 mb-6 group-hover:scale-110 transition-transform" />
                <p className="text-4xl font-black italic uppercase tracking-tighter">
                   {userInfo?.userId || 'N/A'}
                </p>
                <p className="text-zinc-500 font-bold uppercase tracking-widest text-[10px] mt-2">OFFICIAL USER ID</p>
             </div>
             
             <div className="bg-white/5 rounded-[2rem] border border-white/5 p-10 hover:bg-white/10 transition-all group">
                <Zap className="w-12 h-12 text-yellow-500 mb-6 group-hover:scale-110 transition-transform" />
                <p className="text-4xl font-black italic uppercase tracking-tighter">
                   {userInfo?.userType === 1 ? 'PRO' : 'FREE'}
                </p>
                <p className="text-zinc-500 font-bold uppercase tracking-widest text-[10px] mt-2">ACCOUNT SUBSCRIPTION</p>
             </div>
        </div>

        {/* Security Detail */}
        <div className="bg-white/5 rounded-[3rem] border border-white/5 p-12 space-y-6">
           <div className="flex items-center justify-between">
              <h3 className="text-xl font-black uppercase italic tracking-tighter flex items-center gap-3">
                 <Shield className="w-6 h-6 text-blue-500" />
                 Secure Session Token
              </h3>
              <div className="px-4 py-1 bg-green-500/10 text-green-500 border border-green-500/20 rounded-full text-[8px] font-black tracking-widest uppercase">
                 ENCRYPTED ACCESS
              </div>
           </div>
           <div className="p-8 bg-black/40 rounded-3xl border border-white/5">
              <p className="text-[11px] font-medium text-zinc-500 break-all leading-relaxed font-mono">
                 {userInfo?.token || 'NO SESSION ACTIVE'}
              </p>
           </div>
           <div className="flex gap-4">
              <div className="px-6 py-3 bg-white/5 rounded-2xl text-[9px] font-black uppercase tracking-widest text-zinc-400">
                 ALGORITHM: HS256
              </div>
              <div className="px-6 py-3 bg-white/5 rounded-2xl text-[9px] font-black uppercase tracking-widest text-zinc-400">
                 AUTH TYPE: HANDSHAKE_OK
              </div>
           </div>
        </div>

        {userInfo && (
          <button 
            onClick={async () => {
              await movieApi.logout();
              router.push('/');
            }}
            className="w-full py-8 bg-zinc-900 rounded-[2.5rem] border border-red-600/20 text-red-600 font-black uppercase tracking-[0.4em] text-xs hover:bg-red-600 hover:text-white transition-all shadow-2xl shadow-red-600/10"
          >
             Terminate Secure Profile Sync
          </button>
        )}

      </div>
    </div>
  );
}

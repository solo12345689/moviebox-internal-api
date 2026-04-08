import React, { useEffect, useRef, memo } from 'react';
import Artplayer from 'artplayer';

declare global {
  interface Window {
    Hls: any;
    dashjs: any;
  }
}

interface VideoPlayerProps {
  url: string;
  cookie: string;
  poster?: string;
  duration?: number;
  subtitleUrl?: string | null;
  onProgress?: (progress: number) => void;
  onError?: (error: any) => void;
  startTime?: number;
}

const VideoPlayer = memo(({ 
  url, 
  cookie, 
  poster, 
  duration = 1440,
  subtitleUrl, 
  onProgress, 
  onError,
  startTime = 0 
}: VideoPlayerProps) => {
  const artRef = useRef<HTMLDivElement>(null);
  const artInstance = useRef<Artplayer | null>(null);
  const seekOffset = useRef<number>(startTime);
  const isSeekingInternal = useRef<boolean>(false);
  
  useEffect(() => {
    if (!artRef.current) return;
    if (artInstance.current) return;

    const getProxiedUrl = (u: string, cookieStr: string, start?: number) => {
        let cleanUrl = u;
        if (u.includes('proxy-media?url=')) {
            const up = new URL(u);
            cleanUrl = up.searchParams.get('url') || u;
        }
        if (cleanUrl.includes('localhost') || cleanUrl.includes('127.0.0.1')) {
            const up = new URL(cleanUrl);
            if (start && start > 0) up.searchParams.set('start_time', start.toString());
            else up.searchParams.delete('start_time');
            return up.toString();
        }
        let pUrl = `http://localhost:8000/proxy-media?url=${encodeURIComponent(cleanUrl)}&cookie=${encodeURIComponent(cookieStr)}`;
        if (start && start > 0) pUrl += `&start_time=${start}`;
        return pUrl;
    };

    const initialUrl = getProxiedUrl(url, cookie, startTime);
    seekOffset.current = startTime;

    const art = new Artplayer({
      container: artRef.current,
      url: initialUrl,
      volume: 1.0,
      isLive: false,
      muted: false,
      autoplay: true,
      pip: true,
      autoSize: true,
      autoMini: true,
      screenshot: true,
      setting: true,
      playbackRate: true,
      aspectRatio: true,
      fullscreen: true,
      fullscreenWeb: true,
      subtitleOffset: true,
      miniProgressBar: true,
      mutex: true,
      backdrop: true,
      playsInline: true,
      theme: '#E11D48',
      poster: poster,
      videoAttributes: { crossOrigin: 'anonymous' },
      subtitle: {
        url: subtitleUrl || '',
        type: 'vtt',
        style: { color: '#FF0', fontSize: '24px' },
        encoding: 'utf-8',
        escape: false
      },
      customType: {
        m3u8: function (video: HTMLMediaElement, url: string) {
          const Hls = window.Hls;
          if (Hls && Hls.isSupported()) {
            const hls = new Hls();
            hls.loadSource(url);
            hls.attachMedia(video);
          } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
            video.src = url;
          }
        },
      },
    });

    artInstance.current = art;

    // === VIRTUAL TIMELINE ENGINE (for transcoded/live FFMPEG streams) ===
    // This runs AFTER the player is created, so we can safely access art.video
    art.on('ready', () => {
      const isTranscoded = art.url.includes('play-compat');
      if (!isTranscoded || !duration || duration <= 0) return;

      try {
        const nativeCT = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, 'currentTime');

        // MOCK currentTime so ArtPlayer sees the "virtual" global position
        Object.defineProperty(art.video, 'currentTime', {
          get: () => {
            const realTime = nativeCT?.get?.call(art.video) ?? 0;
            return seekOffset.current + realTime;
          },
          set: (targetTime: number) => {
            if (isSeekingInternal.current) return;
            const realTimeNow = nativeCT?.get?.call(art.video) ?? 0;
            const virtualTimeNow = seekOffset.current + realTimeNow;

            if (Math.abs(targetTime - virtualTimeNow) > 4) {
              isSeekingInternal.current = true;
              console.info(`[VIRTUAL VOD] Re-tuning to ${targetTime}s...`);
              seekOffset.current = targetTime;
              const newUrl = getProxiedUrl(art.url, '', targetTime);
              art.video.src = newUrl;
              art.video.load();
              art.video.onloadedmetadata = () => {
                isSeekingInternal.current = false;
                art.play();
              };
            }
          },
          configurable: true,
        });

        // MOCK duration so ArtPlayer allows the full seekable range
        Object.defineProperty(art.video, 'duration', {
          get: () => duration,
          configurable: true,
        });
        art.emit('video:durationchange');

        // Continuous UI sync loop — keeps the labels correct as the stream plays
        const syncUI = () => {
          try {
            if (!isSeekingInternal.current) {
              const realTimeNow = nativeCT?.get?.call(art.video) ?? 0;
              const virtualTimeNow = seekOffset.current + realTimeNow;
              const p = Math.min((virtualTimeNow / duration) * 100, 100);

              const curLabel = artRef.current?.querySelector('.art-time-current');
              if (curLabel) curLabel.textContent = Artplayer.utils.secondToTime(virtualTimeNow);
              const durLabel = artRef.current?.querySelector('.art-time-duration');
              if (durLabel) durLabel.textContent = Artplayer.utils.secondToTime(duration);
              const pb = artRef.current?.querySelector('.art-progress-played') as HTMLDivElement;
              if (pb) pb.style.width = `${p}%`;
              const pi = artRef.current?.querySelector('.art-progress-indicator') as HTMLDivElement;
              if (pi) pi.style.left = `${p}%`;
            }

            // Re-lock duration in case the browser resets it
            if (Math.abs(art.video.duration - duration) > 1) {
              Object.defineProperty(art.video, 'duration', { get: () => duration, configurable: true });
              art.emit('video:durationchange');
            }
          } catch (e) {}
        };

        art.on('video:timeupdate', syncUI);
        const t = setInterval(syncUI, 1000);
        art.on('destroy', () => clearInterval(t));
      } catch (e) {
        console.error('[VIRTUAL VOD] Setup failed:', e);
      }
    });

    art.on('video:timeupdate', () => {
      if (!isSeekingInternal.current && onProgress) {
        // art.video.currentTime is intercepted for transcoded streams, so this auto-reports the correct virtual time
        onProgress(art.video.currentTime);
      }
    });

    return () => {
      if (artInstance.current) {
        artInstance.current.destroy(false);
        artInstance.current = null;
      }
    };
  }, []); // PIN — only mount once

  // Silent subtitle sync without reloading the video
  useEffect(() => {
    if (artInstance.current) {
      const art = artInstance.current;
      if (subtitleUrl) {
        art.subtitle.url = subtitleUrl;
        art.subtitle.show = true;
      } else {
        art.subtitle.show = false;
      }
    }
  }, [subtitleUrl]);

  return <div ref={artRef} className="w-full h-full rounded-[2.5rem] overflow-hidden shadow-2xl border border-white/10" />;
});

export default VideoPlayer;

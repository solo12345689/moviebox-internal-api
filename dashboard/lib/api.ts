import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance with credentials enabled for session cookies
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

export interface MovieItem {
  subjectId: string;
  id?: string;
  title: string;
  name?: string;
  cover: string;
  poster?: string;
  description?: string;
  score?: string;
  releaseTime?: string;
  subjectType?: number; // 1: Movie, 2: TV
  seeTime?: number;
  status?: number;
  season?: number;
  episode?: number;
  actionType?: string;
  categoryId?: string;
}

export const movieApi = {
  getHome: async (page = 1) => {
    const res = await api.get('/home', { params: { page } });
    return res.data;
  },
  getMovies: async (page = 1) => {
    const res = await api.get('/movies', { params: { page } });
    return res.data;
  },
  search: async (q: string, page = 1) => {
    const res = await api.get('/search', { params: { q, page } });
    return res.data;
  },
  getDetail: async (id: string) => {
    const res = await api.get(`/detail/${id}`);
    return res.data;
  },
  getEpisodes: async (id: string, page = 1) => {
    const res = await api.get(`/episodes/${id}`, { params: { page } });
    return res.data;
  },
  getStream: async (id: string, season = 1, episode = 1, quality?: string, resource_id?: string) => {
    const res = await api.get(`/stream/${id}`, { params: { season, episode, quality, resource_id } });
    return res.data;
  },
  requestOtp: async (account: string, authType = 1, type = 1) => {
    const res = await api.post('/request-otp', { account, authType, type });
    return res.data;
  },
  login: async (account: string, password: string, authType = 1) => {
    const res = await api.post('/login', { account, password, authType });
    return res.data;
  },
  register: async (account: string, password: string, otp: string, authType = 1) => {
    const res = await api.post('/register', { account, password, otp, authType });
    return res.data;
  },
  logout: async () => {
    const res = await api.post('/logout');
    return res.data;
  },
  getUserInfo: async () => {
    const res = await api.get('/user-info');
    return res.data;
  },
  getHistory: async (page = 1) => {
    const res = await api.get('/history', { params: { page } });
    return res.data;
  },
  getWatchlist: async (page = 1) => {
    const res = await api.get('/watchlist', { params: { page } });
    return res.data;
  },
  toggleWatchlist: async (subjectId: string, active: boolean, subjectType: number = 1) => {
    const res = await api.post('/watchlist/toggle', null, { 
      params: { subject_id: subjectId, active, subject_type: subjectType } 
    });
    return res.data;
  },
  deleteHistory: async (id: string) => {
    const res = await api.post(`/history/delete/${id}`);
    return res.data;
  },
  addToHistory: async (subjectId: string) => {
    const res = await api.post(`/history/add/${subjectId}`);
    return res.data;
  },
  reportProgress: async (subjectId: string, progressMs: number, totalMs: number, status = 1) => {
    const res = await api.post('/history/progress', {
      subject_id: subjectId,
      progress_ms: progressMs,
      total_ms: totalMs,
      status
    });
    return res.data;
  },
  getRankings: async (tabId: number = 1) => {
    const res = await api.get('/rankings', { params: { tabId } });
    return res.data;
  },
  getAnime: async (page = 1) => {
    const res = await api.get('/anime', { params: { page } });
    return res.data;
  },
  getShortTv: async (page = 1) => {
    const res = await api.get('/short-tv', { params: { page } });
    return res.data;
  },
  getKids: async (page = 1) => {
    const res = await api.get('/kids', { params: { page } });
    return res.data;
  },
  getEducation: async (page = 1) => {
    const res = await api.get('/education', { params: { page } });
    return res.data;
  },
  getMusic: async (page = 1) => {
    const res = await api.get('/music', { params: { page } });
    return res.data;
  },
  getAsian: async (page = 1) => {
    const res = await api.get('/asian', { params: { page } });
    return res.data;
  },
  getWestern: async (page = 1) => {
    const res = await api.get('/western', { params: { page } });
    return res.data;
  },
  getNollywood: async (page = 1) => {
    const res = await api.get('/nollywood', { params: { page } });
    return res.data;
  },
  getGame: async (page = 1) => {
    const res = await api.get('/game', { params: { page } });
    return res.data;
  },
  getSearchSuggestions: async (q?: string) => {
    const res = await api.get('/search-suggestions', { params: { q } });
    return res.data;
  },
  getPostCount: async (id: string) => {
    const res = await api.get(`/post/count/${id}`);
    return res.data;
  },
  getTrendingGroups: async () => {
    const res = await api.get('/groups/trending');
    return res.data;
  },
  getGroupPosts: async () => {
    const res = await api.get('/groups/interactive');
    return res.data;
  },
  getSubjectPosts: async (subjectId: string, page = 1) => {
    const res = await api.get(`/post/list/${subjectId}`, { params: { page } });
    return res.data;
  },
  createPost: async (subjectId: string, content: string) => {
    const res = await api.post('/post/create', null, { params: { subject_id: subjectId, content } });
    return res.data;
  },
  getSubtitles: async (id: string, season = 1, episode = 1) => {
    const res = await api.get(`/subtitles/${id}`, { params: { se: season, ep: episode } });
    return res.data;
  },
  
  // --- NEW: Cloud Sync & Advanced Subtitles ---
  getHistoryPosition: async (subjectId: string, resourceId: string) => {
    const res = await api.get(`/history/position`, { params: { subject_id: subjectId, resource_id: resourceId } });
    return res.data;
  },
  
  saveHistoryPosition: async (subjectId: string, resourceId: string, position: number) => {
    const res = await api.post(`/history/position`, null, { params: { subject_id: subjectId, resource_id: resourceId, position } });
    return res.data;
  },
  
  markHaveSeen: async (subjectId: string, progress: number = 0, total: number = 0) => {
    const res = await api.post(`/history/seen`, null, { 
      params: { 
        subject_id: subjectId,
        progress: progress,
        total: total
      } 
    });
    return res.data;
  },
  
  launchPlayer: async (player: string, url: string, opts: any = {}) => {
    const res = await api.post('/launch-player', null, { 
      params: { player, url, ...opts } 
    });
    return res.data;
  }
};

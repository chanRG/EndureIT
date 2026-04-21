/**
 * API client for EndureIT backend
 */
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost/api/v1';

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },
  
  register: async (data: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
  }) => {
    const response = await apiClient.post('/auth/register', data);
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await apiClient.get('/users/me');
    return response.data;
  },
};

// Workouts API
export const workoutsAPI = {
  getAll: async (skip = 0, limit = 100) => {
    const response = await apiClient.get('/workouts/', {
      params: { skip, limit },
    });
    return response.data;
  },
  
  getById: async (id: number) => {
    const response = await apiClient.get(`/workouts/${id}`);
    return response.data;
  },
  
  create: async (data: any) => {
    const response = await apiClient.post('/workouts/', data);
    return response.data;
  },
  
  update: async (id: number, data: any) => {
    const response = await apiClient.put(`/workouts/${id}`, data);
    return response.data;
  },
  
  delete: async (id: number) => {
    const response = await apiClient.delete(`/workouts/${id}`);
    return response.data;
  },
};

// Goals API
export const goalsAPI = {
  getAll: async () => {
    const response = await apiClient.get('/goals/');
    return response.data;
  },
  
  getById: async (id: number) => {
    const response = await apiClient.get(`/goals/${id}`);
    return response.data;
  },
  
  create: async (data: any) => {
    const response = await apiClient.post('/goals/', data);
    return response.data;
  },
  
  update: async (id: number, data: any) => {
    const response = await apiClient.put(`/goals/${id}`, data);
    return response.data;
  },
  
  delete: async (id: number) => {
    const response = await apiClient.delete(`/goals/${id}`);
    return response.data;
  },
};

// Progress API
export const progressAPI = {
  getAll: async () => {
    const response = await apiClient.get('/progress/');
    return response.data;
  },
  
  create: async (data: any) => {
    const response = await apiClient.post('/progress/', data);
    return response.data;
  },
};

// Dashboard API
export const dashboardAPI = {
  getStats: async () => {
    const response = await apiClient.get('/dashboard/stats');
    return response.data;
  },
  
  getRecentWorkouts: async (limit = 5) => {
    const response = await apiClient.get('/dashboard/recent-workouts', {
      params: { limit },
    });
    return response.data;
  },
  
  getWeeklyActivity: async () => {
    const response = await apiClient.get('/dashboard/weekly-activity');
    return response.data;
  },
};

// Strava API
export const stravaAPI = {
  getActivities: async (page = 1, perPage = 30) => {
    const response = await apiClient.get('/strava/activities', {
      params: { page, per_page: perPage },
    });
    return response.data;
  },
  
  getActivity: async (id: number) => {
    const response = await apiClient.get(`/strava/activity/${id}`);
    return response.data;
  },
  
  getAthlete: async () => {
    const response = await apiClient.get('/strava/athlete');
    return response.data;
  },
  
  getStats: async () => {
    const response = await apiClient.get('/strava/stats');
    return response.data;
  },
  
  getBestEfforts: async () => {
    const response = await apiClient.get('/strava/best-efforts');
    return response.data;
  },
  
  getPRHistory: async (distanceName: string) => {
    const response = await apiClient.get(`/strava/pr-history/${encodeURIComponent(distanceName)}`);
    return response.data;
  },
  
  getHeartRateZones: async (maxHr?: number | null) => {
    const response = await apiClient.get('/strava/hr-zones', {
      params: {
        max_hr_override: maxHr ?? undefined,
      },
    });
    return response.data;
  },
};

// Training Plans API
export const trainingAPI = {
  createPlan: async (data: {
    goal_distance_km: number;
    race_date: string;
    days_per_week: number;
    level: string;
    race_name?: string;
    start_date?: string;
  }) => {
    const response = await apiClient.post('/training-plans', data);
    return response.data;
  },

  getActivePlan: async () => {
    const response = await apiClient.get('/training-plans/active');
    return response.data;
  },

  getPlan: async (id: number) => {
    const response = await apiClient.get(`/training-plans/${id}`);
    return response.data;
  },

  updatePlan: async (id: number, data: { status: string }) => {
    const response = await apiClient.patch(`/training-plans/${id}`, data);
    return response.data;
  },

  getPlanOptions: async (distanceKm: number, level: string) => {
    const response = await apiClient.get(`/training-plans/options/${distanceKm}`, {
      params: { level },
    });
    return response.data;
  },

  getTodayWorkouts: async () => {
    const response = await apiClient.get('/planned-workouts/today');
    return response.data;
  },

  getWeekWorkouts: async (start: string) => {
    const response = await apiClient.get('/planned-workouts/week', { params: { start } });
    return response.data;
  },

  getWorkout: async (id: number) => {
    const response = await apiClient.get(`/planned-workouts/${id}`);
    return response.data;
  },

  updateWorkout: async (id: number, data: { perceived_effort?: number; user_notes?: string; status?: string }) => {
    const response = await apiClient.patch(`/planned-workouts/${id}`, data);
    return response.data;
  },

  matchWorkout: async (workoutId: number, stravaId: number) => {
    const response = await apiClient.post(`/planned-workouts/${workoutId}/match/${stravaId}`);
    return response.data;
  },
};


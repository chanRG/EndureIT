'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Activity, Target, TrendingUp, LogOut, Calendar, MapPin, Clock, Zap, Trophy, Award, Timer, CalendarDays, ArrowUpRight } from 'lucide-react';
import { stravaAPI } from '@/lib/api';
import PRDetailModal from '@/components/PRDetailModal';
import ActivityDetailModal from '@/components/ActivityDetailModal';
import HeartRateZonesCard from '@/components/HeartRateZonesCard';

interface StravaActivity {
  id: number;
  name: string;
  type: string;
  distance: number;
  moving_time: number;
  elapsed_time: number;
  total_elevation_gain: number;
  start_date: string;
  start_date_local: string;
  average_speed?: number;
  max_speed?: number;
  average_heartrate?: number;
  max_heartrate?: number;
  calories?: number;
  achievement_count?: number;
}

interface BestEffort {
  name: string;
  distance: number;
  elapsed_time: number;
  moving_time: number;
  start_date: string;
  start_date_local: string;
  activity_id: number;
  activity_name: string;
  pr_rank?: number;
}

interface BestEffortsResponse {
  total_activities: number;
  running_activities: number;
  best_efforts: BestEffort[];
}

export default function DashboardPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const [activities, setActivities] = useState<StravaActivity[]>([]);
  const [bestEffortsData, setBestEffortsData] = useState<BestEffortsResponse | null>(null);
  const [loadingActivities, setLoadingActivities] = useState(true);
  const [loadingBestEfforts, setLoadingBestEfforts] = useState(true);
  const [loadingMoreActivities, setLoadingMoreActivities] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMoreActivities, setHasMoreActivities] = useState(true);
  
  // Modal state
  const [selectedPR, setSelectedPR] = useState<string | null>(null);
  const [prHistory, setPRHistory] = useState<any[]>([]);
  const [loadingPRHistory, setLoadingPRHistory] = useState(false);
  
  // Activity detail modal state
  const [selectedActivity, setSelectedActivity] = useState<any | null>(null);
  const [loadingActivityDetail, setLoadingActivityDetail] = useState(false);
  const [hrZoneAnalysis, setHrZoneAnalysis] = useState<any | null>(null);
  const [loadingHrZones, setLoadingHrZones] = useState(true);
  const [hrZoneError, setHrZoneError] = useState('');
  const [hrMaxOverride, setHrMaxOverride] = useState<number | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      fetchRecentActivities();
      fetchBestEfforts();
      fetchHeartRateZones();
    }
  }, [user]);

  const fetchRecentActivities = async (page: number = 1, append: boolean = false) => {
    try {
      if (append) {
        setLoadingMoreActivities(true);
      } else {
        setLoadingActivities(true);
        setActivities([]);
        setCurrentPage(1);
      }
      setError('');
      
      const perPage = 20;
      const data = await stravaAPI.getActivities(page, perPage);
      
      if (append) {
        setActivities(prev => [...prev, ...data]);
      } else {
        setActivities(data);
      }
      
      // If we got less than perPage, there are no more activities
      setHasMoreActivities(data.length === perPage);
      setCurrentPage(page);
    } catch (err: any) {
      console.error('Error fetching Strava activities:', err);
      setError(err.response?.data?.detail || 'Failed to load Strava activities');
    } finally {
      setLoadingActivities(false);
      setLoadingMoreActivities(false);
    }
  };
  
  const loadMoreActivities = () => {
    fetchRecentActivities(currentPage + 1, true);
  };

  const fetchBestEfforts = async () => {
    try {
      setLoadingBestEfforts(true);
      setError('');
      setProgress('Loading all activities and calculating personal bests...');
      const data = await stravaAPI.getBestEfforts();
      setBestEffortsData(data);
      setProgress('');
    } catch (err: any) {
      console.error('Error fetching best efforts:', err);
      const errorMsg = err.response?.data?.detail || 'Failed to load personal bests';
      setError(errorMsg);
      setProgress('');
      
      // If rate limit, show helpful message
      if (errorMsg.includes('rate limit') || errorMsg.includes('Rate limit')) {
        setError('⚠️ Strava API rate limit exceeded. Please wait 15 minutes before trying again. Strava limits: 100 requests per 15 minutes.');
      }
    } finally {
      setLoadingBestEfforts(false);
    }
  };

  const fetchHeartRateZones = async (override?: number | null) => {
    try {
      setLoadingHrZones(true);
      setHrZoneError('');
      const overrideProvided = override !== undefined;
      const overrideToUse = overrideProvided ? override : hrMaxOverride;
      const data = await stravaAPI.getHeartRateZones(overrideToUse ?? undefined);
      setHrZoneAnalysis(data);
      if (overrideProvided) {
        setHrMaxOverride(override ?? null);
      } else if (typeof data.hr_max_override === 'number') {
        setHrMaxOverride(data.hr_max_override);
      }
    } catch (err: any) {
      console.error('Error fetching heart rate zones:', err);
      setHrZoneError(err.response?.data?.detail || 'Failed to load heart rate zone analysis');
    } finally {
      setLoadingHrZones(false);
    }
  };

  const handlePRClick = async (distanceName: string) => {
    setSelectedPR(distanceName);
    setLoadingPRHistory(true);
    setPRHistory([]);
    
    try {
      const data = await stravaAPI.getPRHistory(distanceName);
      setPRHistory(data.pr_history || []);
    } catch (err: any) {
      console.error('Error fetching PR history:', err);
      // Keep modal open but show empty state
    } finally {
      setLoadingPRHistory(false);
    }
  };

  const handleCloseModal = () => {
    setSelectedPR(null);
    setPRHistory([]);
  };

  const handleActivityClick = async (activityId: number) => {
    setSelectedActivity(null);
    setLoadingActivityDetail(true);
    
    try {
      const data = await stravaAPI.getActivity(activityId);
      setSelectedActivity(data);
    } catch (err: any) {
      console.error('Error fetching activity detail:', err);
      setSelectedActivity({ error: 'Failed to load activity details' });
    } finally {
      setLoadingActivityDetail(false);
    }
  };

  const handleHrMaxChange = (value: number | null) => {
    fetchHeartRateZones(value);
  };

  const handleCloseActivityModal = () => {
    setSelectedActivity(null);
  };

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const formatDistance = (meters: number) => {
    return (meters / 1000).toFixed(2) + ' km';
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const formatPace = (meters: number, seconds: number) => {
    const km = meters / 1000;
    const secondsPerKm = seconds / km;
    const minutes = Math.floor(secondsPerKm / 60);
    const secs = Math.floor(secondsPerKm % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')} /km`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getActivityIcon = (type: string) => {
    const iconClass = "w-5 h-5";
    switch (type.toLowerCase()) {
      case 'run':
        return <Activity className={iconClass + " text-orange-500"} />;
      case 'ride':
        return <Zap className={iconClass + " text-blue-500"} />;
      case 'swim':
        return <Activity className={iconClass + " text-cyan-400"} />;
      default:
        return <Activity className={iconClass + " text-slate-500"} />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="text-center text-slate-400">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto"></div>
          <p className="mt-4">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const totalActivities = bestEffortsData?.total_activities || 0;
  const runningActivities = bestEffortsData?.running_activities || 0;
  const bestEffortsList = bestEffortsData?.best_efforts || [];
  const longestEffort = bestEffortsList.reduce<BestEffort | null>(
    (prev, curr) => (!prev || curr.distance > prev.distance ? curr : prev),
    null
  );
  const fastestEffort = bestEffortsList.reduce<BestEffort | null>(
    (prev, curr) => {
      const prevPace = prev ? prev.moving_time / prev.distance : Infinity;
      const currPace = curr.moving_time / curr.distance;
      return curr.distance > 0 && currPace < prevPace ? curr : prev;
    },
    null
  );
  const latestEffort = bestEffortsList.reduce<BestEffort | null>(
    (prev, curr) => (!prev || new Date(curr.start_date) > new Date(prev.start_date) ? curr : prev),
    null
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Navigation */}
      <nav className="bg-slate-900/50 backdrop-blur-md border-b border-slate-800 shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold gradient-text">
              Endure<span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">IT</span>
            </h1>
            <div className="flex items-center gap-4">
              <span className="text-slate-300">Welcome, <span className="text-blue-400 font-semibold">{user.username}</span>!</span>
              <a
                href="/training"
                className="flex items-center gap-2 px-4 py-2 text-slate-300 hover:text-orange-400 transition-all hover:bg-slate-800 rounded-lg text-sm"
              >
                Training
              </a>
              <a
                href="/nutrition"
                className="flex items-center gap-2 px-4 py-2 text-slate-300 hover:text-green-400 transition-all hover:bg-slate-800 rounded-lg text-sm"
              >
                Nutrition
              </a>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 text-slate-300 hover:text-red-400 transition-all hover:bg-slate-800 rounded-lg"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-4xl font-bold text-slate-100 mb-2">Dashboard</h2>
          <p className="text-slate-400 text-lg">Your Strava personal records and training history</p>
        </div>

        {progress && (
          <div className="glass rounded-xl p-4 mb-6 border border-blue-500/30">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
              <p className="text-blue-300 font-medium">{progress}</p>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <StatCard
            icon={<Activity className="w-8 h-8 text-blue-400" />}
            title="Total Activities"
            value={loadingBestEfforts ? "..." : totalActivities.toString()}
            subtitle="All time"
          />
          <StatCard
            icon={<Activity className="w-8 h-8 text-orange-500" />}
            title="Running Activities"
            value={loadingBestEfforts ? "..." : runningActivities.toString()}
            subtitle="Total runs"
          />
          <StatCard
            icon={<Trophy className="w-8 h-8 text-yellow-400" />}
            title="Personal Records"
            value={loadingBestEfforts ? "..." : (bestEffortsData?.best_efforts.length || 0).toString()}
            subtitle="Best efforts tracked"
          />
        </div>

        {/* Personal Bests from Strava */}
        {loadingBestEfforts ? (
          <div className="glass rounded-2xl p-8 mb-8 border border-blue-500/30 bg-slate-900/70">
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto"></div>
              <p className="mt-4 text-slate-400">Loading personal bests...</p>
            </div>
          </div>
        ) : bestEffortsList.length > 0 ? (
          <div className="glass rounded-2xl shadow-2xl p-8 mb-8 border border-yellow-500/30 bg-gradient-to-br from-yellow-900/20 via-orange-900/10 to-slate-900/50">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <Trophy className="w-8 h-8 text-yellow-400 animate-pulse" />
                <div>
                  <h3 className="text-2xl font-bold text-slate-100">Personal Records</h3>
                  <p className="text-sm text-slate-400">Best efforts from Strava (official PRs)</p>
                </div>
              </div>
              <button
                onClick={fetchBestEfforts}
                disabled={loadingBestEfforts}
                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-500 text-white rounded-lg transition-all disabled:bg-yellow-900/50 disabled:text-slate-500 shadow-lg hover:shadow-yellow-500/50"
              >
                Refresh
              </button>
            </div>
            
            {(fastestEffort || longestEffort || latestEffort) && (
              <div className="grid md:grid-cols-3 gap-4 mb-6 text-slate-100">
                {fastestEffort && (
                  <div className="rounded-2xl border border-blue-500/40 bg-blue-900/10 p-4 backdrop-blur-md shadow-lg">
                    <p className="text-xs uppercase tracking-wide text-blue-300 flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      Fastest Pace
                    </p>
                    <p className="text-xl font-semibold mt-2">{fastestEffort.name}</p>
                    <p className="text-sm text-slate-400 mt-1">{formatPace(fastestEffort.distance, fastestEffort.moving_time)} / km</p>
                  </div>
                )}
                {longestEffort && (
                  <div className="rounded-2xl border border-purple-500/40 bg-purple-900/10 p-4 backdrop-blur-md shadow-lg">
                    <p className="text-xs uppercase tracking-wide text-purple-300 flex items-center gap-2">
                      <Activity className="w-4 h-4" />
                      Longest Distance
                    </p>
                    <p className="text-xl font-semibold mt-2">{longestEffort.name}</p>
                    <p className="text-sm text-slate-400 mt-1">{formatDistance(longestEffort.distance)}</p>
                  </div>
                )}
                {latestEffort && (
                  <div className="rounded-2xl border border-emerald-500/40 bg-emerald-900/10 p-4 backdrop-blur-md shadow-lg">
                    <p className="text-xs uppercase tracking-wide text-emerald-300 flex items-center gap-2">
                      <CalendarDays className="w-4 h-4" />
                      Most Recent PR
                    </p>
                    <p className="text-xl font-semibold mt-2">{latestEffort.name}</p>
                    <p className="text-sm text-slate-400 mt-1">{formatDate(latestEffort.start_date_local)}</p>
                  </div>
                )}
              </div>
            )}
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {bestEffortsList
                .sort((a, b) => a.distance - b.distance)
                .map((pr) => (
                <button
                  key={pr.name}
                  onClick={() => handlePRClick(pr.name)}
                  className="glass rounded-xl p-5 shadow-lg hover:shadow-2xl hover:shadow-yellow-500/20 transition-all border border-slate-700 hover:border-yellow-500/50 text-left hover:scale-105 cursor-pointer transform duration-300 group"
                >
                  <div className="flex items-center gap-2 mb-3">
                    <Award className="w-5 h-5 text-yellow-400 group-hover:scale-110 transition-transform" />
                    <h4 className="text-lg font-bold text-slate-100">{pr.name}</h4>
                    {pr.pr_rank === 1 && (
                      <span className="ml-auto bg-yellow-500/20 text-yellow-400 text-xs font-bold px-2 py-1 rounded border border-yellow-500/30">
                        #1 PR
                      </span>
                    )}
                  </div>
                  
                  <div className="mt-4 grid grid-cols-2 gap-3">
                    <div className="rounded-lg bg-slate-900/60 border border-slate-800/70 px-3 py-2">
                      <p className="text-[0.65rem] uppercase tracking-wider text-slate-500 flex items-center gap-1">
                        <Timer className="w-3 h-3" />
                        Time
                      </p>
                      <p className="text-xl font-bold text-blue-300 mt-1">
                        {formatDuration(pr.elapsed_time)}
                      </p>
                    </div>
                    <div className="rounded-lg bg-slate-900/60 border border-slate-800/70 px-3 py-2">
                      <p className="text-[0.65rem] uppercase tracking-wider text-slate-500 flex items-center gap-1">
                        <Zap className="w-3 h-3" />
                        Pace
                      </p>
                      <p className="text-lg font-semibold text-emerald-200 mt-1">
                        {formatPace(pr.distance, pr.moving_time)}
                      </p>
                    </div>
                    <div className="rounded-lg bg-slate-900/60 border border-slate-800/70 px-3 py-2">
                      <p className="text-[0.65rem] uppercase tracking-wider text-slate-500 flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        Distance
                      </p>
                      <p className="text-base font-semibold text-slate-200 mt-1">
                        {formatDistance(pr.distance)}
                      </p>
                    </div>
                    <div className="rounded-lg bg-slate-900/60 border border-slate-800/70 px-3 py-2">
                      <p className="text-[0.65rem] uppercase tracking-wider text-slate-500 flex items-center gap-1">
                        <CalendarDays className="w-3 h-3" />
                        Date
                      </p>
                      <p className="text-sm font-medium text-slate-300 mt-1">
                        {formatDate(pr.start_date_local)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="mt-4 rounded-lg border border-slate-800/70 bg-slate-900/60 px-3 py-2">
                    <p className="text-[0.65rem] uppercase tracking-wider text-slate-500">Activity</p>
                    <p className="text-xs text-slate-400 truncate mt-1" title={pr.activity_name}>
                      {pr.activity_name}
                    </p>
                  </div>
                  
                  <div className="mt-4 text-xs text-blue-400 font-medium flex items-center justify-center gap-2 pt-3 border-t border-slate-800/80 group-hover:text-yellow-400 transition-colors">
                    <ArrowUpRight className="w-3 h-3" />
                    View progression history
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : null}

        <HeartRateZonesCard
          analysis={hrZoneAnalysis}
          loading={loadingHrZones}
          error={hrZoneError}
          onRefresh={() => fetchHeartRateZones()}
          onMaxHrChange={handleHrMaxChange}
          maxHrOverride={hrMaxOverride}
        />

        {/* Recent Activities */}
        <div className="glass rounded-2xl shadow-2xl p-8 mb-8 border border-slate-700/50">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-2xl font-bold text-slate-100">Recent Activities</h3>
              <p className="text-sm text-slate-400 mt-1">
                {activities.length > 0 ? `Showing ${activities.length} activities` : 'No activities loaded'}
              </p>
            </div>
            <button
              onClick={() => fetchRecentActivities(1, false)}
              disabled={loadingActivities}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-all disabled:bg-slate-700 disabled:text-slate-500 shadow-lg hover:shadow-blue-500/50"
            >
              {loadingActivities ? 'Loading...' : 'Refresh'}
            </button>
          </div>

          {loadingActivities ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto"></div>
              <p className="mt-4 text-slate-400">Loading activities...</p>
            </div>
          ) : error ? (
            <div className="glass border border-rose-500/40 bg-rose-900/20 rounded-xl p-4 text-rose-200">
              {error}
            </div>
          ) : activities.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <Activity className="w-16 h-16 mx-auto mb-4 text-slate-700" />
              <p>No activities found. Start tracking your workouts on Strava!</p>
            </div>
          ) : (
            <>
              <div className="space-y-4">
                {activities.map((activity) => (
                  <button
                    key={activity.id}
                    onClick={() => handleActivityClick(activity.id)}
                    className="relative overflow-hidden w-full rounded-2xl border border-slate-800/70 bg-slate-900/60 p-5 hover:shadow-2xl hover:shadow-blue-500/20 hover:border-blue-500/50 transition-all text-left cursor-pointer group"
                  >
                    <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-r from-blue-500/5 via-indigo-500/10 to-purple-500/10" />
                    <div className="relative z-10">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3 flex-1">
                          <div className="mt-1">
                            {getActivityIcon(activity.type)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <h4 className="text-lg font-semibold text-slate-100">
                                {activity.name}
                              </h4>
                              {activity.achievement_count && activity.achievement_count > 0 && (
                                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-[0.65rem] font-semibold text-amber-200 bg-amber-500/20 border border-amber-500/30">
                                  <Trophy className="w-3 h-3" />
                                  {activity.achievement_count}
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-slate-500 mt-1 uppercase tracking-wide">
                              {formatDate(activity.start_date_local)}
                            </p>

                            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm text-slate-300">
                              <div className="rounded-xl border border-slate-800/70 bg-slate-900/60 px-3 py-2">
                                <p className="text-[0.65rem] text-slate-400 uppercase tracking-wider">Distance</p>
                                <p className="text-base font-semibold text-slate-100 mt-1">
                                  {formatDistance(activity.distance)}
                                </p>
                              </div>
                              <div className="rounded-xl border border-slate-800/70 bg-slate-900/60 px-3 py-2">
                                <p className="text-[0.65rem] text-slate-400 uppercase tracking-wider">Duration</p>
                                <p className="text-base font-semibold text-slate-100 mt-1">
                                  {formatDuration(activity.moving_time)}
                                </p>
                              </div>
                              {activity.total_elevation_gain > 0 && (
                                <div className="rounded-xl border border-slate-800/70 bg-slate-900/60 px-3 py-2">
                                  <p className="text-[0.65rem] text-slate-400 uppercase tracking-wider">Elevation</p>
                                  <p className="text-base font-semibold text-slate-100 mt-1">
                                    {activity.total_elevation_gain.toFixed(0)} m
                                  </p>
                                </div>
                              )}
                              {activity.average_heartrate && (
                                <div className="rounded-xl border border-slate-800/70 bg-slate-900/60 px-3 py-2">
                                  <p className="text-[0.65rem] text-slate-400 uppercase tracking-wider">Avg HR</p>
                                  <p className="text-base font-semibold text-rose-200 mt-1">
                                    {activity.average_heartrate.toFixed(0)} bpm
                                  </p>
                                </div>
                              )}
                            </div>

                            <div className="mt-4 flex flex-wrap gap-2 text-[0.65rem] uppercase tracking-wider text-slate-400">
                              <span className="px-2 py-1 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-200">
                                {activity.type}
                              </span>
                              {activity.has_heartrate && (
                                <span className="px-2 py-1 rounded-full border border-rose-500/30 bg-rose-500/10 text-rose-200">
                                  Heart Rate
                                </span>
                              )}
                              {activity.kudos_count > 0 && (
                                <span className="px-2 py-1 rounded-full border border-purple-500/30 bg-purple-500/10 text-purple-200">
                                  {activity.kudos_count} Kudos
                                </span>
                              )}
                            </div>

                            <div className="mt-4 text-xs text-blue-400 font-medium group-hover:text-purple-400 transition-colors flex items-center gap-2">
                              View full breakdown
                              <ArrowUpRight className="w-3 h-3" />
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-slate-500 uppercase tracking-wide">Efforts</p>
                          <p className="text-lg font-semibold text-slate-100">
                            {activity.best_efforts?.length || 0}
                          </p>
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
              
              {/* Load More Button */}
              {hasMoreActivities && (
                <div className="mt-6 text-center">
                  <button
                    onClick={loadMoreActivities}
                    disabled={loadingMoreActivities}
                    className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-500 hover:from-blue-500 hover:to-indigo-400 text-white rounded-full transition-all disabled:from-slate-700 disabled:to-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed shadow-lg hover:shadow-blue-500/40"
                  >
                    {loadingMoreActivities ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        Loading more...
                      </>
                    ) : (
                      <>
                        Load More Activities
                        <ArrowUpRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {/* API Info */}
        <div className="glass border border-emerald-500/30 rounded-lg p-4 bg-emerald-900/10">
          <p className="text-emerald-300">
            <strong>🎉 Connected to Strava!</strong> Using official Strava best_efforts data from detailed activities
          </p>
          <p className="text-emerald-400 text-sm mt-2">
            API Reference: <a href="https://developers.strava.com/docs/reference/" target="_blank" rel="noopener noreferrer" className="underline hover:text-emerald-300 transition-colors">Strava API Documentation</a>
          </p>
        </div>
      </div>

      {/* PR Detail Modal */}
      <PRDetailModal
        isOpen={selectedPR !== null}
        onClose={handleCloseModal}
        distanceName={selectedPR || ''}
        prHistory={prHistory}
        loading={loadingPRHistory}
      />

      {/* Activity Detail Modal */}
      <ActivityDetailModal
        isOpen={selectedActivity !== null}
        onClose={handleCloseActivityModal}
        activity={selectedActivity}
        loading={loadingActivityDetail}
      />
    </div>
  );
}

function StatCard({
  icon,
  title,
  value,
  subtitle,
}: {
  icon: React.ReactNode;
  title: string;
  value: string;
  subtitle: string;
}) {
  return (
    <div className="glass rounded-xl shadow-xl p-6 hover:shadow-2xl hover:scale-105 transition-all duration-300 group">
      <div className="flex items-center gap-4 mb-4">
        <div className="group-hover:scale-110 transition-transform duration-300">
        {icon}
        </div>
        <h3 className="text-lg font-semibold text-slate-300">{title}</h3>
      </div>
      <p className="text-4xl font-bold text-slate-100 mb-2">{value}</p>
      <p className="text-sm text-slate-500">{subtitle}</p>
    </div>
  );
}

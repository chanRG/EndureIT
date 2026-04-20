import Link from 'next/link';
import { Activity, TrendingUp, Target, BarChart } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-gray-900 mb-4">
            Endure<span className="text-blue-600">IT</span>
          </h1>
          <p className="text-2xl text-gray-600 mb-8">
            Your Ultimate Fitness Tracking Companion
          </p>
          <p className="text-lg text-gray-500 mb-12 max-w-2xl mx-auto">
            Track your workouts, set goals, monitor progress, and achieve your fitness dreams with EndureIT.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/login"
              className="px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Get Started
            </Link>
            <Link
              href="/register"
              className="px-8 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-gray-50 transition-colors border border-blue-600"
            >
              Sign Up
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
          <FeatureCard
            icon={<Activity className="w-12 h-12 text-blue-600" />}
            title="Track Workouts"
            description="Log all your exercises, sets, reps, and track your performance over time."
          />
          <FeatureCard
            icon={<Target className="w-12 h-12 text-blue-600" />}
            title="Set Goals"
            description="Define your fitness goals and get insights on your progress towards achieving them."
          />
          <FeatureCard
            icon={<TrendingUp className="w-12 h-12 text-blue-600" />}
            title="Monitor Progress"
            description="Track body measurements, weight, and other metrics to see your transformation."
          />
          <FeatureCard
            icon={<BarChart className="w-12 h-12 text-blue-600" />}
            title="View Analytics"
            description="Get detailed insights and analytics about your fitness journey."
          />
        </div>

        {/* About Section */}
        <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Start Your Fitness Journey Today
          </h2>
          <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
            EndureIT helps you stay motivated and accountable by tracking every aspect of your fitness journey.
            Whether you're a beginner or a pro, we've got the tools you need to succeed.
          </p>
          <Link
            href="/login"
            className="inline-block px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            Start Tracking Now
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 mt-16">
        <div className="container mx-auto px-4 text-center">
          <p className="text-gray-400">
            © 2025 EndureIT. Your fitness tracking companion.
          </p>
          <p className="text-gray-500 mt-2">
            <Link href="/docs" className="hover:text-white transition-colors">
              API Documentation
            </Link>
          </p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
      <div className="mb-4">{icon}</div>
      <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

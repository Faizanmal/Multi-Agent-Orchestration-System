/**
 * Modern Dashboard
 * Dashboard with animated metrics
 */

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  Users, 
  Activity, 
  Zap,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import { AnimatedStatCard, FeatureCard, GlassCard } from '@/components/ui/animated-card';
import { staggerContainer, staggerItem } from '@/lib/animations';
import { useCountUp } from '@/hooks/useAnimations';

export function ModernDashboard() {
  const totalUsers = useCountUp(12547, 2000);
  const activeAgents = useCountUp(45, 1500);
  const tasksCompleted = useCountUp(8932, 2500);
  const successRate = useCountUp(98, 1800);

  const stats = [
    {
      title: 'Total Users',
      value: totalUsers.toLocaleString(),
      change: '+12.5%',
      trend: 'up' as const,
      icon: <Users className="w-5 h-5 text-indigo-600" />
    },
    {
      title: 'Active Agents',
      value: activeAgents,
      change: '+8.2%',
      trend: 'up' as const,
      icon: <Activity className="w-5 h-5 text-purple-600" />
    },
    {
      title: 'Tasks Completed',
      value: tasksCompleted.toLocaleString(),
      change: '+23.1%',
      trend: 'up' as const,
      icon: <Zap className="w-5 h-5 text-pink-600" />
    },
    {
      title: 'Success Rate',
      value: `${successRate}%`,
      change: '+2.4%',
      trend: 'up' as const,
      icon: <TrendingUp className="w-5 h-5 text-green-600" />
    }
  ];

  const features = [
    {
      title: 'Real-time Analytics',
      description: 'Monitor agent performance with live metrics and detailed insights into every action.',
      icon: <BarChart3 className="w-6 h-6" />
    },
    {
      title: 'Multi-Agent Coordination',
      description: 'Orchestrate complex workflows with intelligent agent collaboration and task distribution.',
      icon: <Users className="w-6 h-6" />
    },
    {
      title: 'Intelligent Automation',
      description: 'Automate repetitive tasks with AI-powered agents that learn and adapt over time.',
      icon: <Zap className="w-6 h-6" />
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-950 dark:to-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center space-y-4"
        >
          <h1 className="text-4xl md:text-5xl font-bold text-gradient">
            Performance Dashboard
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Real-time insights into your multi-agent system performance
          </p>
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {stats.map((stat, index) => (
            <AnimatedStatCard
              key={index}
              title={stat.title}
              value={stat.value}
              change={stat.change}
              trend={stat.trend}
              icon={stat.icon}
            />
          ))}
        </motion.div>

        {/* Charts Section */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-6"
        >
          <motion.div variants={staggerItem}>
            <GlassCard blur="lg" gradient animated>
              <div className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                    Agent Activity
                  </h3>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                  >
                    <Activity className="w-5 h-5 text-indigo-600" />
                  </motion.div>
                </div>

                {/* Mini Chart Representation */}
                <div className="space-y-3">
                  {[
                    { label: 'Vision Agent', value: 85, color: 'bg-indigo-600' },
                    { label: 'Reasoning Agent', value: 92, color: 'bg-purple-600' },
                    { label: 'Action Agent', value: 78, color: 'bg-pink-600' },
                    { label: 'Memory Agent', value: 95, color: 'bg-green-600' }
                  ].map((item, index) => (
                    <div key={index} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-700 dark:text-gray-300">{item.label}</span>
                        <span className="font-semibold text-gray-900 dark:text-white">{item.value}%</span>
                      </div>
                      <div className="h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
                        <motion.div
                          className={cn('h-full', item.color)}
                          initial={{ width: 0 }}
                          whileInView={{ width: `${item.value}%` }}
                          viewport={{ once: true }}
                          transition={{ duration: 1, delay: index * 0.1 }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </GlassCard>
          </motion.div>

          <motion.div variants={staggerItem}>
            <GlassCard blur="lg" gradient animated>
              <div className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                    Recent Activity
                  </h3>
                  <span className="px-3 py-1 text-xs font-semibold bg-green-500/10 text-green-600 rounded-full">
                    Live
                  </span>
                </div>

                <div className="space-y-3">
                  {[
                    { action: 'Task completed', agent: 'Vision Agent', time: '2m ago', status: 'success' },
                    { action: 'Processing request', agent: 'Reasoning Agent', time: '5m ago', status: 'processing' },
                    { action: 'Workflow executed', agent: 'Action Agent', time: '8m ago', status: 'success' },
                    { action: 'Data stored', agent: 'Memory Agent', time: '12m ago', status: 'success' }
                  ].map((activity, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-center gap-3 p-3 rounded-lg bg-white/50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700"
                    >
                      <div className={cn(
                        'w-2 h-2 rounded-full',
                        activity.status === 'success' ? 'bg-green-500 animate-pulse' : 'bg-yellow-500 animate-pulse'
                      )} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {activity.action}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {activity.agent}
                        </p>
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {activity.time}
                      </span>
                    </motion.div>
                  ))}
                </div>
              </div>
            </GlassCard>
          </motion.div>
        </motion.div>

        {/* Features Section */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          {features.map((feature, index) => (
            <FeatureCard
              key={index}
              title={feature.title}
              description={feature.description}
              icon={feature.icon}
            />
          ))}
        </motion.div>

        {/* Performance Metrics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <GlassCard blur="xl" gradient>
            <div className="p-8 space-y-6">
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                System Performance
              </h3>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {[
                  { label: 'Core focus', value: 'Agents', trend: 'up', change: 'MVP' },
                  { label: 'Status', value: 'Beta', trend: 'up', change: 'Live' },
                  { label: 'Inference', value: 'Groq', trend: 'up', change: 'Fast' },
                  { label: 'Free tier', value: '100', trend: 'up', change: 'msgs/mo' }
                ].map((metric, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, scale: 0.9 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: index * 0.1 }}
                    className="text-center space-y-2"
                  >
                    <p className="text-sm text-gray-600 dark:text-gray-400">{metric.label}</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white">{metric.value}</p>
                    <div className={cn(
                      'flex items-center justify-center gap-1 text-sm font-medium',
                      metric.trend === 'up' ? 'text-green-600' : 'text-red-600'
                    )}>
                      {metric.trend === 'up' ? (
                        <ArrowUpRight className="w-4 h-4" />
                      ) : (
                        <ArrowDownRight className="w-4 h-4" />
                      )}
                      <span>{metric.change}</span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}

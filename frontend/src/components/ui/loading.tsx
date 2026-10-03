/**
 * Modern Loading Components
 * Loading indicators and skeleton screens
 */

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

// ============================================
// SPINNER LOADER
// ============================================
interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  return (
    <motion.div
      className={cn(sizes[size], className)}
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
    >
      <Loader2 className="w-full h-full text-indigo-600" />
    </motion.div>
  );
}

// ============================================
// PULSE LOADER
// ============================================
export function PulseLoader({ className }: { className?: string }) {
  return (
    <div className={cn('flex gap-2', className)}>
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-3 h-3 rounded-full bg-indigo-600"
          animate={{
            scale: [1, 1.5, 1],
            opacity: [1, 0.5, 1],
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            delay: i * 0.2,
          }}
        />
      ))}
    </div>
  );
}

// ============================================
// GRADIENT SPINNER
// ============================================
export function GradientSpinner({ size = 'md', className }: SpinnerProps) {
  const sizes = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
    xl: 'w-24 h-24'
  };

  return (
    <motion.div
      className={cn(
        sizes[size],
        'rounded-full border-4 border-transparent',
        'bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-border',
        className
      )}
      style={{
        borderTopColor: 'transparent',
        borderRightColor: 'currentColor',
        borderBottomColor: 'currentColor',
        borderLeftColor: 'transparent',
      }}
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
    />
  );
}

// ============================================
// SKELETON LOADER
// ============================================
interface SkeletonProps {
  className?: string;
  animated?: boolean;
}

export function Skeleton({ className, animated = true }: SkeletonProps) {
  return (
    <div
      className={cn(
        'rounded-lg bg-gray-200 dark:bg-gray-800',
        animated && 'animate-pulse',
        className
      )}
    />
  );
}

// ============================================
// CARD SKELETON
// ============================================
export function CardSkeleton() {
  return (
    <div className="rounded-2xl border border-gray-200 dark:border-gray-800 p-6 space-y-4">
      <div className="flex items-center gap-4">
        <Skeleton className="w-12 h-12 rounded-full" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      <Skeleton className="h-24 w-full" />
      <div className="flex gap-2">
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-8 w-20" />
      </div>
    </div>
  );
}

// ============================================
// TABLE SKELETON
// ============================================
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 items-center">
          <Skeleton className="h-10 flex-1" />
          <Skeleton className="h-10 flex-1" />
          <Skeleton className="h-10 flex-1" />
          <Skeleton className="h-10 w-20" />
        </div>
      ))}
    </div>
  );
}

// ============================================
// CHAT SKELETON
// ============================================
export function ChatSkeleton() {
  return (
    <div className="space-y-4 p-4">
      {[0, 1, 2].map((i) => (
        <div key={i} className={cn('flex gap-3', i % 2 === 0 ? 'justify-start' : 'justify-end')}>
          {i % 2 === 0 && <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />}
          <div className={cn('space-y-2', i % 2 === 0 ? 'max-w-[70%]' : 'max-w-[70%]')}>
            <Skeleton className="h-20 w-full rounded-2xl" />
          </div>
          {i % 2 !== 0 && <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />}
        </div>
      ))}
    </div>
  );
}

// ============================================
// DASHBOARD SKELETON
// ============================================
export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 space-y-3">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-3 w-20" />
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 space-y-4">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-64 w-full" />
        </div>
        <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 space-y-4">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    </div>
  );
}

// ============================================
// LOADING OVERLAY
// ============================================
interface LoadingOverlayProps {
  message?: string;
  className?: string;
}

export function LoadingOverlay({ message, className }: LoadingOverlayProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className={cn(
        'fixed inset-0 z-50 flex items-center justify-center',
        'bg-white/80 dark:bg-black/80 backdrop-blur-sm',
        className
      )}
    >
      <div className="text-center space-y-4">
        <GradientSpinner size="lg" />
        {message && (
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-gray-700 dark:text-gray-300 font-medium"
          >
            {message}
          </motion.p>
        )}
      </div>
    </motion.div>
  );
}

// ============================================
// PAGE LOADER
// ============================================
export function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-gray-900 dark:to-gray-800">
      <div className="text-center space-y-6">
        <motion.div
          className="relative"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          {/* Outer ring */}
          <motion.div
            className="w-24 h-24 rounded-full border-4 border-indigo-200 dark:border-indigo-900"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          />
          
          {/* Inner ring */}
          <motion.div
            className="absolute inset-0 w-24 h-24 rounded-full border-4 border-transparent border-t-indigo-600"
            animate={{ rotate: -360 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          />

          {/* Center dot */}
          <motion.div
            className="absolute inset-0 flex items-center justify-center"
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 1, repeat: Infinity }}
          >
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600" />
          </motion.div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="space-y-2"
        >
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Loading
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Please wait while we prepare your experience
          </p>
        </motion.div>

        <PulseLoader />
      </div>
    </div>
  );
}

// ============================================
// PROGRESS BAR
// ============================================
interface ProgressBarProps {
  progress: number;
  className?: string;
  showLabel?: boolean;
}

export function ProgressBar({ progress, className, showLabel = true }: ProgressBarProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {showLabel && (
        <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
          <span>Loading...</span>
          <span>{Math.round(progress)}%</span>
        </div>
      )}
      <div className="h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>
    </div>
  );
}

// ============================================
// CIRCULAR PROGRESS
// ============================================
interface CircularProgressProps {
  progress: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
}

export function CircularProgress({ 
  progress, 
  size = 100, 
  strokeWidth = 8,
  className 
}: CircularProgressProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className={cn('relative', className)} style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-gray-200 dark:text-gray-800"
        />
        {/* Progress circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="url(#gradient)"
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.5 }}
        />
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="100%" stopColor="#a855f7" />
          </linearGradient>
        </defs>
      </svg>
      
      {/* Center text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-bold text-gray-900 dark:text-white">
          {Math.round(progress)}%
        </span>
      </div>
    </div>
  );
}

// ============================================
// BOUNCING DOTS
// ============================================
export function BouncingDots({ className }: { className?: string }) {
  return (
    <div className={cn('flex gap-1', className)}>
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-2 h-2 rounded-full bg-indigo-600"
          animate={{
            y: ['0%', '-50%', '0%'],
          }}
          transition={{
            duration: 0.6,
            repeat: Infinity,
            delay: i * 0.1,
          }}
        />
      ))}
    </div>
  );
}

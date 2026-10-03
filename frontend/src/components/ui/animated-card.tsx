/**
 * Modern Animated Card Components
 * Card designs with stunning animations
 */

'use client';

import React, { ReactNode, useRef } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { cn } from '@/lib/utils';
import { fadeInUp, glassCard, scaleIn } from '@/lib/animations';
import { useTiltEffect } from '@/hooks/useAnimations';

// ============================================
// GLASSMORPHIC CARD
// ============================================
interface GlassCardProps {
  children: ReactNode;
  className?: string;
  blur?: 'sm' | 'md' | 'lg' | 'xl';
  gradient?: boolean;
  animated?: boolean;
}

export function GlassCard({ 
  children, 
  className, 
  blur = 'md',
  gradient = false,
  animated = true 
}: GlassCardProps) {
  const blurValues = {
    sm: 'backdrop-blur-sm',
    md: 'backdrop-blur-md',
    lg: 'backdrop-blur-lg',
    xl: 'backdrop-blur-xl'
  };

  const Component = animated ? motion.div : 'div';
  const animationProps = animated ? {
    variants: glassCard,
    initial: 'hidden',
    whileInView: 'visible',
    viewport: { once: true, amount: 0.3 }
  } : {};

  return (
    <Component
      {...animationProps}
      className={cn(
        'relative overflow-hidden rounded-2xl border border-white/20',
        'bg-white/10 dark:bg-black/20',
        blurValues[blur],
        'shadow-xl shadow-black/10',
        gradient && 'before:absolute before:inset-0 before:bg-gradient-to-br before:from-white/20 before:to-transparent',
        className
      )}
    >
      {children}
    </Component>
  );
}

// ============================================
// 3D TILT CARD
// ============================================
interface TiltCardProps {
  children: ReactNode;
  className?: string;
  maxTilt?: number;
}

export function TiltCard({ children, className, maxTilt = 15 }: TiltCardProps) {
  const ref = useRef<HTMLDivElement | null>(null);
  const tilt = useTiltEffect(ref as React.RefObject<HTMLElement>, maxTilt);

  return (
    <motion.div
      ref={ref}
      className={cn(
        'relative rounded-2xl p-6',
        'bg-gradient-to-br from-indigo-500/10 to-purple-500/10',
        'border border-indigo-500/20',
        'shadow-xl shadow-indigo-500/10',
        'transition-all duration-300',
        className
      )}
      style={{
        rotateX: tilt.x,
        rotateY: tilt.y,
        transformStyle: 'preserve-3d'
      }}
      whileHover={{ scale: 1.02 }}
    >
      {children}
    </motion.div>
  );
}

// ============================================
// GRADIENT BORDER CARD
// ============================================
interface GradientBorderCardProps {
  children: ReactNode;
  className?: string;
  borderWidth?: number;
  gradientFrom?: string;
  gradientTo?: string;
}

export function GradientBorderCard({
  children,
  className,
  borderWidth = 2,
  gradientFrom = 'from-indigo-500',
  gradientTo = 'to-purple-500'
}: GradientBorderCardProps) {
  return (
    <motion.div
      className={cn('relative rounded-2xl', className)}
      style={{ padding: borderWidth }}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      variants={fadeInUp}
    >
      <div className={cn(
        'absolute inset-0 rounded-2xl bg-gradient-to-r',
        gradientFrom,
        gradientTo,
        'opacity-75 blur-sm'
      )} />
      <div className={cn(
        'relative rounded-2xl bg-white dark:bg-gray-900',
        'border border-gray-200 dark:border-gray-800'
      )}>
        {children}
      </div>
    </motion.div>
  );
}

// ============================================
// HOVER GLOW CARD
// ============================================
interface HoverGlowCardProps {
  children: ReactNode;
  className?: string;
  glowColor?: string;
}

export function HoverGlowCard({ 
  children, 
  className,
  glowColor = 'rgba(99, 102, 241, 0.5)' 
}: HoverGlowCardProps) {
  return (
    <motion.div
      className={cn(
        'relative rounded-2xl p-6',
        'bg-white dark:bg-gray-900',
        'border border-gray-200 dark:border-gray-800',
        'transition-all duration-300',
        className
      )}
      whileHover={{
        scale: 1.02,
        boxShadow: `0 20px 40px ${glowColor}`,
        y: -5
      }}
      transition={{ duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
}

// ============================================
// MAGNETIC CARD (Follows cursor)
// ============================================
interface MagneticCardProps {
  children: ReactNode;
  className?: string;
  strength?: number;
}

export function MagneticCard({ children, className, strength = 0.15 }: MagneticCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const springConfig = { damping: 20, stiffness: 300 };
  const rotateX = useSpring(useTransform(y, [-100, 100], [10, -10]), springConfig);
  const rotateY = useSpring(useTransform(x, [-100, 100], [-10, 10]), springConfig);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return;
    
    const rect = ref.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    x.set((e.clientX - centerX) * strength);
    y.set((e.clientY - centerY) * strength);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div
      ref={ref}
      className={cn(
        'relative rounded-2xl p-6',
        'bg-gradient-to-br from-white to-gray-50',
        'dark:from-gray-900 dark:to-gray-800',
        'border border-gray-200 dark:border-gray-700',
        'shadow-lg',
        className
      )}
      style={{
        rotateX,
        rotateY,
        transformStyle: 'preserve-3d'
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {children}
    </motion.div>
  );
}

// ============================================
// ANIMATED STAT CARD
// ============================================
interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

export function AnimatedStatCard({ 
  title, 
  value, 
  change, 
  icon, 
  trend = 'neutral',
  className 
}: StatCardProps) {
  const trendColors = {
    up: 'text-green-500',
    down: 'text-red-500',
    neutral: 'text-gray-500'
  };

  return (
    <motion.div
      className={cn(
        'relative overflow-hidden rounded-2xl p-6',
        'bg-gradient-to-br from-white to-gray-50',
        'dark:from-gray-900 dark:to-gray-800',
        'border border-gray-200 dark:border-gray-700',
        'shadow-lg hover:shadow-xl',
        'transition-shadow duration-300',
        className
      )}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      variants={scaleIn}
      whileHover={{ scale: 1.05, y: -5 }}
    >
      {/* Background gradient */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 rounded-full blur-3xl" />
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          {icon && (
            <motion.div
              className="p-2 rounded-lg bg-indigo-500/10"
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.6 }}
            >
              {icon}
            </motion.div>
          )}
        </div>
        
        <div className="flex items-end justify-between">
          <motion.p 
            className="text-3xl font-bold text-gray-900 dark:text-white"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            {value}
          </motion.p>
          
          {change && (
            <motion.span 
              className={cn('text-sm font-medium', trendColors[trend])}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
            >
              {change}
            </motion.span>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// ============================================
// FEATURE CARD with Icon
// ============================================
interface FeatureCardProps {
  title: string;
  description: string;
  icon: ReactNode;
  className?: string;
}

export function FeatureCard({ title, description, icon, className }: FeatureCardProps) {
  return (
    <motion.div
      className={cn(
        'group relative overflow-hidden rounded-2xl p-8',
        'bg-white dark:bg-gray-900',
        'border border-gray-200 dark:border-gray-800',
        'transition-all duration-500',
        'hover:border-indigo-500/50',
        className
      )}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.3 }}
      variants={fadeInUp}
      whileHover="hover"
    >
      {/* Gradient background on hover */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100"
        transition={{ duration: 0.5 }}
      />

      {/* Icon */}
      <motion.div
        className="mb-4 inline-flex p-3 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500"
        whileHover={{ scale: 1.1, rotate: 5 }}
        transition={{ duration: 0.3 }}
      >
        <div className="text-white">
          {icon}
        </div>
      </motion.div>

      {/* Content */}
      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
        {title}
      </h3>
      <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
        {description}
      </p>

      {/* Hover arrow */}
      <motion.div
        className="mt-4 flex items-center text-indigo-500 font-medium opacity-0 group-hover:opacity-100"
        initial={{ x: -10 }}
        whileHover={{ x: 0 }}
        transition={{ duration: 0.3 }}
      >
        <span>Learn more</span>
        <svg className="ml-2 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </motion.div>
    </motion.div>
  );
}

// ============================================
// PRICING CARD
// ============================================
interface PricingCardProps {
  name: string;
  price: string;
  period?: string;
  features: string[];
  highlighted?: boolean;
  className?: string;
  ctaHref?: string;
  ctaLabel?: string;
}

export function PricingCard({ 
  name, 
  price, 
  period = '/month',
  features, 
  highlighted = false,
  className,
  ctaHref = '/register',
  ctaLabel = 'Get Started',
}: PricingCardProps) {
  return (
    <motion.div
      className={cn(
        'relative overflow-hidden rounded-2xl p-8',
        highlighted
          ? 'bg-gradient-to-br from-indigo-600 to-purple-600 text-white border-2 border-indigo-400'
          : 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800',
        'shadow-xl',
        className
      )}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      variants={scaleIn}
      whileHover={{ scale: 1.05, y: -10 }}
    >
      {highlighted && (
        <div className="absolute top-4 right-4">
          <span className="px-3 py-1 text-xs font-bold bg-white/20 rounded-full backdrop-blur-sm">
            POPULAR
          </span>
        </div>
      )}

      <h3 className="text-2xl font-bold mb-2">{name}</h3>
      <div className="flex items-baseline mb-6">
        <span className="text-5xl font-bold">{price}</span>
        <span className="ml-2 text-lg opacity-75">{period}</span>
      </div>

      <ul className="space-y-3 mb-8">
        {features.map((feature, index) => (
          <motion.li
            key={index}
            className="flex items-center"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <svg className="w-5 h-5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            <span>{feature}</span>
          </motion.li>
        ))}
      </ul>

      <motion.a
        href={ctaHref}
        className={cn(
          'block w-full py-3 px-6 rounded-xl font-semibold transition-all text-center',
          highlighted
            ? 'bg-white text-indigo-600 hover:bg-gray-100'
            : 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-700 hover:to-purple-700'
        )}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {ctaLabel}
      </motion.a>
    </motion.div>
  );
}

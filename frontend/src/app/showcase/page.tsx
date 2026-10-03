/**
 * Component Showcase
 * View all modern components in one place
 */

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  GlassCard, 
  TiltCard, 
  FeatureCard, 
  AnimatedStatCard,
  PricingCard,
  HoverGlowCard
} from '@/components/ui/animated-card';
import {
  GridBackground,
  FloatingParticles,
  AnimatedGradientMesh,
  AuroraBackground,
  GlowOrbs,
  DotPattern
} from '@/components/ui/background-effects';
import {
  Spinner,
  PulseLoader,
  GradientSpinner,
  CardSkeleton,
  ProgressBar,
  CircularProgress
} from '@/components/ui/loading';
import {
  ModernButton,
  MagneticButton,
  ShimmerButton,
  RippleButton,
  IconButton,
  FAB,
  SplitButton,
  GradientButton
} from '@/components/ui/modern-button';
import { Sparkles, Zap, Heart, Star, Plus } from 'lucide-react';

export default function ComponentShowcase() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-950 dark:to-gray-900 py-12 px-4">
      <div className="max-w-7xl mx-auto space-y-24">
        
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-4"
        >
          <h1 className="text-6xl font-bold text-gradient">Component Showcase</h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Explore all modern UI components
          </p>
        </motion.div>

        {/* Card Components */}
        <section className="space-y-8">
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white">Card Components</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <GlassCard blur="lg" gradient>
              <div className="p-6">
                <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">Glass Card</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Beautiful glassmorphism effect with blur and gradient
                </p>
              </div>
            </GlassCard>

            <TiltCard>
              <div className="p-6">
                <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">Tilt Card</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  3D tilt effect on mouse movement
                </p>
              </div>
            </TiltCard>

            <HoverGlowCard>
              <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">Glow Card</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Glowing effect on hover
              </p>
            </HoverGlowCard>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <AnimatedStatCard
              title="Total Users"
              value="12,547"
              change="+12.5%"
              trend="up"
              icon={<Sparkles className="w-5 h-5 text-indigo-600" />}
            />
            <AnimatedStatCard
              title="Revenue"
              value="$45.2K"
              change="+23.1%"
              trend="up"
              icon={<Zap className="w-5 h-5 text-green-600" />}
            />
            <AnimatedStatCard
              title="Satisfaction"
              value="98%"
              change="+2.4%"
              trend="up"
              icon={<Heart className="w-5 h-5 text-pink-600" />}
            />
            <AnimatedStatCard
              title="Rating"
              value="4.9"
              change="+0.3"
              trend="up"
              icon={<Star className="w-5 h-5 text-yellow-600" />}
            />
          </div>
        </section>

        {/* Button Components */}
        <section className="space-y-8">
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white">Button Components</h2>
          
          <div className="flex flex-wrap gap-4">
            <ModernButton variant="primary">Primary Button</ModernButton>
            <ModernButton variant="secondary">Secondary Button</ModernButton>
            <ModernButton variant="outline">Outline Button</ModernButton>
            <ModernButton variant="ghost">Ghost Button</ModernButton>
            <GradientButton>Gradient Button</GradientButton>
            <ModernButton variant="glow">Glow Button</ModernButton>
          </div>

          <div className="flex flex-wrap gap-4">
            <ModernButton size="sm">Small</ModernButton>
            <ModernButton size="md">Medium</ModernButton>
            <ModernButton size="lg">Large</ModernButton>
            <ModernButton size="xl">Extra Large</ModernButton>
          </div>

          <div className="flex flex-wrap gap-4">
            <ModernButton loading>Loading...</ModernButton>
            <ModernButton disabled>Disabled</ModernButton>
            <ModernButton icon={<Zap className="w-4 h-4" />} iconPosition="left">
              With Icon
            </ModernButton>
          </div>

          <div className="flex flex-wrap gap-4">
            <MagneticButton>Magnetic Button</MagneticButton>
            <ShimmerButton>Shimmer Button</ShimmerButton>
            <RippleButton>Ripple Button</RippleButton>
          </div>

          <div className="flex flex-wrap gap-4">
            <IconButton icon={<Sparkles className="w-5 h-5" />} />
            <IconButton icon={<Zap className="w-5 h-5" />} variant="primary" />
            <IconButton icon={<Heart className="w-5 h-5" />} variant="gradient" size="lg" />
          </div>

          <SplitButton
            mainLabel="Split Button"
            mainOnClick={() => alert('Main action')}
            options={[
              { label: 'Option 1', onClick: () => alert('Option 1') },
              { label: 'Option 2', onClick: () => alert('Option 2') },
              { label: 'Option 3', onClick: () => alert('Option 3') }
            ]}
          />
        </section>

        {/* Loading Components */}
        <section className="space-y-8">
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white">Loading Components</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <GlassCard>
              <div className="p-8 flex flex-col items-center gap-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Spinners</h3>
                <div className="flex gap-4">
                  <Spinner size="sm" />
                  <Spinner size="md" />
                  <Spinner size="lg" />
                </div>
              </div>
            </GlassCard>

            <GlassCard>
              <div className="p-8 flex flex-col items-center gap-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Gradient Spinner</h3>
                <GradientSpinner size="lg" />
              </div>
            </GlassCard>

            <GlassCard>
              <div className="p-8 flex flex-col items-center gap-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Pulse Loader</h3>
                <PulseLoader />
              </div>
            </GlassCard>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <GlassCard>
              <div className="p-6 space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Progress Bar</h3>
                <ProgressBar progress={65} />
              </div>
            </GlassCard>

            <GlassCard>
              <div className="p-6 flex flex-col items-center gap-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Circular Progress</h3>
                <CircularProgress progress={75} />
              </div>
            </GlassCard>
          </div>

          <GlassCard>
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Skeleton Screens</h3>
              <CardSkeleton />
            </div>
          </GlassCard>
        </section>

        {/* Background Effects */}
        <section className="space-y-8">
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white">Background Effects</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="relative h-64 rounded-2xl overflow-hidden">
              <GridBackground />
              <div className="relative z-10 flex items-center justify-center h-full">
                <p className="text-xl font-bold text-gray-900 dark:text-white">Grid Background</p>
              </div>
            </div>

            <div className="relative h-64 rounded-2xl overflow-hidden bg-gray-900">
              <FloatingParticles count={30} />
              <div className="relative z-10 flex items-center justify-center h-full">
                <p className="text-xl font-bold text-white">Floating Particles</p>
              </div>
            </div>

            <div className="relative h-64 rounded-2xl overflow-hidden">
              <AnimatedGradientMesh />
              <div className="relative z-10 flex items-center justify-center h-full">
                <p className="text-xl font-bold text-gray-900 dark:text-white">Gradient Mesh</p>
              </div>
            </div>

            <div className="relative h-64 rounded-2xl overflow-hidden">
              <DotPattern />
              <div className="relative z-10 flex items-center justify-center h-full">
                <p className="text-xl font-bold text-gray-900 dark:text-white">Dot Pattern</p>
              </div>
            </div>

            <div className="relative h-64 rounded-2xl overflow-hidden bg-gray-900">
              <GlowOrbs />
              <div className="relative z-10 flex items-center justify-center h-full">
                <p className="text-xl font-bold text-white">Glow Orbs</p>
              </div>
            </div>

            <div className="relative h-64 rounded-2xl overflow-hidden">
              <AuroraBackground />
              <div className="relative z-10 flex items-center justify-center h-full">
                <p className="text-xl font-bold text-gray-900 dark:text-white">Aurora Background</p>
              </div>
            </div>
          </div>
        </section>

        {/* Feature Cards */}
        <section className="space-y-8">
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white">Feature Cards</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <FeatureCard
              icon={<Sparkles className="w-6 h-6" />}
              title="Amazing Features"
              description="Discover powerful features that make your application stand out from the crowd."
            />
            <FeatureCard
              icon={<Zap className="w-6 h-6" />}
              title="Lightning Fast"
              description="Experience blazing fast performance with optimized code and modern techniques."
            />
            <FeatureCard
              icon={<Heart className="w-6 h-6" />}
              title="User Friendly"
              description="Intuitive interface designed with user experience as the top priority."
            />
          </div>
        </section>

        {/* Pricing Cards */}
        <section className="space-y-8">
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white">Pricing Cards</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <PricingCard
              name="Basic"
              price="$9"
              period="/month"
              features={[
                '10 Projects',
                '5 GB Storage',
                'Email Support',
                'Basic Features'
              ]}
            />
            <PricingCard
              name="Pro"
              price="$29"
              period="/month"
              features={[
                'Unlimited Projects',
                '50 GB Storage',
                'Priority Support',
                'Advanced Features',
                'Analytics Dashboard'
              ]}
              highlighted
            />
            <PricingCard
              name="Premium"
              price="$99"
              period="/month"
              features={[
                'Everything in Pro',
                'Unlimited Storage',
                '24/7 Support',
                'Custom Features',
                'Dedicated Manager'
              ]}
            />
          </div>
        </section>

        {/* FAB */}
        <FAB icon={<Plus className="w-6 h-6" />} onClick={() => alert('FAB clicked!')} />
      </div>
    </div>
  );
}

/**
 * Modern Hero Section
 * Hero with stunning animations
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles, Zap, Brain, Globe } from 'lucide-react';
import { staggerContainer, staggerItem } from '@/lib/animations';
import { GridBackground, FloatingParticles, GlowOrbs } from '@/components/ui/background-effects';
import { useTypewriter } from '@/hooks/useAnimations';

export function ModernHero() {
  const { displayText } = useTypewriter('Multi-Agent Intelligence Platform', 100);

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-b from-white via-indigo-50/30 to-white dark:from-gray-950 dark:via-indigo-950/30 dark:to-gray-950">
      {/* Background Effects */}
      <GridBackground />
      <FloatingParticles count={30} />
      <GlowOrbs />

      {/* Content */}
      <motion.div
        className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        {/* Badge */}
        <motion.div variants={staggerItem} className="flex justify-center mb-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 backdrop-blur-sm">
            <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            <span className="text-sm font-medium text-indigo-600 dark:text-indigo-400">
              Public Beta · Groq-powered
            </span>
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          </div>
        </motion.div>

        {/* Main Heading */}
        <motion.h1
          variants={staggerItem}
          className="text-5xl md:text-7xl lg:text-8xl font-bold mb-6 leading-tight"
        >
          <span className="text-gradient">
            {displayText}
          </span>
          <motion.span
            animate={{ opacity: [1, 0, 1] }}
            transition={{ duration: 1, repeat: Infinity }}
            className="inline-block w-1 h-16 md:h-24 ml-2 bg-indigo-600"
          />
        </motion.h1>

        {/* Subheading */}
        <motion.p
          variants={staggerItem}
          className="text-xl md:text-2xl text-gray-600 dark:text-gray-400 mb-12 max-w-3xl mx-auto leading-relaxed"
        >
          Orchestrate intelligent agents with vision, reasoning, and action capabilities. 
          Build the future of AI-powered automation.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          variants={staggerItem}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16"
        >
          <Link href="/register">
            <motion.span
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.95 }}
              className="group inline-flex px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold shadow-lg shadow-indigo-500/50 hover:shadow-xl hover:shadow-indigo-500/60 transition-all"
            >
              <span className="flex items-center gap-2">
                Get Started
                <motion.span
                  animate={{ x: [0, 5, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  <ArrowRight className="w-5 h-5" />
                </motion.span>
              </span>
            </motion.span>
          </Link>

          <Link href="/login">
            <motion.span
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.95 }}
              className="inline-flex px-8 py-4 rounded-xl bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-800 text-gray-900 dark:text-white font-semibold hover:border-indigo-500/50 transition-all"
            >
              Sign In
            </motion.span>
          </Link>
        </motion.div>

        {/* Feature Pills */}
        <motion.div
          variants={staggerContainer}
          className="flex flex-wrap gap-4 justify-center"
        >
          {[
            { icon: Brain, text: 'AI-Powered' },
            { icon: Zap, text: 'Real-time' },
            { icon: Globe, text: 'Multi-Modal' },
          ].map((feature, index) => (
            <motion.div
              key={index}
              variants={staggerItem}
              whileHover={{ scale: 1.1, y: -5 }}
              className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border border-gray-200 dark:border-gray-800 shadow-lg"
            >
              <feature.icon className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {feature.text}
              </span>
            </motion.div>
          ))}
        </motion.div>

        {/* Floating Cards */}
        <div className="absolute inset-0 pointer-events-none">
          <motion.div
            className="absolute top-1/4 left-10 w-24 h-24 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 backdrop-blur-sm border border-white/20"
            animate={{
              y: [0, -20, 0],
              rotate: [0, 5, 0],
            }}
            transition={{
              duration: 5,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
          <motion.div
            className="absolute top-1/3 right-10 w-32 h-32 rounded-2xl bg-gradient-to-br from-pink-500/20 to-purple-500/20 backdrop-blur-sm border border-white/20"
            animate={{
              y: [0, 20, 0],
              rotate: [0, -5, 0],
            }}
            transition={{
              duration: 6,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        </div>
      </motion.div>

      {/* Scroll Indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
        animate={{ y: [0, 10, 0] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <div className="w-6 h-10 rounded-full border-2 border-gray-400 dark:border-gray-600 flex justify-center p-2">
          <motion.div
            className="w-1 h-2 rounded-full bg-indigo-600"
            animate={{ y: [0, 12, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        </div>
      </motion.div>
    </section>
  );
}

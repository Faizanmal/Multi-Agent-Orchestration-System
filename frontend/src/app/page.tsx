/**
 * Public marketing landing page
 */

"use client";

import React, { useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ModernHeader } from '@/components/layout/ModernHeader';
import { ModernHero } from '@/components/hero/ModernHero';
import { ModernChatInterface } from '@/components/chat/ModernChatInterface';
import { ModernDashboard } from '@/components/dashboard/ModernDashboard';
import {
  FeatureCard,
  TiltCard,
  PricingCard
} from '@/components/ui/animated-card';
import {
  GridBackground,
  FloatingParticles,
  AnimatedGradientMesh,
  WaveAnimation
} from '@/components/ui/background-effects';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { staggerContainer, staggerItem } from '@/lib/animations';
import {
  Brain,
  Eye,
  Cpu,
  Zap
} from 'lucide-react';

export default function LandingPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading || isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-gray-950">
        <div className="h-10 w-10 rounded-full border-4 border-indigo-500/30 border-t-indigo-600 animate-spin" />
      </div>
    );
  }

  return (
    <ThemeProvider>
      <div className="relative min-h-screen bg-white dark:bg-gray-950 overflow-hidden">
        <ModernHeader />

        <section id="hero" className="relative">
          <ModernHero />
        </section>

        <section id="features" className="relative py-24 px-4 sm:px-6 lg:px-8">
          <GridBackground />

          <motion.div
            className="max-w-7xl mx-auto"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
          >
            <motion.div variants={staggerItem} className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold text-gradient mb-4">
                Powerful Features
              </h2>
              <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                Everything you need to build intelligent agent systems
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                {
                  icon: <Brain className="w-6 h-6" />,
                  title: 'AI Orchestration',
                  description: 'Coordinate multiple AI agents seamlessly with intelligent task distribution'
                },
                {
                  icon: <Eye className="w-6 h-6" />,
                  title: 'Vision Analysis',
                  description: 'Advanced computer vision capabilities for image and video processing'
                },
                {
                  icon: <Cpu className="w-6 h-6" />,
                  title: 'Logic Engine',
                  description: 'Powerful reasoning and decision-making capabilities'
                },
                {
                  icon: <Zap className="w-6 h-6" />,
                  title: 'Real-time Processing',
                  description: 'Lightning-fast inference powered by Groq'
                }
              ].map((feature) => (
                <motion.div key={feature.title} variants={staggerItem}>
                  <FeatureCard
                    icon={feature.icon}
                    title={feature.title}
                    description={feature.description}
                  />
                </motion.div>
              ))}
            </div>
          </motion.div>
        </section>

        <section id="chat" className="relative py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-white to-gray-50 dark:from-gray-950 dark:to-gray-900">
          <AnimatedGradientMesh />

          <motion.div
            className="max-w-5xl mx-auto"
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <div className="text-center mb-12">
              <h2 className="text-4xl md:text-5xl font-bold text-gradient mb-4">
                Experience the Future of AI Chat
              </h2>
              <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                Interact with our intelligent agents in real-time
              </p>
            </div>

            <ModernChatInterface />
          </motion.div>
        </section>

        <section id="dashboard" className="relative">
          <ModernDashboard />
        </section>

        <section className="relative py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-950">
          <FloatingParticles count={20} />

          <motion.div
            className="max-w-7xl mx-auto"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
          >
            <motion.div variants={staggerItem} className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold text-gradient mb-4">
                Built for speed
              </h2>
              <p className="text-xl text-gray-600 dark:text-gray-400">
                Groq-powered inference for responsive multi-agent workflows
              </p>
            </motion.div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {[
                { value: '5', label: 'Agent Roles' },
                { value: '3+', label: 'AI Providers' },
                { value: 'Beta', label: 'Public Launch' },
                { value: 'Groq', label: 'Fast Inference' }
              ].map((stat) => (
                <motion.div
                  key={stat.label}
                  variants={staggerItem}
                  whileHover={{ scale: 1.05, y: -5 }}
                >
                  <TiltCard>
                    <div className="text-center space-y-2">
                      <p className="text-4xl font-bold text-gradient">{stat.value}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</p>
                    </div>
                  </TiltCard>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </section>

        <section id="pricing" className="relative py-24 px-4 sm:px-6 lg:px-8">
          <GridBackground gridColor="rgba(168, 85, 247, 0.1)" />

          <motion.div
            className="max-w-7xl mx-auto"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
          >
            <motion.div variants={staggerItem} className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold text-gradient mb-4">
                Choose Your Plan
              </h2>
              <p className="text-xl text-gray-600 dark:text-gray-400">
                Start free, scale as you grow
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <motion.div variants={staggerItem}>
                <PricingCard
                  name="Starter"
                  price="$0"
                  period="/month"
                  ctaHref="/register"
                  features={[
                    '5 Active Agents',
                    '100 Messages/month',
                    'Email Support',
                    'Core Automations'
                  ]}
                />
              </motion.div>

              <motion.div variants={staggerItem}>
                <PricingCard
                  name="Professional"
                  price="$49"
                  period="/month"
                  ctaHref="/register"
                  features={[
                    'Unlimited Agents',
                    '10,000 Messages/month',
                    'Priority Support',
                    'Integrations',
                    'Usage Metering'
                  ]}
                  highlighted
                />
              </motion.div>

              <motion.div variants={staggerItem}>
                <PricingCard
                  name="Premium"
                  price="Custom"
                  period=""
                  ctaHref="/register"
                  ctaLabel="Contact Us"
                  features={[
                    'Everything in Pro',
                    'Custom Limits',
                    'Dedicated Onboarding',
                    'Security Review',
                    'Priority Roadmap Input'
                  ]}
                />
              </motion.div>
            </div>
          </motion.div>
        </section>

        <section className="relative py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-indigo-600 to-purple-600 overflow-hidden">
          <WaveAnimation />

          <motion.div
            className="relative z-10 max-w-4xl mx-auto text-center"
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Ready to try the beta?
            </h2>
            <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
              Create agents, run chat workflows, and automate simple ops tasks — free to start.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/register">
                <motion.span
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  className="inline-flex px-8 py-4 rounded-xl bg-white text-indigo-600 font-semibold shadow-2xl hover:shadow-3xl transition-all"
                >
                  Start Free
                </motion.span>
              </Link>

              <Link href="/login">
                <motion.span
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  className="inline-flex px-8 py-4 rounded-xl bg-transparent border-2 border-white text-white font-semibold hover:bg-white/10 transition-all"
                >
                  Sign In
                </motion.span>
              </Link>
            </div>
          </motion.div>
        </section>

        <footer className="relative bg-gray-900 text-white py-12 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
              <div>
                <h3 className="text-lg font-bold mb-4">MultiAgent AI</h3>
                <p className="text-gray-400 text-sm">
                  Building the future of intelligent automation
                </p>
              </div>

              <div>
                <h4 className="font-semibold mb-4">Product</h4>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                  <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                  <li><Link href="/login" className="hover:text-white transition-colors">Sign In</Link></li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold mb-4">Company</h4>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li><Link href="/register" className="hover:text-white transition-colors">Get Started</Link></li>
                  <li><Link href="/dashboard" className="hover:text-white transition-colors">Dashboard</Link></li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold mb-4">Legal</h4>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li><Link href="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link></li>
                  <li><Link href="/terms" className="hover:text-white transition-colors">Terms of Service</Link></li>
                </ul>
              </div>
            </div>

            <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center">
              <p className="text-sm text-gray-400">
                © {new Date().getFullYear()} MultiAgent AI. Public beta.
              </p>
              <div className="flex gap-4 mt-4 md:mt-0">
                <Link href="/privacy" className="text-sm text-gray-400 hover:text-white transition-colors">
                  Privacy
                </Link>
                <Link href="/terms" className="text-sm text-gray-400 hover:text-white transition-colors">
                  Terms
                </Link>
                <Link href="/login" className="text-sm text-gray-400 hover:text-white transition-colors">
                  Sign In
                </Link>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </ThemeProvider>
  );
}

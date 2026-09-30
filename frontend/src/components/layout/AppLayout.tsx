"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { cn } from '@/lib/utils';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { QuotaUpgradeDialog } from '@/components/billing/QuotaUpgradeDialog';
import { ReportIssueDialog } from '@/components/support/ReportIssueDialog';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setTimeout(() => { setIsMounted(true); }, 0)
    const saved = localStorage.getItem('sidebar-collapsed');
    if (saved) {
      setTimeout(() => {
          setSidebarCollapsed(JSON.parse(saved));
        }, 0)
    }

    // Listen for storage changes
    const handleStorageChange = () => {
      const saved = localStorage.getItem('sidebar-collapsed');
      if (saved) {
        setSidebarCollapsed(JSON.parse(saved));
      }
    };

    window.addEventListener('storage', handleStorageChange);
    
    // Custom event for same-tab updates
    const handleSidebarToggle = (e: Event) => {
      setSidebarCollapsed((e as CustomEvent).detail);
    };
    window.addEventListener('sidebar-toggle', handleSidebarToggle);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('sidebar-toggle', handleSidebarToggle);
    };
  }, []);

  // Sync with localStorage on interval (for same-tab updates)
  useEffect(() => {
    const interval = setInterval(() => {
      const saved = localStorage.getItem('sidebar-collapsed');
      if (saved) {
        const value = JSON.parse(saved);
        if (value !== sidebarCollapsed) {
          setSidebarCollapsed(value);
        }
      }
    }, 100);

    return () => clearInterval(interval);
  }, [sidebarCollapsed]);

  if (!isMounted) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="relative">
          <div className="h-16 w-16 rounded-full border-4 border-primary/30 border-t-primary animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-background">
        {/* Animated Background */}
        <div className="fixed inset-0 -z-10 overflow-hidden">
          {/* Gradient Mesh Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/50 dark:from-slate-950 dark:via-slate-900 dark:to-indigo-950/30" />
          
          {/* Animated Gradient Orbs */}
          <div className="absolute top-0 -left-40 h-[500px] w-[500px] rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 blur-3xl animate-blob" />
          <div className="absolute top-1/3 -right-40 h-[400px] w-[400px] rounded-full bg-gradient-to-br from-cyan-500/20 to-blue-500/20 blur-3xl animate-blob animation-delay-2000" />
          <div className="absolute -bottom-40 left-1/3 h-[600px] w-[600px] rounded-full bg-gradient-to-br from-pink-500/10 to-rose-500/10 blur-3xl animate-blob animation-delay-4000" />
          
          {/* Grid Pattern */}
          <div 
            className="absolute inset-0 opacity-[0.02] dark:opacity-[0.03]"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60' viewBox='0 0 60 60'%3E%3Cg fill='none' stroke='%23000' stroke-width='0.5'%3E%3Cpath d='M0 0h60v60H0z'/%3E%3C/g%3E%3C/svg%3E")`,
            }}
          />
        </div>

        {/* Sidebar */}
        <Sidebar />

        {/* Main Content Area */}
        <div 
          className={cn(
            "min-h-screen transition-all duration-300",
            sidebarCollapsed ? "pl-[72px]" : "pl-[260px]"
          )}
        >
          {/* Topbar */}
          <Topbar sidebarCollapsed={sidebarCollapsed} />

          {/* Page Content */}
          <main className="pt-16">
            <AnimatePresence mode="wait">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
                className="p-6"
              >
                {children}
              </motion.div>
            </AnimatePresence>
          </main>
        </div>

        <QuotaUpgradeDialog />
        <ReportIssueDialog />
      </div>
    </ThemeProvider>
  );
}

export default AppLayout;

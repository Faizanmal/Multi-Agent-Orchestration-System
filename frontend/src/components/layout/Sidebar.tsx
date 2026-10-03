"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { CommandPalette } from './CommandPalette';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Bot,
  Workflow,
  BarChart3,
  Plug,
  Bell,
  Settings,
  Users,
  Database,
  Webhook,
  MessageSquare,
  Brain,
  Cpu,
  FileText,
  Globe,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Clock,
  CreditCard,
  LogOut,
  Search,
  Command,
  Layers,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';

interface NavItem {
  title: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  badgeVariant?: 'default' | 'secondary' | 'destructive' | 'outline';
  children?: NavItem[];
}

const navigationItems: NavItem[] = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'Workspace',
    href: '/workspace',
    icon: Layers,
  },
  {
    title: 'Agents',
    href: '/agents',
    icon: Bot,
  },
  {
    title: 'Chat',
    href: '/chat',
    icon: MessageSquare,
  },
  {
    title: 'Automations',
    href: '/automations',
    icon: Clock,
  },
  {
    title: 'Workflows',
    href: '/workflows',
    icon: Workflow,
  },
  {
    title: 'Integrations',
    href: '/integrations',
    icon: Globe,
  },
  {
    title: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
  },
  {
    title: 'Coordination',
    href: '/coordination',
    icon: Users,
  },
  {
    title: 'Intelligence',
    href: '/intelligence',
    icon: Brain,
  },
  {
    title: 'MCP Tools',
    href: '/mcp',
    icon: Cpu,
  },
  {
    title: 'Data Pipelines',
    href: '/pipelines',
    icon: Database,
  },
  {
    title: 'Plugins',
    href: '/plugins',
    icon: Plug,
  },
  {
    title: 'Webhooks',
    href: '/webhooks',
    icon: Webhook,
  },
  {
    title: 'Reports',
    href: '/reports',
    icon: FileText,
  },
  {
    title: 'Notifications',
    href: '/notifications',
    icon: Bell,
  },
];

const bottomItems: NavItem[] = [
  {
    title: 'Settings',
    href: '/settings',
    icon: Settings,
  },
  {
    title: 'Billing',
    href: '/settings/billing',
    icon: CreditCard,
  },
];

const NavItemComponent: React.FC<{
  item: NavItem;
  isCollapsed: boolean;
  isActive: boolean;
}> = ({ item, isCollapsed, isActive }) => {
  const Icon = item.icon;

  const content = (
    <Link href={item.href}>
      <motion.div
        className={cn(
          "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 font-medium transition-all duration-200",
          isActive
            ? "bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 text-primary"
            : "text-muted-foreground hover:bg-muted hover:text-foreground"
        )}
        whileHover={{ x: 4 }}
        whileTap={{ scale: 0.98 }}
      >
        {/* Active indicator */}
        {isActive && (
          <motion.div
            layoutId="activeIndicator"
            className="absolute left-0 top-1/2 h-8 w-1 -translate-y-1/2 rounded-r-full bg-gradient-to-b from-indigo-500 to-purple-500"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.2 }}
          />
        )}

        <Icon className={cn(
          "h-5 w-5 shrink-0 transition-colors",
          isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
        )} />

        {!isCollapsed && (
          <motion.span
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            className="flex-1 truncate"
          >
            {item.title}
          </motion.span>
        )}

        {!isCollapsed && item.badge && (
          <Badge 
            variant={item.badgeVariant || 'secondary'}
            className="ml-auto h-5 px-1.5 text-xs"
          >
            {item.badge}
          </Badge>
        )}
      </motion.div>
    </Link>
  );

  if (isCollapsed) {
    return (
      <TooltipProvider delayDuration={0}>
        <Tooltip>
          <TooltipTrigger asChild>{content}</TooltipTrigger>
          <TooltipContent side="right" className="flex items-center gap-2">
            {item.title}
            {item.badge && (
              <Badge variant={item.badgeVariant || 'secondary'} className="h-5 px-1.5 text-xs">
                {item.badge}
              </Badge>
            )}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return content;
};

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const [openCommand, setOpenCommand] = useState(false);

  const displayName = user?.display_name || user?.username || user?.email || 'User';
  const initials = displayName
    .split(/\s+/)
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
  const tierLabel = user?.subscription_tier
    ? `${user.subscription_tier.charAt(0).toUpperCase()}${user.subscription_tier.slice(1)} Plan`
    : 'Free Plan';

  const handleLogout = async () => {
    await logout();
    router.replace('/login');
  };

  useEffect(() => {
    setTimeout(() => { setIsMounted(true); }, 0)
    // Check localStorage for saved preference
    const saved = localStorage.getItem('sidebar-collapsed');
    if (saved) {
      setTimeout(() => {
          setIsCollapsed(JSON.parse(saved));
        }, 0)
    }
  }, []);

  const toggleCollapsed = () => {
    setIsCollapsed(!isCollapsed);
    localStorage.setItem('sidebar-collapsed', JSON.stringify(!isCollapsed));
  };

  if (!isMounted) return null;

  return (
    <>
    <motion.aside
      initial={false}
      animate={{ width: isCollapsed ? 72 : 260 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-border/50",
        "bg-gradient-to-b from-background via-background to-muted/20",
        "backdrop-blur-xl"
      )}
    >
      {/* Logo Section */}
      <div className={cn(
        "flex h-16 items-center border-b border-border/50 px-4",
        isCollapsed ? "justify-center" : "justify-between"
      )}>
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="relative flex h-9 w-9 items-center justify-center">
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 opacity-80" />
            <div className="absolute inset-0.5 rounded-[10px] bg-background" />
            <Sparkles className="relative h-5 w-5 text-primary" />
          </div>
          <AnimatePresence mode="wait">
            {!isCollapsed && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
              >
                <span className="text-lg font-bold gradient-text">MultiAgent</span>
                <span className="text-xs text-muted-foreground block -mt-0.5">AI Platform</span>
              </motion.div>
            )}
          </AnimatePresence>
        </Link>
      </div>

      {/* Search Button */}
      <div className={cn("px-3 py-3", isCollapsed && "px-2")}>
        <Button
          variant="outline"
          className={cn(
            "w-full justify-start gap-2 rounded-xl border-dashed text-muted-foreground",
            isCollapsed && "justify-center px-0"
          )}
          onClick={() => {
            setOpenCommand(true);
          }}
        >
          <Search className="h-4 w-4" />
          {!isCollapsed && (
            <>
              <span className="flex-1 text-left">Search...</span>
              <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
                <Command className="h-3 w-3" />K
              </kbd>
            </>
          )}
        </Button>
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 px-3">
        <nav className="flex flex-col gap-1 py-2">
          {navigationItems.map((item) => (
            <NavItemComponent
              key={item.href}
              item={item}
              isCollapsed={isCollapsed}
              isActive={pathname === item.href || pathname?.startsWith(item.href + '/')}
            />
          ))}
        </nav>
      </ScrollArea>

      {/* Bottom Section */}
      <div className="mt-auto border-t border-border/50 p-3">
        <nav className="flex flex-col gap-1">
          {bottomItems.map((item) => (
            <NavItemComponent
              key={item.href}
              item={item}
              isCollapsed={isCollapsed}
              isActive={pathname === item.href}
            />
          ))}
        </nav>

        {/* User Profile / Logout */}
        <div className={cn(
          "mt-3 flex items-center gap-3 rounded-xl bg-muted/50 p-2",
          isCollapsed && "justify-center"
        )}>
          <div className="relative h-8 w-8 shrink-0">
            <div className="absolute inset-0 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500" />
              <div className="absolute inset-0.5 rounded-full bg-background flex items-center justify-center">
              <span className="text-xs font-semibold">{initials}</span>
            </div>
            <span className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-background bg-green-500" />
          </div>
          <AnimatePresence mode="wait">
            {!isCollapsed && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="flex-1 min-w-0"
              >
                <p className="truncate text-sm font-medium">{displayName}</p>
                <p className="truncate text-xs text-muted-foreground">{tierLabel}</p>
              </motion.div>
            )}
          </AnimatePresence>
          {!isCollapsed && (
            <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={handleLogout} title="Sign out">
              <LogOut className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={toggleCollapsed}
        className={cn(
          "absolute -right-3 top-20 z-50 flex h-6 w-6 items-center justify-center",
          "rounded-full border bg-background shadow-md",
          "transition-transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-primary"
        )}
      >
        {isCollapsed ? (
          <ChevronRight className="h-3 w-3" />
        ) : (
          <ChevronLeft className="h-3 w-3" />
        )}
      </button>
    </motion.aside>
      <CommandPalette open={openCommand} setOpen={setOpenCommand} />
    </>
  );
}

export default Sidebar;

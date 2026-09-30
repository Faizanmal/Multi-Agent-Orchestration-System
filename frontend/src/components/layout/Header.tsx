"use client";

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Moon, Sun, Zap, Activity, Settings, Brain } from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';
import { useRouter } from 'next/navigation';
import { useAgent } from '@/contexts/AgentContext';
import { WorkspaceSwitcher } from '@/components/workspace/WorkspaceSwitcher';

export default function Header() {
  const { isDark, toggleTheme } = useTheme();
  const { agents, activeAgents, isOrchestrating } = useAgent();
  const router = useRouter();
  const [avgLatency, setAvgLatency] = useState(0);

  useEffect(() => {
    const activeAgentsList = agents.filter(agent => activeAgents.has(agent.id));
    const totalLatency = activeAgentsList.reduce((sum, agent) => sum + (agent.latency ?? 0), 0);
    setTimeout(() => { setAvgLatency(activeAgentsList.length > 0 ? Math.round(totalLatency / activeAgentsList.length) : 0); }, 0)
  }, [agents, activeAgents]);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200/50 dark:border-slate-700/50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-8">
          <div className="flex items-center space-x-2">
            <div className="relative">
              <Brain className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${
                isOrchestrating ? 'bg-green-400 animate-pulse' : 'bg-slate-300'
              }`} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                MultiAgent AI
              </h1>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Orchestration Platform
              </p>
            </div>
          </div>

          <div className="hidden md:block">
            <WorkspaceSwitcher />
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="hidden md:flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Zap className="h-4 w-4 text-orange-500" />
              <Badge variant="secondary" className="text-xs">
                {avgLatency}ms avg
              </Badge>
            </div>
            
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-green-500" />
              <Badge variant="secondary" className="text-xs">
                {activeAgents.size} active
              </Badge>
            </div>

            {isOrchestrating && (
              <Badge className="bg-blue-500 text-white animate-pulse">
                Orchestrating
              </Badge>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="default"
              size="sm"
              className="hidden md:flex bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white border-0 h-9"
              onClick={() => router.push('/settings/billing')}
            >
              Upgrade to Pro
            </Button>

            <Button
              variant="outline"
              size="icon"
              onClick={toggleTheme}
              className="w-9 h-9"
            >
              {isDark ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </Button>

            <Button
              variant="outline"
              size="icon"
              className="w-9 h-9"
            >
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
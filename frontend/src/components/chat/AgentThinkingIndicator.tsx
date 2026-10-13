import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, Sparkles, Cpu, Search } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

const thinkingSteps = [
  { text: 'Analyzing intent...', icon: <Bot className="w-4 h-4" /> },
  { text: 'Searching knowledge base...', icon: <Search className="w-4 h-4" /> },
  { text: 'Synthesizing data...', icon: <Cpu className="w-4 h-4" /> },
  { text: 'Formulating response...', icon: <Sparkles className="w-4 h-4" /> },
];

export interface AgentThinkingIndicatorProps {
  /** Live status from WebSocket (stream_start / agent_status_update). */
  status?: string | null;
  /** Optional detail line from the backend. */
  detail?: string | null;
}

export function AgentThinkingIndicator({
  status,
  detail,
}: AgentThinkingIndicatorProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const liveLabel = status?.trim() || detail?.trim() || null;

  useEffect(() => {
    if (liveLabel) return;
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % thinkingSteps.length);
    }, 2000);
    return () => clearInterval(interval);
  }, [liveLabel]);

  const displayText = liveLabel || thinkingSteps[currentStep].text;
  const displayIcon = liveLabel
    ? <Sparkles className="w-4 h-4" />
    : thinkingSteps[currentStep].icon;

  return (
    <Card className="mr-12 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-transparent border-indigo-500/30 relative overflow-hidden">
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-12"
        animate={{ x: ['-100%', '200%'] }}
        transition={{ repeat: Infinity, duration: 2, ease: 'linear' }}
      />

      <CardContent className="p-4 relative z-10">
        <div className="flex items-start space-x-3">
          <motion.div
            animate={{ scale: [1, 1.1, 1], rotate: [0, 5, -5, 0] }}
            transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
            className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gradient-to-br from-indigo-500 to-purple-500 shadow-lg shadow-indigo-500/30"
          >
            <Bot className="h-4 w-4 text-white" />
          </motion.div>

          <div className="flex-1 flex flex-col justify-center h-8">
            <AnimatePresence mode="wait">
              <motion.div
                key={displayText}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
                className="flex items-center space-x-2 text-sm font-medium bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400"
              >
                <span className="text-indigo-500">{displayIcon}</span>
                <span>{displayText}</span>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

"use client";

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useAgent } from '@/contexts/AgentContext';
import { formatDistanceToNow } from 'date-fns';
import { History, Download, Play, MessageSquare, Brain } from 'lucide-react';

export default function SessionHistory() {
  const { messages, reasoningSteps, exportSession } = useAgent();
  const [selectedSession, setSelectedSession] = useState<string | null>(null);

  // Group messages by session (simplified - in real app would be more sophisticated)
  const sessions = [
    {
      id: 'session-1',
      name: 'Image Analysis Workflow',
      timestamp: new Date(new Date().getTime() - 3600000),
      messageCount: 8,
      agentsUsed: ['claude-vision', 'gpt-4'],
      status: 'completed'
    },
    {
      id: 'session-2', 
      name: 'Voice Processing Task',
      timestamp: new Date(new Date().getTime() - 7200000),
      messageCount: 12,
      agentsUsed: ['whisper', 'groq-fast'],
      status: 'completed'
    },
    {
      id: 'session-3',
      name: 'Multi-Modal Research',
      timestamp: new Date(new Date().getTime() - 86400000),
      messageCount: 24,
      agentsUsed: ['gpt-4', 'claude-vision', 'whisper', 'groq-fast'],
      status: 'completed'
    }
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-slate-900 dark:text-white">
          Session History
        </h4>
        <Badge variant="outline" className="text-xs">
          {sessions.length} sessions
        </Badge>
      </div>

      <ScrollArea className="h-[200px]">
        <div className="space-y-2">
          {sessions.map((session) => (
            <Card 
              key={session.id} 
              className={`p-3 cursor-pointer transition-colors ${
                selectedSession === session.id 
                  ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' 
                  : 'bg-slate-50/50 dark:bg-slate-700/50 hover:bg-slate-100/50 dark:hover:bg-slate-600/50'
              }`}
              onClick={() => setSelectedSession(selectedSession === session.id ? null : session.id)}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <History className="h-4 w-4 text-slate-500" />
                  <h5 className="text-sm font-medium text-slate-900 dark:text-white">
                    {session.name}
                  </h5>
                </div>
                <Badge variant={session.status === 'completed' ? 'secondary' : 'outline'} className="text-xs">
                  {session.status}
                </Badge>
              </div>
              
              <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400">
                <div className="flex items-center space-x-3">
                  <span className="flex items-center space-x-1">
                    <MessageSquare className="h-3 w-3" />
                    <span>{session.messageCount} messages</span>
                  </span>
                  <span>{session.agentsUsed.length} agents</span>
                </div>
                <span>{formatDistanceToNow(session.timestamp, { addSuffix: true })}</span>
              </div>
              
              {selectedSession === session.id && (
                <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-600">
                  <div className="flex items-center justify-between">
                    <div className="flex flex-wrap gap-1">
                      {session.agentsUsed.map((agentId) => (
                        <Badge key={agentId} variant="outline" className="text-xs">
                          {agentId}
                        </Badge>
                      ))}
                    </div>
                    <div className="flex space-x-1">
                      <Button variant="outline" size="sm">
                        <Play className="h-3 w-3" />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => exportSession('json')}>
                        <Download className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      </ScrollArea>

      {/* Current Session Stats */}
      <Card className="p-3 bg-slate-50/50 dark:bg-slate-700/50">
        <h5 className="text-sm font-medium text-slate-900 dark:text-white mb-2">
          Current Session
        </h5>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="flex items-center space-x-2">
            <MessageSquare className="h-3 w-3 text-blue-500" />
            <span className="text-slate-600 dark:text-slate-400">
              {messages.length} messages
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <Brain className="h-3 w-3 text-purple-500" />
            <span className="text-slate-600 dark:text-slate-400">
              {reasoningSteps.length} reasoning steps
            </span>
          </div>
        </div>
      </Card>
    </div>
  );
}
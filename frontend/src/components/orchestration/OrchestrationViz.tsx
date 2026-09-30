"use client";

import { useAgent, Agent } from '@/contexts/AgentContext';
import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Activity, Clock } from 'lucide-react';

export default function OrchestrationViz() {
  const { agents, activeAgents, isOrchestrating, reasoningSteps } = useAgent();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [hoveredAgent, setHoveredAgent] = useState<string | null>(null);
  const getColorHex = (colorClass: string) => {
    const colorMap: Record<string, string> = {
      'bg-blue-500': '#3B82F6',
      'bg-purple-500': '#8B5CF6',
      'bg-green-500': '#10B981',
      'bg-orange-500': '#F97316',
    };
    return colorMap[colorClass] || '#94A3B8';
  };

  const lightenColor = (hex: string, percent: number) => {
    const num = parseInt(hex.replace("#", ""), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) + amt;
    const G = (num >> 8 & 0x00FF) + amt;
    const B = (num & 0x0000FF) + amt;
    return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
      (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
      (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1);
  };
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const activeAgentsList = agents.filter(agent => activeAgents.has(agent.id));
        
        // Handle canvas clicks
        const handleCanvasClick = (event: MouseEvent) => {
          const rect = canvas.getBoundingClientRect();
          const x = event.clientX - rect.left;
          const y = event.clientY - rect.top;
          
          const centerX = canvas.width / 2;
          const centerY = canvas.height / 2;
          const radius = 60;
          
          activeAgentsList.forEach((agent, index) => {
            const angle = (index / activeAgentsList.length) * 2 * Math.PI - Math.PI / 2;
            const agentX = centerX + Math.cos(angle) * radius;
            const agentY = centerY + Math.sin(angle) * radius;
            
            const distance = Math.sqrt((x - agentX) ** 2 + (y - agentY) ** 2);
            if (distance <= 12) {
              setSelectedAgent(agent);
            }
          });
        };
        
        canvas.addEventListener('click', handleCanvasClick);
        
        const animate = () => {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          
          const centerX = canvas.width / 2;
          const centerY = canvas.height / 2;
          const radius = 60;
          
          // Draw center node
          ctx.beginPath();
          ctx.arc(centerX, centerY, 12, 0, 2 * Math.PI);
          const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, 15);
          if (isOrchestrating) {
            gradient.addColorStop(0, '#60A5FA');
            gradient.addColorStop(1, '#3B82F6');
          } else {
            gradient.addColorStop(0, '#CBD5E1');
            gradient.addColorStop(1, '#94A3B8');
          }
          ctx.fillStyle = gradient;
          ctx.fill();
          
          // Add glow effect when orchestrating
          if (isOrchestrating) {
            ctx.shadowColor = '#3B82F6';
            ctx.shadowBlur = 20;
            ctx.beginPath();
            ctx.arc(centerX, centerY, 15, 0, 2 * Math.PI);
            ctx.fill();
            ctx.shadowBlur = 0;
          }
          
          // Draw agent nodes and connections
          activeAgentsList.forEach((agent, index) => {
            const angle = (index / activeAgentsList.length) * 2 * Math.PI - Math.PI / 2;
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;
            
            // Draw animated connection lines
            if (isOrchestrating) {
              const time = Date.now() * 0.005;
              const pulseOffset = Math.sin(time + index) * 0.5 + 0.5;
              
              ctx.beginPath();
              ctx.moveTo(centerX, centerY);
              ctx.lineTo(x, y);
              ctx.strokeStyle = `rgba(59, 130, 246, ${0.3 + pulseOffset * 0.7})`;
              ctx.lineWidth = 2 + pulseOffset * 2;
              ctx.stroke();
              
              // Data flow animation
              const flowProgress = (time + index) % 2;
              if (flowProgress < 1) {
                const flowX = centerX + (x - centerX) * flowProgress;
                const flowY = centerY + (y - centerY) * flowProgress;
                
                ctx.beginPath();
                ctx.arc(flowX, flowY, 3, 0, 2 * Math.PI);
                ctx.fillStyle = '#60A5FA';
                ctx.fill();
              }
            }
            
            // Draw agent node with enhanced styling
            const nodeRadius = hoveredAgent === agent.id ? 12 : 10;
            const nodeGradient = ctx.createRadialGradient(x, y, 0, x, y, nodeRadius);
            const color = getColorHex(agent.color);
            nodeGradient.addColorStop(0, lightenColor(color, 20));
            nodeGradient.addColorStop(1, color);
            
            ctx.beginPath();
            ctx.arc(x, y, nodeRadius, 0, 2 * Math.PI);
            ctx.fillStyle = nodeGradient;
            ctx.fill();
            
            // Add status indicator
            if (agent.status === 'processing') {
              const pulseRadius = 4 + Math.sin(Date.now() * 0.01 + index) * 2;
              ctx.beginPath();
              ctx.arc(x, y, pulseRadius, 0, 2 * Math.PI);
              ctx.fillStyle = '#10B981';
              ctx.globalAlpha = 0.7;
              ctx.fill();
              ctx.globalAlpha = 1;
            } else if (agent.status === 'error') {
              ctx.beginPath();
              ctx.arc(x + 8, y - 8, 4, 0, 2 * Math.PI);
              ctx.fillStyle = '#EF4444';
              ctx.fill();
            }
            
            // Draw agent label
            ctx.fillStyle = hoveredAgent === agent.id ? '#1E293B' : '#64748B';
            ctx.font = hoveredAgent === agent.id ? 'bold 10px system-ui' : '10px system-ui';
            ctx.textAlign = 'center';
            ctx.fillText(agent.name.split(' ')[0], x, y + 20);
            
            // Draw latency indicator
            if (hoveredAgent === agent.id) {
              ctx.fillStyle = '#94A3B8';
              ctx.font = '8px system-ui';
              ctx.fillText(`${agent.latency}ms`, x, y + 35);
            }
          });
          
          if (isOrchestrating) {
            requestAnimationFrame(animate);
          }
        };
        
        animate();
        
        return () => {
          canvas.removeEventListener('click', handleCanvasClick);
        };
      }, [agents, activeAgents, isOrchestrating, hoveredAgent]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-center">
        <canvas
          ref={canvasRef}
          width={280}
          height={200}
          className="border border-slate-200/50 dark:border-slate-700/50 rounded-lg bg-slate-50/50 dark:bg-slate-900/50 cursor-pointer"
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = 140;
            const centerY = 100;
            const radius = 60;
            
            let hoveredId = null;
            agents.filter(agent => activeAgents.has(agent.id)).forEach((agent, index) => {
              const angle = (index / agents.filter(a => activeAgents.has(a.id)).length) * 2 * Math.PI - Math.PI / 2;
              const agentX = centerX + Math.cos(angle) * radius;
              const agentY = centerY + Math.sin(angle) * radius;
              
              const distance = Math.sqrt((x - agentX) ** 2 + (y - agentY) ** 2);
              if (distance <= 12) {
                hoveredId = agent.id;
              }
            });
            
            setHoveredAgent(hoveredId);
          }}
          onMouseLeave={() => setHoveredAgent(null)}
        />
      </div>
      
      {/* Agent Details Modal */}
      {selectedAgent && (
        <Card className="p-4 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3">
              <div className={`w-8 h-8 ${selectedAgent.color} rounded-lg flex items-center justify-center text-white`}>
                {selectedAgent.avatar || selectedAgent.name.charAt(0)}
              </div>
              <div>
                <h4 className="font-medium text-slate-900 dark:text-white">
                  {selectedAgent.name}
                </h4>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  {selectedAgent.type} agent
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedAgent(null)}
            >
              ×
            </Button>
          </div>
          
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-slate-500" />
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  {selectedAgent.latency}ms avg
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <Activity className="h-4 w-4 text-green-500" />
                <Badge variant={
                  selectedAgent.status === 'processing' ? 'default' : 
                  selectedAgent.status === 'error' ? 'destructive' : 'secondary'
                }>
                  {selectedAgent.status}
                </Badge>
              </div>
            </div>
            
            <div>
              <h5 className="text-sm font-medium text-slate-900 dark:text-white mb-2">
                Capabilities
              </h5>
              <div className="flex flex-wrap gap-1">
                {selectedAgent.capabilities.map((capability) => (
                  <Badge key={capability} variant="outline" className="text-xs">
                    {capability}
                  </Badge>
                ))}
              </div>
            </div>
            
            {/* Recent reasoning steps */}
            {reasoningSteps.filter(step => step.agentId === selectedAgent.id).length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-slate-900 dark:text-white mb-2">
                  Recent Activity
                </h5>
                <ScrollArea className="h-20">
                  <div className="space-y-1">
                    {reasoningSteps
                      .filter(step => step.agentId === selectedAgent.id)
                      .slice(-3)
                      .map((step) => (
                        <p key={step.id} className="text-xs text-slate-600 dark:text-slate-400">
                          {step.step}
                        </p>
                      ))}
                  </div>
                </ScrollArea>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
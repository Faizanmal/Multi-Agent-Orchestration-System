"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { 
  Send, 
  Brain, 
  Eye, 
  Cpu, 
  Zap, 
  Database, 
  Bot,
  Image,
  FileText,
  Mic,
  Settings
} from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';
import { toast } from '@/hooks/use-toast';
import useWebSocket from 'react-use-websocket';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAgent } from '@/contexts/AgentContext';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  agentId?: string;
  agentName?: string;
  agentType?: string;
  timestamp: Date;
  type: 'text' | 'image' | 'file';
  status?: 'sending' | 'sent' | 'processing' | 'completed' | 'error';
}

interface Agent {
  id: string;
  name: string;
  type: 'orchestrator' | 'vision' | 'reasoning' | 'action' | 'memory' | 'custom';
  status: 'idle' | 'active' | 'processing' | 'error' | 'offline';
  capabilities: string[];
}

const agentTypeIcons = {
  orchestrator: Brain,
  vision: Eye,
  reasoning: Cpu,
  action: Zap,
  memory: Database,
  custom: Settings,
};

const agentTypeColors = {
  orchestrator: 'text-blue-600',
  vision: 'text-purple-600',
  reasoning: 'text-green-600',
  action: 'text-orange-600',
  memory: 'text-indigo-600',
  custom: 'text-gray-600',
};

export default function AgentChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<string>('auto');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Use enhanced agent context
  const { optimizeAgentSelection, getAgentPerformance } = useAgent();

  // WebSocket connection
  const wsUrl = sessionId ? `ws://localhost:8000/ws/session/${sessionId}/` : null;
  const { sendMessage: sendWebSocketMessage, lastMessage } = useWebSocket(
    wsUrl,
    {
      shouldReconnect: () => true,
      reconnectAttempts: 10,
      reconnectInterval: 3000,
    },
    Boolean(wsUrl) // Only connect when sessionId is available
  );

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data = JSON.parse(lastMessage.data);
        console.log('Received WebSocket message:', data);
        
        if (data.type === 'agent_response') {
          // Decode HTML entities in the content
          const decodeHtmlEntities = (text: string) => {
            const textarea = document.createElement('textarea');
            textarea.innerHTML = text;
            return textarea.value;
          };
          
          const rawContent = typeof data.response.content === 'string' ? decodeHtmlEntities(data.response.content) : String(data.response.content);
          console.log('Raw message content:', rawContent);
          console.log('Message contains markdown:', rawContent.includes('##') || rawContent.includes('**') || rawContent.includes('```') || rawContent.includes('- '));
          
          const agentMessage: Message = {
            id: (Date.now() + Math.random()).toString(),
            content: rawContent,
            sender: 'agent',
            agentName: data.response.orchestrator || 'Agent',
            timestamp: new Date(data.timestamp || Date.now()),
            type: 'text',
            status: 'completed'
          };
          
          console.log('Created agent message:', agentMessage);
          setTimeout(() => { setMessages(prev => [...prev, agentMessage]); }, 0)
          setTimeout(() => {
              setIsLoading(false);
            }, 0)
        } else if (data.type === 'error') {
          toast({
            title: "Error",
            description: data.message || "An error occurred",
            variant: "destructive"
          });
          setTimeout(() => setIsLoading(false), 0);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    }
  }, [lastMessage]);

  // Load agents from API
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const response = await fetch('http://localhost:8000/agents/api/agents/');
        const data = await response.json();
        
        if (data.results) {
          const loadedAgents = data.results.slice(0, 20).map((agent: { id: string; name: string; type: string; status: string; capabilities?: string[] }) => ({
            id: agent.id,
            name: agent.name,
            type: agent.type,
            status: agent.status,
            capabilities: agent.capabilities || []
          }));
          setAgents(loadedAgents);
          
          // Add welcome message
          const welcomeMessage: Message = {
            id: 'welcome',
            content: `🤖 Welcome! I've loaded ${data.count} agents. You can chat with specific agents or let me choose the best one for your task.`,
            sender: 'agent',
            agentName: 'System',
            timestamp: new Date(),
            type: 'text',
            status: 'completed'
          };
          setMessages([welcomeMessage]);
        }
      } catch (error) {
        console.error('Failed to load agents:', error);
        toast({
          title: "Connection Error",
          description: "Could not connect to backend. Make sure localhost:8000 is running.",
          variant: "destructive"
        });
      }
    };

    loadAgents();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Send message to agent
  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const messageContent = inputMessage; // Save before clearing
    const userMessage: Message = {
      id: Date.now().toString(),
      content: messageContent,
      sender: 'user',
      timestamp: new Date(),
      type: 'text',
      status: 'sent'
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Create session if needed
      if (!sessionId) {
        const sessionResponse = await fetch('http://localhost:8000/agents/api/sessions/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: `Chat Session ${new Date().toLocaleTimeString()}`,
            agents: selectedAgent === 'auto' ? [] : [selectedAgent]
          })
        });
        const newSession = await sessionResponse.json();
        setSessionId(newSession.id);
        
        // Wait for WebSocket to connect
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      // Enhanced agent selection if auto mode
      let targetAgent = selectedAgent;
      if (selectedAgent === 'auto') {
        const recommendedAgents = optimizeAgentSelection('text', messageContent);
        if (recommendedAgents.length > 0) {
          // Select the highest performing agent from recommendations
          let bestAgentId = recommendedAgents[0];
          let bestPerformance = getAgentPerformance(bestAgentId);
          
          for (const agentId of recommendedAgents) {
            const performance = getAgentPerformance(agentId);
            if (performance > bestPerformance) {
              bestAgentId = agentId;
              bestPerformance = performance;
            }
          }
          
          targetAgent = bestAgentId;
        }
      }

      // Send message via WebSocket
      if (sendWebSocketMessage) {
        console.log('Sending message via WebSocket:', messageContent);
        sendWebSocketMessage(JSON.stringify({
          type: 'chat_message',
          content: messageContent, // Use saved content, not cleared inputMessage
          message_type: 'text',
          metadata: {
            target_agent: targetAgent !== 'auto' ? targetAgent : undefined
          }
        }));
      } else {
        throw new Error('WebSocket not connected');
      }

    } catch (error) {
      console.error('Failed to send message:', error);
      setIsLoading(false);
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive"
      });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[80vh]">
      {/* Agent Selection Panel */}
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Available Agents
          </CardTitle>
          <CardDescription>
            Choose an agent or let the system select automatically
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Select value={selectedAgent} onValueChange={setSelectedAgent}>
            <SelectTrigger>
              <SelectValue placeholder="Select an agent" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="auto">🤖 Auto-Select Best Agent</SelectItem>
              <Separator />
              {agents.map((agent) => {
                const IconComponent = agentTypeIcons[agent.type];
                return (
                  <SelectItem key={agent.id} value={agent.id}>
                    <div className="flex items-center gap-2">
                      <IconComponent className={`h-4 w-4 ${agentTypeColors[agent.type]}`} />
                      <span>{agent.name}</span>
                      <Badge 
                        variant="outline" 
                        className={agent.status === 'active' ? 'border-green-500 text-green-700' : ''}
                      >
                        {agent.status}
                      </Badge>
                    </div>
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>

          {/* Quick Task Templates */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Quick Tasks:</h4>
            <div className="space-y-1">
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full justify-start text-left"
                onClick={() => setInputMessage("Analyze this image for objects and text")}
              >
                👁️ Image Analysis
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full justify-start text-left"
                onClick={() => setInputMessage("Help me solve this problem logically")}
              >
                🧠 Logical Reasoning
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full justify-start text-left"
                onClick={() => setInputMessage("Execute this task and integrate with external APIs")}
              >
                ⚡ Action Execution
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full justify-start text-left"
                onClick={() => setInputMessage("Remember this information for future use")}
              >
                💾 Store Information
              </Button>
            </div>
          </div>

          {/* Agent Stats */}
          <div className="space-y-2 pt-4 border-t">
            <div className="text-sm">
              <div className="flex justify-between">
                <span>Total Agents:</span>
                <Badge variant="secondary">{agents.length}</Badge>
              </div>
              <div className="flex justify-between mt-1">
                <span>Active:</span>
                <Badge variant="secondary" className="bg-green-100 text-green-800">
                  {agents.filter(a => a.status === 'active').length}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Chat Interface */}
      <Card className="lg:col-span-3 flex flex-col">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Send className="h-5 w-5" />
            Agent Chat Interface
          </CardTitle>
          <CardDescription>
            Communicate with your 702 intelligent agents
          </CardDescription>
        </CardHeader>
        
        {/* Messages Area */}
        <CardContent className="flex-1 flex flex-col">
          <ScrollArea className="flex-1 mb-4 h-96">
            <div className="space-y-4 pr-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      message.sender === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-muted'
                    }`}
                  >
                    {message.sender === 'agent' && message.agentName && (
                      <div className="flex items-center gap-2 mb-1">
                        {message.agentType && agentTypeIcons[message.agentType as keyof typeof agentTypeIcons] && (
                          React.createElement(agentTypeIcons[message.agentType as keyof typeof agentTypeIcons], {
                            className: `h-4 w-4 ${agentTypeColors[message.agentType as keyof typeof agentTypeColors]}`
                          })
                        )}
                        <span className="text-xs font-medium text-muted-foreground">
                          {message.agentName}
                        </span>
                      </div>
                    )}
                    {message.sender === 'agent' ? (
                      <div className="text-sm prose prose-sm max-w-none dark:prose-invert">
                        <ReactMarkdown 
                          key={message.id}
                          remarkPlugins={[remarkGfm]}
                        >
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm">{message.content}</p>
                    )}
                    <p className="text-xs mt-1 opacity-70">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-muted rounded-lg p-3 max-w-[80%]">
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                      <span className="text-sm">Agent is thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="border-t pt-4">
            <div className="flex gap-2">
              <Textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask your agents anything... (Press Enter to send, Shift+Enter for new line)"
                className="min-h-[60px] resize-none"
                disabled={isLoading}
              />
              <Button
                onClick={sendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="px-4"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            
            {/* Input Tools */}
            <div className="flex justify-between items-center mt-2">
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" aria-label="Upload image">
                  <Image className="h-4 w-4" aria-label="Upload Image" role="img" />
                </Button>
                <Button variant="ghost" size="sm">
                  <FileText className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <Mic className="h-4 w-4" />
                </Button>
              </div>
              <div className="text-xs text-muted-foreground">
                {selectedAgent === 'auto' ? 'Auto-selecting best agent' : 
                 `Chatting with ${agents.find(a => a.id === selectedAgent)?.name || 'Selected Agent'}`}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
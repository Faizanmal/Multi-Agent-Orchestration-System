"use client";

/* eslint-disable @typescript-eslint/no-explicit-any */

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare,
  Send,
  Paperclip,
  User,
  MoreVertical,
  Trash2,
  Copy,
  Check,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  Plus,
  Search,
  Sparkles,
  Zap,
  Download,
  Star,
  Archive,
  Pin,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { cn } from '@/lib/utils';
import { getSessions, getMessages, sendMessage, getAgents, createSession, addAgentToSession } from '@/lib/api';
import { axiosErrorDetail, errorMessage as getErrorMessage, isQuotaLimitError } from '@/types/api';
import { dispatchQuotaLimit } from '@/components/billing/QuotaUpgradeDialog';
import { trackEvent, trackOnce } from '@/lib/analytics';
import Link from 'next/link';
import { useWebSocket } from '@/hooks/useWebSocket';
import { AgentThinkingIndicator } from '@/components/chat/AgentThinkingIndicator';
export default function ChatPage() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [thinkingStatus, setThinkingStatus] = useState<string | null>(null);
  const [apiAgents, setApiAgents] = useState<any[]>([]);
  const [apiConversations, setApiConversations] = useState<any[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [selectedConversation, setSelectedConversation] = useState<any>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      try {
        const [agentsRes, sessionsRes] = await Promise.all([
          getAgents(),
          getSessions()
        ]);
        
        const agents = (agentsRes as any).results || [];
        const sessions = ((sessionsRes as any).results || []).map((s: any) => ({
          ...s,
          title: s.name || 'Conversation',
          agent: s.agents && s.agents.length > 0 ? s.agents[0].name : 'Orchestrator',
          agentId: s.agents && s.agents.length > 0 ? s.agents[0].id : null,
          lastMessage: s.status || 'Active',
          time: new Date(s.created_at).toLocaleDateString(),
          unread: 0,
          pinned: false
        }));
        
        setApiAgents(agents);
        setApiConversations(sessions);
        
        if (agents.length > 0) setSelectedAgent(agents[0]);
        if (sessions.length > 0) setSelectedConversation(sessions[0]);
      } catch (err) {
        console.error('Failed to load chat data:', err);
      }
    };
    loadData();
  }, []);

  // Load messages when conversation changes
  useEffect(() => {
    const loadConversationMessages = async () => {
      if (!selectedConversation?.id) return;
      try {
        const msgsRes = await getMessages(selectedConversation.id);
        const msgs = (msgsRes as any).results || [];
        setMessages(msgs.map((m: any) => ({
          id: m.id,
          role: m.sender_name ? 'user' : 'assistant',
          content: m.content || m.metadata?.content || 'No content',
          timestamp: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          agent: m.sender_name ? undefined : (selectedAgent?.name || 'Agent')
        })));
      } catch (err) {
        console.error('Failed to load messages:', err);
      }
    };
    loadConversationMessages();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload when conversation changes
  }, [selectedConversation?.id]);

  const wsUrl = selectedConversation?.id 
    ? `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/session/${selectedConversation.id}/` 
    : '';

  const { sendMessage: wsSendMessage, connectionStatus } = useWebSocket({
    url: wsUrl,
    onMessage: (msg) => {
      console.log("WS Msg:", msg);
      if (msg.type === 'chat_message') {
        const payload = msg.message as any;
        setMessages(prev => {
          if (prev.some(m => m.id === payload.id)) return prev;
          return [...prev, {
            id: payload.id,
            role: payload.sender === 'Anonymous' || payload.sender === 'websocket_user' ? 'user' : 'user', // Simplified
            content: payload.content,
            timestamp: payload.timestamp ? new Date(payload.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString(),
            agent: undefined
          }];
        });
      }
      else if (msg.type === 'agent_response') {
        const payload = msg.response as any;
        setIsTyping(false);
        setMessages(prev => {
          // If we already have a streaming message with same ID or a placeholder, update it. For now just append.
          return [...prev, {
            id: msg.original_message_id || Date.now().toString(),
            role: 'assistant',
            content: payload.content,
            timestamp: msg.timestamp ? new Date(msg.timestamp as string).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString(),
            agent: payload.orchestrator || 'Agent'
          }];
        });
        setApiConversations(prev => prev.map(c => c.id === selectedConversation?.id ? { ...c, lastMessage: payload.content } : c));
      }
      else if (msg.type === 'stream_start') {
        setIsTyping(true);
        setThinkingStatus(
          typeof msg.message === 'string' ? msg.message : 'Generating response...'
        );
        setMessages(prev => [...prev, {
          id: 'stream-current',
          role: 'assistant',
          content: '',
          timestamp: new Date().toLocaleTimeString(),
          agent: selectedAgent?.name || 'Agent',
          isStreaming: true
        }]);
      }
      else if (msg.type === 'stream_chunk') {
        setThinkingStatus(null);
        setIsTyping(false);
        setMessages(prev => {
          const newMsgs = [...prev];
          const streamIdx = newMsgs.findIndex(m => m.id === 'stream-current' || m.isStreaming);
          if (streamIdx >= 0) {
            newMsgs[streamIdx].content = (msg.full_content as string) || newMsgs[streamIdx].content + (msg.chunk as string);
          }
          return newMsgs;
        });
      }
      else if (msg.type === 'stream_end') {
        setIsTyping(false);
        setThinkingStatus(null);
        setMessages(prev => {
          const newMsgs = [...prev];
          const streamIdx = newMsgs.findIndex(m => m.id === 'stream-current' || m.isStreaming);
          if (streamIdx >= 0) {
            newMsgs[streamIdx].isStreaming = false;
            newMsgs[streamIdx].id = Date.now().toString();
            if (msg.full_content) {
              newMsgs[streamIdx].content = msg.full_content as string;
            }
          }
          return newMsgs;
        });
      }
      else if (msg.type === 'agent_status_update' || msg.type === 'agent_thinking') {
        setIsTyping(true);
        setThinkingStatus(
          (typeof msg.status === 'string' && msg.status) ||
          (typeof msg.message === 'string' && msg.message) ||
          'Agent working...'
        );
      }
    }
  });

  const handleSend = async () => {
    if (!input.trim()) return;
    
    let activeSession = selectedConversation;
    if (!activeSession) {
      try {
        activeSession = await createSession({ name: `Chat with ${selectedAgent?.name || 'Agent'}` });
        
        // If an agent is selected, add it to the session in the backend
        if (selectedAgent && selectedAgent.id) {
          try {
            await addAgentToSession(activeSession.id, selectedAgent.id);
          } catch (e) { console.error('Failed to link agent:', e); }
        }

        activeSession = {
          ...activeSession,
          title: activeSession.name || 'New Conversation',
          agent: selectedAgent?.name || 'Orchestrator',
          agentId: selectedAgent?.id || null,
          lastMessage: 'Started',
          time: new Date().toLocaleTimeString(),
          unread: 0,
          pinned: false
        };
        setApiConversations(prev => [activeSession, ...prev]);
        setSelectedConversation(activeSession);
        
        // Small delay to allow WS to connect to new session
        await new Promise(r => setTimeout(r, 500));
      } catch (err) {
        console.error('Failed to create session:', err);
        return;
      }
    }

    const messageContent = input;
    setInput('');
    
    // Add user message optimistically
    const tempId = Date.now().toString();
    setMessages(prev => [...prev, {
      id: tempId,
      role: 'user',
      content: messageContent,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }]);
    
    setIsTyping(true);

    try {
      if (selectedAgent?.id) {
        try { await addAgentToSession(activeSession.id, selectedAgent.id); } catch { /* ignore */ }
      }
      
      // Prefer token streaming over the WebSocket when connected
      if (connectionStatus === 'connected') {
        setThinkingStatus('Connecting to agent...');
        wsSendMessage({
          type: 'stream_request',
          content: messageContent,
          message: messageContent,
          message_type: 'text',
          metadata: { agent_id: selectedAgent?.id },
          agent_id: selectedAgent?.id,
        });
      } else {
        // Fallback to HTTP POST
        const responseMsg = await sendMessage(activeSession.id, {
          content: messageContent,
          message_type: 'text',
          metadata: { agent_id: selectedAgent?.id },
        });

        const aiMessage = {
          id: responseMsg.id || (Date.now() + 1).toString(),
          role: 'assistant',
          content: responseMsg.content || responseMsg.metadata?.content || responseMsg.metadata?.response || 'Done.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          agent: selectedAgent?.name || 'Agent',
        };
        setMessages(prev => [...prev, aiMessage]);
        setApiConversations(prev => prev.map(c => c.id === activeSession.id ? { ...c, lastMessage: responseMsg.content } : c));
        setIsTyping(false);
      }
      trackEvent('message_sent', { session_id: activeSession.id });
      trackOnce('first_message_sent', { session_id: activeSession.id });
    } catch (err: unknown) {
      console.error('Failed to send message:', err);
      setIsTyping(false);
      if (isQuotaLimitError(err)) {
        const data = (err as { response?: { data?: { message?: string; usage?: { used?: number; limit?: number; tier?: string } } } }).response?.data;
        dispatchQuotaLimit({
          message: data?.message || axiosErrorDetail(err) || 'Monthly message limit reached. Upgrade to continue.',
          used: data?.usage?.used,
          limit: data?.usage?.limit,
          tier: data?.usage?.tier,
        });
      }
      const detail = axiosErrorDetail(err) || getErrorMessage(err);
      const assistantError = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: isQuotaLimitError(err)
          ? `${detail || 'Monthly message limit reached.'} Open Billing to upgrade your plan.`
          : detail
            ? `Sorry, I encountered an error: ${typeof detail === 'string' ? detail : JSON.stringify(detail)}`
            : 'Sorry, I encountered an error processing your request. The request may have timed out — try again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        agent: 'System',
      };
      setMessages(prev => [...prev, assistantError]);
    }
  };

  const copyToClipboard = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <AppLayout>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="h-[calc(100vh-8rem)] flex gap-6"
      >
        {/* Sidebar - Conversations */}
        <Card className="w-80 shrink-0 flex flex-col">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Chats
              </CardTitle>
              <Button size="icon" variant="ghost" onClick={() => {
                setSelectedConversation(null);
                setMessages([]);
              }}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <div className="relative mt-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search conversations..." className="pl-10" />
            </div>
          </CardHeader>
          <CardContent className="flex-1 p-0 overflow-hidden">
            <ScrollArea className="h-full">
              <div className="p-2 space-y-1">
                {apiConversations
                  .filter(conv => !selectedAgent || conv.agentId === selectedAgent.id || conv.agent === 'Orchestrator')
                  .map((conv) => (
                  <motion.button
                    key={conv.id}
                    onClick={() => setSelectedConversation(conv)}
                    className={cn(
                      "w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors",
                      selectedConversation?.id === conv.id
                        ? "bg-primary/10 border border-primary/20"
                        : "hover:bg-muted/50"
                    )}
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                  >
                    <Avatar className="h-10 w-10">
                      <AvatarFallback className="text-lg">
                        {apiAgents.find(a => a.name === conv.agent)?.avatar || '🤖'}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-medium truncate flex items-center gap-1">
                          {conv.pinned && <Pin className="h-3 w-3 text-primary" />}
                          {conv.title}
                        </span>
                        <span className="text-xs text-muted-foreground">{conv.time}</span>
                      </div>
                      <p className="text-sm text-muted-foreground truncate">{conv.lastMessage}</p>
                    </div>
                    {conv.unread > 0 && (
                      <Badge className="h-5 px-1.5">{conv.unread}</Badge>
                    )}
                  </motion.button>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Main Chat Area */}
        <Card className="flex-1 flex flex-col overflow-hidden">
          {/* Chat Header */}
          <CardHeader className="border-b shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Avatar className="h-10 w-10">
                  <AvatarFallback className="text-lg">{selectedAgent?.avatar || 'A'}</AvatarFallback>
                </Avatar>
                <div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    {selectedAgent?.name || 'Loading...'}
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-xs",
                        selectedAgent?.status === 'online' && "text-green-500 border-green-500/30",
                        selectedAgent?.status === 'busy' && "text-yellow-500 border-yellow-500/30",
                        selectedAgent?.status === 'offline' && "text-muted-foreground"
                      )}
                    >
                      {selectedAgent?.status || 'offline'}
                    </Badge>
                  </CardTitle>
                  <CardDescription>{selectedAgent?.type || 'Unknown'} agent</CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Select
                  value={selectedAgent?.id || ''}
                  onValueChange={(id) => {
                    const agent = apiAgents.find(a => a.id === id);
                    if (agent) {
                      setSelectedAgent(agent);
                      setSelectedConversation(null);
                      setMessages([]);
                    }
                  }}
                >
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Switch agent" />
                  </SelectTrigger>
                  <SelectContent>
                    {apiAgents.map(agent => (
                      <SelectItem key={agent.id} value={agent.id}>
                        <div className="flex items-center gap-2">
                          <span>{agent.avatar || '🤖'}</span>
                          <span>{agent.name}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>
                      <Star className="h-4 w-4 mr-2" />
                      Star conversation
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Archive className="h-4 w-4 mr-2" />
                      Archive
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Download className="h-4 w-4 mr-2" />
                      Export chat
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem className="text-destructive">
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete conversation
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </CardHeader>

          {/* Messages */}
          <CardContent className="flex-1 overflow-hidden p-0">
            <ScrollArea className="h-full p-4">
              <div className="space-y-6">
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-16 text-center px-6">
                    <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted mb-4">
                      <MessageSquare className="h-8 w-8 text-muted-foreground" />
                    </div>
                    {apiAgents.length === 0 ? (
                      <>
                        <h3 className="text-lg font-semibold mb-2">Create an agent first</h3>
                        <p className="text-muted-foreground mb-4 max-w-sm">
                          Chat needs at least one agent. Create one, then come back and send your first message.
                        </p>
                        <Button asChild>
                          <Link href="/agents">Go to Agents</Link>
                        </Button>
                      </>
                    ) : (
                      <>
                        <h3 className="text-lg font-semibold mb-2">Send your first message</h3>
                        <p className="text-muted-foreground mb-2 max-w-sm">
                          Ask {selectedAgent?.name || 'your agent'} something concrete — for example:
                        </p>
                        <p className="text-sm text-muted-foreground italic mb-4">
                          &ldquo;Summarize what you can help me with in this workspace.&rdquo;
                        </p>
                      </>
                    )}
                  </div>
                )}
                <AnimatePresence>
                  {messages.map((message, index) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className={cn(
                        "flex gap-3",
                        message.role === 'user' && "flex-row-reverse"
                      )}
                    >
                      <Avatar className="h-8 w-8 shrink-0">
                        {message.role === 'assistant' ? (
                          <AvatarFallback className="text-sm bg-primary/10">
                            {selectedAgent.avatar}
                          </AvatarFallback>
                        ) : (
                          <AvatarFallback className="bg-muted">
                            <User className="h-4 w-4" />
                          </AvatarFallback>
                        )}
                      </Avatar>
                      <div className={cn(
                        "group max-w-[70%] space-y-1",
                        message.role === 'user' && "items-end"
                      )}>
                        <div className={cn(
                          "rounded-2xl px-4 py-2.5",
                          message.role === 'assistant'
                            ? "bg-muted"
                            : "bg-gradient-to-br from-indigo-600 to-purple-600 text-white"
                        )}>
                          {message.role === 'assistant' ? (
                            <div className="prose prose-sm dark:prose-invert max-w-none">
                              <ReactMarkdown 
                                remarkPlugins={[remarkGfm]}
                                components={{
                                  code: ({ className, children, ...rest }) => {
                                    const match = /language-(\w+)/.exec(className || '');
                                    const isInline = !match && !String(children).includes('\n');
                                    return !isInline && match ? (
                                      <SyntaxHighlighter
                                        // @ts-expect-error prism theme export type mismatch
                                        style={oneDark}
                                        language={match[1]}
                                        PreTag="div"
                                        className="rounded-md text-sm"
                                        {...rest}
                                      >
                                        {String(children).replace(/\n$/, '')}
                                      </SyntaxHighlighter>
                                    ) : (
                                      <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono" {...rest}>
                                        {children}
                                      </code>
                                    );
                                  },
                                  h1: ({ children }) => <h1 className="text-lg font-bold mb-2 mt-4 first:mt-0">{children}</h1>,
                                  h2: ({ children }) => <h2 className="text-base font-bold mb-2 mt-3 first:mt-0">{children}</h2>,
                                  h3: ({ children }) => <h3 className="text-sm font-bold mb-1 mt-2 first:mt-0">{children}</h3>,
                                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                  ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                                  ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                                  li: ({ children }) => <li className="ml-4">{children}</li>,
                                  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                                  em: ({ children }) => <em className="italic">{children}</em>,
                                  blockquote: ({ children }) => <blockquote className="border-l-4 border-muted-foreground/30 pl-4 italic my-2">{children}</blockquote>
                                }}
                              >
                                {message.content}
                              </ReactMarkdown>
                            </div>
                          ) : (
                            <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
                          )}
                        </div>
                        <div className={cn(
                          "flex items-center gap-2 px-2 opacity-0 group-hover:opacity-100 transition-opacity",
                          message.role === 'user' && "flex-row-reverse"
                        )}>
                          <span className="text-xs text-muted-foreground">{message.timestamp}</span>
                          {message.role === 'assistant' && (
                            <>
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      className="h-6 w-6"
                                      onClick={() => copyToClipboard(message.id, message.content)}
                                    >
                                      {copied === message.id ? (
                                        <Check className="h-3 w-3 text-green-500" />
                                      ) : (
                                        <Copy className="h-3 w-3" />
                                      )}
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent>Copy</TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                              <Button variant="ghost" size="icon" className="h-6 w-6">
                                <ThumbsUp className="h-3 w-3" />
                              </Button>
                              <Button variant="ghost" size="icon" className="h-6 w-6">
                                <ThumbsDown className="h-3 w-3" />
                              </Button>
                              <Button variant="ghost" size="icon" className="h-6 w-6">
                                <RefreshCw className="h-3 w-3" />
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>

                {isTyping && <AgentThinkingIndicator status={thinkingStatus} />}

                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
          </CardContent>

          {/* Input Area */}
          <div className="border-t p-4 shrink-0">
            <div className="flex items-end gap-3">
              <div className="flex-1 relative">
                <Textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type your message..."
                  className="min-h-[60px] max-h-[200px] resize-none pr-12"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                />
                <div className="absolute right-2 bottom-2 flex items-center gap-1">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <Paperclip className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Attach file</TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
              </div>
              <Button onClick={handleSend} size="lg" className="h-[60px] gap-2">
                <Send className="h-5 w-5" />
                Send
              </Button>
            </div>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="outline" className="text-xs gap-1">
                <Sparkles className="h-3 w-3" />
                GPT-4 Turbo
              </Badge>
              <Badge variant="outline" className="text-xs gap-1">
                <Zap className="h-3 w-3" />
                Fast mode
              </Badge>
            </div>
          </div>
        </Card>
      </motion.div>
    </AppLayout>
  );
}

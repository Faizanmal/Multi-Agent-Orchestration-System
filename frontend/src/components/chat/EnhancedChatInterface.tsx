/**
 * Enhanced Chat Interface with WebSocket and HTTP API integration
 * Provides full chat functionality with message persistence and agent interaction
 */

"use client";

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { InputBar } from '@/components/input/InputBar';
import { useWebSocketContext } from '@/contexts/WebSocketContext';
import { useMessages, useSendMessage, useSessions, useDeleteSession, useCreateSession } from '@/hooks/useApi';
import type { Session } from '@/lib/api';
import { Bot, User, AlertCircle, Wifi, WifiOff, MessageSquare, Loader2, RefreshCw, Settings, Trash2 } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from '@/hooks/use-toast';
import { ApiTestComponent } from '@/components/debug/ApiTestComponent';

interface EnhancedChatInterfaceProps {
  className?: string;
  defaultSessionId?: string;
}

export function EnhancedChatInterface({ className, defaultSessionId }: EnhancedChatInterfaceProps) {
  // Use the WebSocket session ID as default, or first available session
  const { 
    messages: wsMessages, 
    sendChatMessage: wsSendMessage, 
    connectionStatus, 
    isConnected,
    sessionId: webSocketSessionId,
    setSessionId: setWsSessionId,
    clearMessages: clearWsMessages
  } = useWebSocketContext();
  
  // API hooks for HTTP fallback and persistence
  const { data: sessionsResponse } = useSessions();
  const sendMessageMutation = useSendMessage();
  const deleteSessionMutation = useDeleteSession();
  const createSessionMutation = useCreateSession();
  
  // Filter and deduplicate sessions
  const sessions = (() => {
      if (!sessionsResponse?.results) return [];
      
      // Remove duplicates based on name and keep only recent ones
      const uniqueSessions = sessionsResponse.results.reduce((acc: Session[], session: Session) => {
        const existingIndex = acc.findIndex(s => s.name === session.name);
        if (existingIndex >= 0) {
          // Keep the more recent session
          const existing = acc[existingIndex];
          if (new Date(session.created_at) > new Date(existing.created_at)) {
            acc[existingIndex] = session;
          }
        } else {
          acc.push(session);
        }
        return acc;
      }, []);
      
      console.log('📋 Filtered sessions:', uniqueSessions.length, 'from', sessionsResponse.results.length);
      return uniqueSessions;
    })();
  
  // Create a default session if none exist
  useEffect(() => {
    if (sessionsResponse && sessionsResponse.results.length === 0 && !createSessionMutation.isPending) {
      console.log('🚀 No sessions found, creating default session...');
      createSessionMutation.mutate({ name: `Chat Session ${new Date().toLocaleString()}` });
    }
  }, [sessionsResponse, createSessionMutation]);
  
  const [currentSessionId, setCurrentSessionId] = useState(() => {
    return defaultSessionId || webSocketSessionId || '';
  });
  const [isAutoScroll, setIsAutoScroll] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Update current session when sessions are loaded
  useEffect(() => {
    if (!currentSessionId && sessions.length > 0) {
      console.log('🎯 Setting current session to first available:', sessions[0].id);
      setTimeout(() => { setCurrentSessionId(sessions[0].id); }, 0)
    } else if (currentSessionId && !sessions.find(s => s.id === currentSessionId) && sessions.length > 0) {
      // If current session doesn't exist anymore, switch to first available
      console.log('🔄 Current session not found, switching to:', sessions[0].id);
      setTimeout(() => {
          setCurrentSessionId(sessions[0].id);
        }, 0)
    }
  }, [sessions, currentSessionId]);
  
  // Update messages query based on current session - only query when we have a valid session ID
  const { data: currentMessagesResponse, isLoading: isLoadingCurrentMessages, refetch: refetchCurrentMessages } = useMessages(
    currentSessionId && currentSessionId !== 'initializing...' ? currentSessionId : ''
  );
  const apiMessages = currentMessagesResponse?.results || [];

  // Sync WebSocket session with current session
  useEffect(() => {
    if (webSocketSessionId !== currentSessionId) {
      setWsSessionId(currentSessionId);
    }
  }, [currentSessionId, setWsSessionId, webSocketSessionId]);

  // Auto scroll to bottom
  const scrollToBottom = useCallback(() => {
    if (isAutoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [isAutoScroll]);

  useEffect(() => {
    scrollToBottom();
  }, [wsMessages, scrollToBottom]);

  // Combined message handling - prefer WebSocket messages for real-time, fall back to API
  const allMessages = wsMessages.length > 0 ? wsMessages : apiMessages.map(msg => ({
    id: msg.id,
    content: msg.content,
    sender: msg.sender_agent ? 'agent' : (msg.sender ? 'user' : 'system'),
    timestamp: msg.created_at,
    type: msg.sender_agent ? 'agent' as const : (msg.sender ? 'user' as const : 'system' as const),
    agentName: msg.sender_agent || undefined,
  }));

  // Debug logging for messages and sessions
  useEffect(() => {
    console.log('🔄 Sessions updated:', sessions.length);
    console.log('📨 WebSocket messages:', wsMessages.length);
    console.log('📡 API messages:', apiMessages.length);
    console.log('📋 All messages:', allMessages.length);
    console.log('🎯 Current session:', currentSessionId);
    console.log('🌐 Connection status:', connectionStatus, 'isConnected:', isConnected);
  }, [sessions.length, wsMessages.length, apiMessages.length, allMessages.length, currentSessionId, connectionStatus, isConnected]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;
    
    console.log('📤 Sending message:', content.trim());
    console.log('🎯 Current session ID:', currentSessionId);
    console.log('🌐 Connection status:', connectionStatus, 'isConnected:', isConnected);
    
    if (!currentSessionId || currentSessionId === 'initializing...') {
      toast({
        title: 'Session not ready',
        description: 'Please wait for session initialization to complete.',
        variant: 'destructive',
      });
      return;
    }

    try {
      // Send via WebSocket first (real-time) if connected
      if (isConnected) {
        console.log('� Sending via WebSocket:', content);
        wsSendMessage(content.trim());
      } else {
        // Fallback to HTTP API - this should always work
        console.log('🌐 Sending via HTTP API:', content);
        console.log('🔗 Session ID for API call:', currentSessionId);
        
        await sendMessageMutation.mutateAsync({
          sessionId: currentSessionId,
          messageData: {
            content: content.trim(),
            message_type: 'text',
            metadata: {},
          },
        });
      }
    } catch (error) {
      console.error('❌ Failed to send message:', error);
      toast({
        title: 'Error',
        description: `Failed to send message: ${error instanceof Error ? error.message : 'Unknown error'}`,
        variant: 'destructive',
      });
    }
  };

  const handleSessionChange = (newSessionId: string) => {
    setCurrentSessionId(newSessionId);
    clearWsMessages(); // Clear WebSocket messages when switching sessions
  };

  const handleRefreshMessages = () => {
    refetchCurrentMessages();
    toast({
      title: 'Messages refreshed',
      description: 'Chat history has been updated',
    });
  };

  const handleDeleteSession = async (sessionId: string) => {
    console.log('🗑️ Attempting to delete session:', sessionId);
    console.log('📋 Available sessions:', sessions.length);
    console.log('🎯 Current session:', currentSessionId);
    
    if (!sessionId || sessionId === 'initializing...') {
      toast({
        title: 'Invalid session',
        description: 'Cannot delete an invalid session.',
        variant: 'destructive',
      });
      return;
    }
    
    if (sessions.length <= 1) {
      toast({
        title: 'Cannot delete session',
        description: 'You must have at least one session.',
        variant: 'destructive',
      });
      return;
    }

    try {
      console.log('🚀 Calling delete mutation for session:', sessionId);
      await deleteSessionMutation.mutateAsync(sessionId);
      
      // If deleting current session, switch to another session
      if (sessionId === currentSessionId) {
        const remainingSession = sessions.find(s => s.id !== sessionId);
        if (remainingSession) {
          console.log('🔄 Switching to remaining session:', remainingSession.id);
          setCurrentSessionId(remainingSession.id);
          clearWsMessages();
        }
      }
      
      toast({
        title: 'Session deleted',
        description: 'Chat session has been deleted successfully.',
      });
    } catch (error) {
      console.error('❌ Failed to delete session:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete session. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'user':
        return <User className="h-4 w-4" />;
      case 'agent':
        return <Bot className="h-4 w-4" />;
      case 'system':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <MessageSquare className="h-4 w-4" />;
    }
  };

  const getMessageVariant = (type: string) => {
    switch (type) {
      case 'user':
        return 'default';
      case 'agent':
        return 'secondary';
      case 'system':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return '';
    }
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'bg-green-500';
      case 'connecting':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      case 'disconnected':
        return 'bg-gray-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getConnectionStatusVariant = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'default';
      case 'connecting':
        return 'secondary';
      case 'error':
        return 'destructive';
      case 'disconnected':
        return 'secondary';
      default:
        return 'secondary';
    }
  };

  return (
    <>
      {/* Temporary Debug Panel - Remove after debugging */}
      {process.env.NODE_ENV === 'development' && <ApiTestComponent />}
      
      <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Agent Chat
          </CardTitle>
          
          <div className="flex items-center gap-3">
            {/* Session Selector with Delete Button */}
            {sessions.length > 0 ? (
              <div className="flex items-center gap-2">
                <Select value={currentSessionId} onValueChange={handleSessionChange}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Select session" />
                  </SelectTrigger>
                  <SelectContent>
                    {sessions.map((session) => (
                      <SelectItem key={session.id} value={session.id}>
                        {session.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                {/* Delete Session Button */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    console.log('🖱️ Delete button clicked for session:', currentSessionId);
                    if (currentSessionId && currentSessionId !== 'initializing...') {
                      handleDeleteSession(currentSessionId);
                    }
                  }}
                  disabled={
                    !currentSessionId || 
                    currentSessionId === 'initializing...' || 
                    sessions.length <= 1 || 
                    deleteSessionMutation.isPending
                  }
                  title={
                    sessions.length <= 1 
                      ? 'Cannot delete the only session' 
                      : !currentSessionId || currentSessionId === 'initializing...'
                      ? 'Session not ready'
                      : 'Delete current session'
                  }
                  className="text-red-600 hover:text-red-700 hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {deleteSessionMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </Button>
              </div>
            ) : createSessionMutation.isPending ? (
              <Badge variant="outline" className="flex items-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" />
                Creating session...
              </Badge>
            ) : (
              <div className="flex items-center gap-2">
                <Badge variant="destructive">No sessions available</Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    console.log('🚀 Manually creating session...');
                    createSessionMutation.mutate({ name: `Chat Session ${new Date().toLocaleString()}` });
                  }}
                  disabled={createSessionMutation.isPending}
                >
                  Create Session
                </Button>
              </div>
            )}

            {/* Refresh Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefreshMessages}
              disabled={isLoadingCurrentMessages}
            >
              <RefreshCw className={`h-4 w-4 ${isLoadingCurrentMessages ? 'animate-spin' : ''}`} />
            </Button>

            {/* Connection Status */}
            <div className="flex items-center gap-2">
              <Badge 
                variant={getConnectionStatusVariant()}
                className="flex items-center space-x-1"
              >
                <div className={`w-2 h-2 rounded-full ${getConnectionStatusColor()}`} />
                {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                <span className="text-xs capitalize">{connectionStatus}</span>
              </Badge>
              {connectionStatus !== 'connected' && (
                <Badge variant="outline" className="text-xs text-yellow-600">
                  HTTP Mode
                </Badge>  
              )}
            </div>

            {/* Auto-scroll toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsAutoScroll(!isAutoScroll)}
              className={isAutoScroll ? 'bg-primary/10' : ''}
            >
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="p-0">
        <div className="h-96 flex flex-col">
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4">
              {isLoadingCurrentMessages && allMessages.length === 0 ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin mr-2" />
                  <span className="text-muted-foreground">Loading messages...</span>
                </div>
              ) : allMessages.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  <Bot className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>Start a conversation with the multi-agent system</p>
                  <p className="text-sm mt-1">Your messages will be processed by specialized AI agents</p>
                </div>
              ) : (
                <>
                  {allMessages.map((message, index) => (
                    <div key={`${message.id}-${index}`} className="flex items-start space-x-3">
                      <div className="flex-shrink-0 mt-1">
                        {getMessageIcon(message.type)}
                      </div>
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center space-x-2">
                          <Badge variant={getMessageVariant(message.type)} className="text-xs">
                            {message.agentName || message.sender}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {formatTimestamp(message.timestamp)}
                          </span>
                          {message.type === 'agent' && message.agentName && (
                            <Badge variant="outline" className="text-xs">
                              AI
                            </Badge>
                          )}
                        </div>
                        <div className="text-sm bg-muted/50 rounded-lg p-3">
                          <p className="whitespace-pre-wrap">{message.content}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {/* Sending indicator */}
                  {(sendMessageMutation.isPending || (!isConnected && allMessages.length === 0)) && (
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 mt-1">
                        <Loader2 className="h-4 w-4 animate-spin" />
                      </div>
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className="text-xs">
                            System
                          </Badge>
                        </div>
                        <div className="text-sm bg-muted/50 rounded-lg p-3">
                          <p className="text-muted-foreground">
                            {sendMessageMutation.isPending 
                              ? 'Sending message...' 
                              : 'Connecting to agents...'}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
          
          <div className="border-t p-4">
            <InputBar
              onSend={handleSendMessage}
              isLoading={sendMessageMutation.isPending}
              placeholder={
                connectionStatus === 'connected'
                  ? "Type your message to the agents..."
                  : connectionStatus === 'connecting'
                  ? "Connecting to agents..."
                  : currentSessionId === 'initializing...'
                  ? "Initializing session..."
                  : "Type your message (HTTP mode)..."
              }
            />
            
            {/* Status info */}
            <div className="flex items-center justify-between text-xs text-muted-foreground mt-2">
              <span>
                {allMessages.length} message{allMessages.length !== 1 ? 's' : ''} in this session
              </span>
              <div className="flex items-center gap-2">
                <span>
                  Session: {currentSessionId || 'Not selected'}
                </span>
                {(!currentSessionId || currentSessionId === 'initializing...') && (
                  <Badge variant="outline" className="text-xs text-yellow-600">
                    Initializing
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
    </>
  );
}
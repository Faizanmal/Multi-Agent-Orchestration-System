"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAgent } from './AgentContext';
import { getSessions, createSession } from '@/lib/api';
import type { Session } from '@/lib/api';

interface WebSocketMessage {
  type: string;
  [key: string]: unknown;
}

interface ChatMessageWebSocket {
  type: 'chat_message';
  message: {
    id: string;
    content: string;
    sender: string;
    timestamp: string;
    message_type: string;
  };
}

interface AgentResponseWebSocket {
  type: 'agent_response';
  response: {
    content: string;
    orchestrator?: string;
    agent_id?: string;
    error?: boolean;
    [key: string]: unknown;
  };
  original_message_id?: string;
  timestamp?: string;
}

interface ConnectionEstablishedWebSocket {
  type: 'connection_established';
  session_id: string;
  message: string;
}

interface StreamStartWebSocket {
  type: 'stream_start';
  message: string;
}

interface StreamChunkWebSocket {
  type: 'stream_chunk';
  chunk: string;
}

interface StreamEndWebSocket {
  type: 'stream_end';
}

interface ErrorWebSocket {
  type: 'error';
  message: string;
}

interface TaskCompletedWebSocket {
  type: 'task_completed';
  result?: string;
  [key: string]: unknown;
}

interface PingWebSocket {
  type: 'ping';
}

interface PongWebSocket {
  type: 'pong';
}

type WebSocketMessageType = 
  | ChatMessageWebSocket
  | AgentResponseWebSocket
  | ConnectionEstablishedWebSocket
  | StreamStartWebSocket
  | StreamChunkWebSocket
  | StreamEndWebSocket
  | ErrorWebSocket
  | TaskCompletedWebSocket
  | PingWebSocket
  | PongWebSocket
  | WebSocketMessage;

interface ChatMessage {
  id: string;
  content: string;
  sender: string;
  timestamp: string;
  type: 'user' | 'agent' | 'system';
  agentName?: string;
}

interface WebSocketContextType {
  isConnected: boolean;
  sendChatMessage: (content: string, userId?: string) => void;
  messages: ChatMessage[];
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  sessionId: string;
  setSessionId: (sessionId: string) => void;
  clearMessages: () => void;
  sendPing: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: React.ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  // Initialize with a default session ID, will be replaced with actual session
  const [sessionId, setSessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('currentSessionId');
      return stored || 'initializing...';
    }
    return 'initializing...';
  });
  
  // Initialize session with backend API
  useEffect(() => {
    const initializeSession = async () => {
      try {
        console.log('🚀 Initializing session...');
        
        // First, try to get existing sessions
        const sessionsResponse = await getSessions();
        console.log('📋 Found sessions:', sessionsResponse.results);
        
        // Look for existing default session
        let targetSession = sessionsResponse.results.find((s: Session) => 
          s.name === 'default-session' || s.name.includes('default')
        );
        
        if (!targetSession && sessionsResponse.results.length > 0) {
          // Use the first available session
          targetSession = sessionsResponse.results[0];
          console.log('✅ Using first available session:', targetSession);
        } else if (!targetSession) {
          // Only create if no sessions exist at all
          console.log('📝 Creating new default session...');
          targetSession = await createSession({ name: `default-session-${Date.now()}` });
          console.log('✅ Session created:', targetSession);
        } else {
          console.log('✅ Using existing default session:', targetSession);
        }
        
        setSessionId(targetSession.id);
        localStorage.setItem('currentSessionId', targetSession.id);
        console.log('🎯 Session ID set to:', targetSession.id);
        
      } catch (error) {
        console.error('❌ Failed to initialize session:', error);
        // Fallback: generate a UUID (this won't work for API calls but prevents crashes)
        const fallbackId = crypto.randomUUID();
        setSessionId(fallbackId);
        localStorage.setItem('currentSessionId', fallbackId);
      }
    };
    
    if (sessionId === 'initializing...') {
      initializeSession();
    }
  }, [sessionId]);
  
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    // Load messages from localStorage on initial render
    if (typeof window !== 'undefined') {
      const savedMessages = localStorage.getItem('chatMessages');
      if (savedMessages) {
        try {
          return JSON.parse(savedMessages);
        } catch (e) {
          console.error('Failed to parse saved messages', e);
        }
      }
    }
    return [];
  });
  const { addMessage } = useAgent();

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('chatMessages', JSON.stringify(messages));
      localStorage.setItem('currentSessionId', sessionId);
    }
  }, [messages, sessionId]);

  // WebSocket URL construction - using the correct path for session-based WebSocket
  // Only create WebSocket URL if session is properly initialized
  const wsUrl = sessionId !== 'initializing...' ? 
    `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/session/${sessionId}/` : 
    '';
    
  // Debug WebSocket URL construction
  useEffect(() => {
    if (wsUrl && sessionId !== 'initializing...') {
      console.log('🔗 WebSocket URL constructed:', wsUrl);
      console.log('🆔 Session ID type:', typeof sessionId, 'value:', sessionId);
      console.log('📏 Session ID length:', sessionId.length);
      console.log('✅ UUID format check:', /^[0-9a-f-]{36}$/.test(sessionId));
    }
  }, [wsUrl, sessionId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const handleMessage = useCallback((message: WebSocketMessageType) => {
    console.log('Received WebSocket message:', message);

    switch (message.type) {
      case 'connection_established':
        console.log('Connection established for session:', (message as ConnectionEstablishedWebSocket).session_id);
        break;

      case 'chat_message':
        const chatMessage = message as ChatMessageWebSocket;
        const chatMsg: ChatMessage = {
          id: chatMessage.message.id,
          content: chatMessage.message.content,
          sender: chatMessage.message.sender,
          timestamp: chatMessage.message.timestamp,
          type: chatMessage.message.sender === 'Anonymous' || chatMessage.message.sender === 'user' ? 'user' : 'agent'
        };
        setMessages(prev => [...prev, chatMsg]);
        
        // Also add to agent context
        addMessage({
          content: chatMsg.content,
          sender: chatMsg.sender,
          type: 'text'
        });
        break;

      case 'agent_response':
        const agentMessage = message as AgentResponseWebSocket;
        const agentMsg: ChatMessage = {
          id: `agent-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          content: agentMessage.response.content || JSON.stringify(agentMessage.response),
          sender: 'agent',
          timestamp: agentMessage.timestamp || new Date().toISOString(),
          type: 'agent',
          agentName: agentMessage.response.orchestrator || 'AI Assistant'
        };
        setMessages(prev => [...prev, agentMsg]);
        
        // Also add to agent context
        addMessage({
          content: agentMsg.content,
          sender: agentMsg.agentName || 'AI Assistant',
          type: 'text'
        });
        break;

      case 'stream_start':
        console.log('Stream started:', (message as StreamStartWebSocket).message);
        // Add system message for stream start
        const streamStartMsg: ChatMessage = {
          id: `stream-start-${Date.now()}`,
          content: 'Agent is processing your request...',
          sender: 'system',
          timestamp: new Date().toISOString(),
          type: 'system'
        };
        setMessages(prev => [...prev, streamStartMsg]);
        break;

      case 'stream_chunk':
        console.log('Stream chunk:', (message as StreamChunkWebSocket).chunk);
        // Handle streaming response
        break;

      case 'stream_end':
        console.log('Stream ended');
        // Add system message for stream end
        const streamEndMsg: ChatMessage = {
          id: `stream-end-${Date.now()}`,
          content: 'Processing complete',
          sender: 'system',
          timestamp: new Date().toISOString(),
          type: 'system'
        };
        setMessages(prev => [...prev, streamEndMsg]);
        break;

      case 'error':
        const errorMessage = message as ErrorWebSocket;
        console.error('WebSocket error:', errorMessage.message);
        const errorMsg: ChatMessage = {
          id: `error-${Date.now()}`,
          content: `Error: ${errorMessage.message}`,
          sender: 'system',
          timestamp: new Date().toISOString(),
          type: 'system'
        };
        setMessages(prev => [...prev, errorMsg]);
        break;

      case 'task_completed':
        const taskMessage = message as TaskCompletedWebSocket;
        console.log('Task completed:', taskMessage);
        const taskMsg: ChatMessage = {
          id: `task-${Date.now()}`,
          content: `Task completed: ${taskMessage.result || 'Task finished successfully'}`,
          sender: 'system',
          timestamp: new Date().toISOString(),
          type: 'system'
        };
        setMessages(prev => [...prev, taskMsg]);
        break;

      case 'session_deleted':
        const sessionDeletedMessage = message as WebSocketMessage & { session_id: string };
        const deletedSessionId = sessionDeletedMessage.session_id;
        if (sessionId === deletedSessionId) {
          // If the deleted session is the current one, switch to a new one
          // This logic can be improved to select a specific session
          setSessionId('initializing...');
        }
        break;

      case 'ping':
        // Ping messages are handled by the WebSocket hook
        break;

      case 'pong':
        // Pong messages are handled by the WebSocket hook
        console.log('Pong received - connection is alive');
        break;

      default:
        console.log('Unhandled message type:', message.type);
        // Handle unknown message types as system messages
        const unknownMsg: ChatMessage = {
          id: `unknown-${Date.now()}`,
          content: `Received unknown message type: ${message.type}`,
          sender: 'system',
          timestamp: new Date().toISOString(),
          type: 'system'
        };
        setMessages(prev => [...prev, unknownMsg]);
    }
  }, [addMessage, sessionId]);

  const { sendMessage, connectionStatus } = useWebSocket({
    url: wsUrl, // Will be empty string during initialization
    onMessage: handleMessage,
    onConnect: () => {
      console.log('✅ WebSocket connected to session:', sessionId);
      console.log('🔗 WebSocket URL was:', wsUrl);
    },
    onDisconnect: () => {
      console.log('❌ WebSocket disconnected from session:', sessionId);
      console.log('🔗 WebSocket URL was:', wsUrl);
    },
    onError: () => {
      // Error handling without using the error parameter
    },
  });

  const sendChatMessage = useCallback((content: string, userId?: string) => {
    const message = {
      type: 'chat_message',
      content,
      user_id: userId || '1', // Default user ID
      message_type: 'text',
      metadata: {}
    };
    
    console.log('📤 Attempting to send message:', content);
    console.log('🔌 WebSocket connected:', connectionStatus === 'connected');
    console.log('🆔 Session ID:', sessionId);
    
    if (connectionStatus === 'connected' && sendMessage) {
      console.log('📡 Sending via WebSocket');
      sendMessage(message);
    } else {
      console.warn('❌ WebSocket not connected, adding system message');
      
      // Add a system message to show the issue
      const systemMessage: ChatMessage = {
        id: `system-${Date.now()}`,
        content: `Message "${content}" could not be sent via WebSocket (status: ${connectionStatus}). Use Enhanced Chat for HTTP fallback.`,
        sender: 'system',
        timestamp: new Date().toISOString(),
        type: 'system'
      };
      setMessages(prev => [...prev, systemMessage]);
    }
  }, [sendMessage, connectionStatus, sessionId]);

  const sendPing = useCallback(() => {
    const pingMessage = {
      type: 'ping'
    };
    sendMessage(pingMessage);
  }, [sendMessage]);

  // Add a system message when connection is established
  useEffect(() => {
    if (connectionStatus === 'connected') {
      const systemMsg: ChatMessage = {
        id: `system-${Date.now()}`,
        content: 'Connected to multi-agent system',
        sender: 'system',
        timestamp: new Date().toISOString(),
        type: 'system'
      };
      setTimeout(() => { setMessages(prev => [...prev, systemMsg]); }, 0)
    }
  }, [connectionStatus]);

  const contextValue: WebSocketContextType = {
    isConnected: connectionStatus === 'connected',
    sendChatMessage,
    messages,
    connectionStatus,
    sessionId,
    setSessionId,
    clearMessages,
    sendPing
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}
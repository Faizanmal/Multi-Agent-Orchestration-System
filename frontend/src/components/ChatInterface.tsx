'use client';

import { useState, useEffect, useRef } from 'react';
import { useMultiModel } from '@/hooks/useMultiModel';
import { useWebSocket } from '@/hooks/useWebSocket';
import { FeedbackWidget } from './FeedbackWidget';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Send, Loader2, User, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { toast } from 'sonner';

interface WsMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  provider?: string;
  model?: string;
  timestamp: Date;
}

interface ChatInterfaceProps {
  sessionId: string;
  agentId?: string;
}

export function ChatInterface({ sessionId, agentId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<WsMessage[]>([]);
  const [input, setInput] = useState('');
  const { chat, loading } = useMultiModel();
  const { connectionStatus, lastMessage } = useWebSocket({
    url: `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/session/${sessionId}/`,
  });
  const isConnected = connectionStatus === 'connected';
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      const wsMessage = lastMessage as unknown as WsMessage;
      setTimeout(() => { setMessages((prev) => [
                ...prev,
                {
                  id: wsMessage.id,
                  role: 'assistant',
                  content: wsMessage.content,
                  timestamp: new Date(wsMessage.timestamp),
                },
              ]); }, 0)
    }
  }, [lastMessage]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: WsMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    try {
      const response = await chat(
        [
          ...messages.map((m) => ({ role: m.role, content: m.content })),
          { role: 'user', content: input },
        ],
        agentId ? { model_preference: agentId } : undefined
      );

      if (response) {
        setMessages((prev) => [
          ...prev,
          {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: response.response,
            provider: response.provider,
            model: response.model_used,
            timestamp: new Date(),
          },
        ]);
      }
    } catch (error) {
      toast.error('Failed to send message');
      console.error('Chat error:', error);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Connection Status */}
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="text-lg font-semibold">AI Chat</h2>
        <Badge variant={isConnected ? 'default' : 'secondary'}>
          {isConnected ? 'Connected' : 'Connecting...'}
        </Badge>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <Card key={message.id} className={message.role === 'user' ? 'ml-12' : 'mr-12'}>
            <CardContent className="p-4">
              <div className="flex items-start space-x-3">
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.role === 'user' ? 'bg-blue-500' : 'bg-purple-500'
                  }`}
                >
                  {message.role === 'user' ? (
                    <User className="h-4 w-4 text-white" />
                  ) : (
                    <Bot className="h-4 w-4 text-white" />
                  )}
                </div>
                <div className="flex-1 space-y-2">
                  <div className="prose max-w-none prose-sm dark:prose-invert">
                    {message.role === 'assistant' ? (
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          code: ({ className, children, ...props }) => {
                            const match = /language-(\w+)/.exec(className || '');
                            const isInline = !match && !String(children).includes('\n');
                            return !isInline && match ? (
                              <SyntaxHighlighter
                                // @ts-expect-error prism theme export type mismatch
                                style={oneDark}
                                language={match[1]}
                                PreTag="div"
                                className="rounded-md text-sm"
                                {...props}
                              >
                                {String(children).replace(/\n$/, '')}
                              </SyntaxHighlighter>
                            ) : (
                              <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono" {...props}>
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
                    ) : (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    )}
                  </div>
                  
                  {/* Model Badge */}
                  {message.provider && (
                    <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                      <Badge variant="outline" className="text-xs">
                        {message.provider}
                      </Badge>
                      {message.model && (
                        <span>{message.model}</span>
                      )}
                    </div>
                  )}

                  {/* Feedback Widget for assistant messages */}
                  {message.role === 'assistant' && (
                    <FeedbackWidget
                      messageId={message.id}
                      agentId={agentId}
                      sessionId={sessionId}
                    />
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex space-x-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Type your message... (Shift+Enter for new line)"
            rows={3}
            className="flex-1"
          />
          <Button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            size="icon"
            className="h-auto"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

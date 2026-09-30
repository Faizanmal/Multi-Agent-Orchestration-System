"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { useWebSocketContext } from '@/contexts/WebSocketContext';
import { Download, Trash2, MessageSquare } from 'lucide-react';

interface ChatMessage {
  id: string;
  content: string;
  sender: string;
  timestamp: string;
  type: 'user' | 'agent' | 'system';
  agentName?: string;
}

interface ChatStorageProps {
  className?: string;
}

export function ChatStorage({ className }: ChatStorageProps) {
  const { messages } = useWebSocketContext();
  const [storedChats, setStoredChats] = useState<ChatMessage[][]>([]);
  const [currentChatName, setCurrentChatName] = useState('');

  // Load stored chats from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('groq_inference_chats');
    if (saved) {
      try {
        setTimeout(() => { setStoredChats(JSON.parse(saved)); }, 0)
      } catch (error) {
        console.error('Error loading stored chats:', error);
      }
    }
  }, []);

  // Save current chat
  const saveCurrentChat = () => {
    if (messages.length === 0) {
      return;
    }

    const newChat = [...messages];
    const updatedChats = [...storedChats, newChat];
    
    setStoredChats(updatedChats);
    localStorage.setItem('groq_inference_chats', JSON.stringify(updatedChats));
    setCurrentChatName('');
    
    console.log('Chat saved successfully');
  };

  // Export chat as JSON
  const exportChat = (chatIndex?: number) => {
    const chatToExport = chatIndex !== undefined ? storedChats[chatIndex] : messages;
    const dataStr = JSON.stringify(chatToExport, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `chat-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  // Export chat as text
  const exportChatAsText = (chatIndex?: number) => {
    const chatToExport = chatIndex !== undefined ? storedChats[chatIndex] : messages;
    const textData = chatToExport.map(msg => 
      `[${new Date(msg.timestamp).toLocaleString()}] ${msg.sender}: ${msg.content}`
    ).join('\n\n');
    
    const dataUri = 'data:text/plain;charset=utf-8,'+ encodeURIComponent(textData);
    const exportFileDefaultName = `chat-${new Date().toISOString().split('T')[0]}.txt`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  // Delete stored chat
  const deleteChat = (chatIndex: number) => {
    const updatedChats = storedChats.filter((_, index) => index !== chatIndex);
    setStoredChats(updatedChats);
    localStorage.setItem('groq_inference_chats', JSON.stringify(updatedChats));
  };

  // Clear all chats
  const clearAllChats = () => {
    if (confirm('Are you sure you want to delete all stored chats?')) {
      setStoredChats([]);
      localStorage.removeItem('groq_inference_chats');
    }
  };

  const formatChatPreview = (chat: ChatMessage[]) => {
    const firstUserMessage = chat.find(msg => msg.type === 'user');
    return firstUserMessage ? firstUserMessage.content.substring(0, 50) + '...' : 'Empty chat';
  };

  const getChatTimestamp = (chat: ChatMessage[]) => {
    if (chat.length === 0) return '';
    return new Date(chat[0].timestamp).toLocaleDateString();
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">Chat Storage</CardTitle>
          <Badge variant="outline">
            {storedChats.length} saved chats
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Save current chat */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <input
                type="text"
                placeholder="Chat name (optional)"
                value={currentChatName}
                onChange={(e) => setCurrentChatName(e.target.value)}
                className="flex-1 px-3 py-2 border rounded-md text-sm"
              />
              <Button
                onClick={saveCurrentChat}
                disabled={messages.length === 0}
                size="sm"
              >
                Save
              </Button>
            </div>
            <div className="flex space-x-2">
              <Button
                onClick={() => exportChat()}
                disabled={messages.length === 0}
                variant="outline"
                size="sm"
              >
                <Download className="h-3 w-3 mr-1" />
                Export JSON
              </Button>
              <Button
                onClick={() => exportChatAsText()}
                disabled={messages.length === 0}
                variant="outline"
                size="sm"
              >
                <Download className="h-3 w-3 mr-1" />
                Export TXT
              </Button>
            </div>
          </div>

          {/* Stored chats */}
          <div className="border-t pt-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium">Saved Chats</h4>
              {storedChats.length > 0 && (
                <Button
                  onClick={clearAllChats}
                  variant="destructive"
                  size="sm"
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              )}
            </div>
            
            <ScrollArea className="h-48">
              {storedChats.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No saved chats</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {storedChats.map((chat, index) => (
                    <div
                      key={index}
                      className="border rounded-lg p-3 bg-muted/30"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-xs text-muted-foreground">
                          {getChatTimestamp(chat)}
                        </div>
                        <div className="flex space-x-1">
                          <Button
                            onClick={() => exportChat(index)}
                            variant="ghost"
                            size="sm"
                          >
                            <Download className="h-3 w-3" />
                          </Button>
                          <Button
                            onClick={() => deleteChat(index)}
                            variant="ghost"
                            size="sm"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                      <div className="text-sm">
                        {formatChatPreview(chat)}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {chat.length} messages
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
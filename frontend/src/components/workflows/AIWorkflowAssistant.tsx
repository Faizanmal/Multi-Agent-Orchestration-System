'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import {
  Bot,
  Lightbulb,
  Zap,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Send,
  Sparkles,
  Brain,
  Target,
  RefreshCw,
  MessageCircle,
  ThumbsUp,
  ThumbsDown,
  Loader2
} from 'lucide-react'
import apiClient from '@/lib/api'

interface AIRecommendation {
  id: string
  type: 'optimization' | 'error-fix' | 'enhancement' | 'best-practice'
  title: string
  description: string
  impact: 'high' | 'medium' | 'low'
  effort: 'low' | 'medium' | 'high'
  confidence: number
  reasoning: string
  implementation: {
    steps: string[]
    estimatedTime: string
    requiredSkills: string[]
  }
  tags: string[]
}

interface WorkflowSuggestion {
  id: string
  query: string
  generatedWorkflow: {
    name: string
    description: string
    steps: {
      type: string
      name: string
      config: Record<string, unknown>
    }[]
  }
  reasoning: string
  confidence: number
}

interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  message: string
  timestamp: number
  suggestions?: string[]
  attachments?: {
    type: 'workflow' | 'recommendation' | 'code'
    data: unknown
  }[]
}

function mapInsightToRecommendation(raw: Record<string, unknown>, index: number): AIRecommendation {
  const typeRaw = String(raw.type || raw.category || 'optimization')
  let type: AIRecommendation['type'] = 'optimization'
  if (typeRaw.includes('error') || typeRaw.includes('fix') || typeRaw === 'warning') {
    type = 'error-fix'
  } else if (typeRaw.includes('enhance') || typeRaw === 'positive') {
    type = 'enhancement'
  } else if (typeRaw.includes('best') || typeRaw.includes('practice')) {
    type = 'best-practice'
  }

  const priority = String(raw.priority || raw.impact || raw.estimated_impact || 'medium').toLowerCase()
  const impact: AIRecommendation['impact'] =
    priority === 'high' || priority === 'critical' ? 'high' :
    priority === 'low' ? 'low' : 'medium'

  const actions = Array.isArray(raw.actions)
    ? (raw.actions as string[])
    : Array.isArray(raw.steps)
      ? (raw.steps as string[])
      : []

  return {
    id: String(raw.id || `rec-${index}`),
    type,
    title: String(raw.title || 'Insight'),
    description: String(raw.description || ''),
    impact,
    effort: (['low', 'medium', 'high'].includes(String(raw.effort))
      ? String(raw.effort) as AIRecommendation['effort']
      : 'medium'),
    confidence: typeof raw.confidence === 'number' ? raw.confidence : 0.75,
    reasoning: String(raw.reasoning || raw.description || ''),
    implementation: {
      steps: actions.length > 0 ? actions : ['Review this insight in your analytics dashboard'],
      estimatedTime: String(raw.estimated_time || '—'),
      requiredSkills: Array.isArray(raw.required_skills) ? (raw.required_skills as string[]) : [],
    },
    tags: Array.isArray(raw.tags)
      ? (raw.tags as string[])
      : [String(raw.category || type)].filter(Boolean),
  }
}

function extractGroqContent(response: Record<string, unknown>): string {
  if (typeof response.content === 'string' && response.content.trim()) {
    return response.content
  }
  if (typeof response.message === 'string' && response.message.trim()) {
    return response.message
  }
  const choices = response.choices
  if (Array.isArray(choices) && choices[0] && typeof choices[0] === 'object') {
    const choice = choices[0] as Record<string, unknown>
    const msg = choice.message as Record<string, unknown> | undefined
    if (msg && typeof msg.content === 'string') return msg.content
    if (typeof choice.text === 'string') return choice.text
  }
  if (response.data && typeof response.data === 'object') {
    return extractGroqContent(response.data as Record<string, unknown>)
  }
  return 'Sorry, I could not generate a response. Please try again.'
}

interface AIWorkflowAssistantProps {
  currentWorkflow?: {
    nodes: unknown[]
    edges: unknown[]
    metadata: Record<string, unknown>
  }
  onApplyRecommendation?: (recommendation: AIRecommendation) => void
  onGenerateWorkflow?: (workflow: WorkflowSuggestion['generatedWorkflow']) => void
}

const AIWorkflowAssistant: React.FC<AIWorkflowAssistantProps> = ({
  currentWorkflow,
  onApplyRecommendation
}) => {
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([])
  const [recsLoading, setRecsLoading] = useState(true)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'assistant',
      message: 'Hello! I\'m your AI Workflow Assistant. I can help you optimize your workflows, generate new ones from natural language, and provide intelligent suggestions. What would you like to work on today?',
      timestamp: new Date().getTime() - 60000,
      suggestions: [
        'Optimize my current workflow',
        'Generate a data processing workflow',
        'Fix errors in my workflow',
        'Suggest best practices'
      ]
    }
  ])
  const [currentMessage, setCurrentMessage] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [activeTab, setActiveTab] = useState('recommendations')
  const [generatorPrompt, setGeneratorPrompt] = useState('')
  const [isGeneratingWorkflow, setIsGeneratingWorkflow] = useState(false)
  const [generatorResult, setGeneratorResult] = useState<string | null>(null)

  const loadRecommendations = useCallback(async () => {
    setRecsLoading(true)
    try {
      const data = await apiClient.getAnalyticsInsights()
      const rawList: Record<string, unknown>[] = []

      if (data && typeof data === 'object') {
        const obj = data as Record<string, unknown>
        if (Array.isArray(obj.recommendations)) {
          rawList.push(...(obj.recommendations as Record<string, unknown>[]))
        }
        if (Array.isArray(obj.insights)) {
          rawList.push(...(obj.insights as Record<string, unknown>[]))
        }
      }

      setRecommendations(rawList.map(mapInsightToRecommendation))
    } catch (err) {
      console.error('Failed to load insights', err)
      setRecommendations([])
    } finally {
      setRecsLoading(false)
    }
  }, [])

  useEffect(() => {
    setTimeout(() => { loadRecommendations() }, 0)
  }, [loadRecommendations])

  const handleSendMessage = async () => {
    if (!currentMessage.trim() || isGenerating) return

    const userText = currentMessage.trim()
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      message: userText,
      timestamp: Date.now()
    }

    setChatMessages(prev => [...prev, userMessage])
    setCurrentMessage('')
    setIsGenerating(true)

    try {
      const systemPrompt = {
        role: 'system',
        content: currentWorkflow
          ? `You are an AI Workflow Assistant. The user has a workflow with ${currentWorkflow.nodes?.length ?? 0} nodes and ${currentWorkflow.edges?.length ?? 0} edges. Help optimize, debug, and design workflows. Be concise and actionable.`
          : 'You are an AI Workflow Assistant. Help users optimize, debug, and design workflows. Be concise and actionable.'
      }

      const history = chatMessages.slice(-6).map(m => ({
        role: m.type === 'user' ? 'user' : 'assistant',
        content: m.message,
      }))

      const response = await apiClient.chatWithGroq([
        systemPrompt,
        ...history,
        { role: 'user', content: userText },
      ])

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        message: extractGroqContent(response),
        timestamp: Date.now()
      }
      setChatMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      console.error('Groq chat failed', err)
      setChatMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        message: 'I could not reach the AI service right now. Please check your connection and try again.',
        timestamp: Date.now()
      }])
    } finally {
      setIsGenerating(false)
    }
  }

  const handleGenerateWorkflow = async () => {
    if (!generatorPrompt.trim() || isGeneratingWorkflow) return
    setIsGeneratingWorkflow(true)
    setGeneratorResult(null)
    try {
      const response = await apiClient.chatWithGroq([
        {
          role: 'system',
          content: 'You are a workflow design assistant. Given a natural language description, propose a clear step-by-step workflow with named steps and brief configs. Use plain text with numbered steps.',
        },
        { role: 'user', content: generatorPrompt.trim() },
      ])
      setGeneratorResult(extractGroqContent(response))
    } catch (err) {
      console.error('Workflow generation failed', err)
      setGeneratorResult('Failed to generate workflow. Please try again.')
    } finally {
      setIsGeneratingWorkflow(false)
    }
  }

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low': return 'bg-green-100 text-green-800 border-green-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getEffortColor = (effort: string) => {
    switch (effort) {
      case 'high': return 'bg-red-100 text-red-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'optimization': return <TrendingUp className="w-4 h-4 text-blue-500" />
      case 'error-fix': return <AlertTriangle className="w-4 h-4 text-red-500" />
      case 'enhancement': return <Sparkles className="w-4 h-4 text-purple-500" />
      case 'best-practice': return <CheckCircle className="w-4 h-4 text-green-500" />
      default: return <Lightbulb className="w-4 h-4 text-orange-500" />
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Brain className="w-5 h-5 text-purple-500" />
            <span>AI Workflow Assistant</span>
            <Badge variant="secondary" className="ml-2">Beta</Badge>
          </CardTitle>
        </CardHeader>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-3 w-full">
          <TabsTrigger value="recommendations">
            <Lightbulb className="w-4 h-4 mr-2" />
            Recommendations
          </TabsTrigger>
          <TabsTrigger value="chat">
            <MessageCircle className="w-4 h-4 mr-2" />
            AI Chat
          </TabsTrigger>
          <TabsTrigger value="generator">
            <Zap className="w-4 h-4 mr-2" />
            Generate Workflow
          </TabsTrigger>
        </TabsList>

        <TabsContent value="recommendations" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Smart Recommendations</h3>
            <Button variant="outline" size="sm" onClick={loadRecommendations} disabled={recsLoading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${recsLoading ? 'animate-spin' : ''}`} />
              Refresh Analysis
            </Button>
          </div>

          {recsLoading ? (
            <Card className="p-8 text-center">
              <Loader2 className="w-8 h-8 mx-auto mb-3 animate-spin text-muted-foreground" />
              <p className="text-muted-foreground">Loading insights…</p>
            </Card>
          ) : recommendations.length === 0 ? (
            <Card className="p-8 text-center">
              <Bot className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">
                No recommendations yet. Use your agents and workflows to generate analytics insights, or ask in AI Chat.
              </p>
            </Card>
          ) : (
            <div className="space-y-4">
              {recommendations.map(recommendation => (
                <Card key={recommendation.id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        {getTypeIcon(recommendation.type)}
                        <div className="flex-1">
                          <h4 className="font-semibold text-base">{recommendation.title}</h4>
                          <p className="text-sm text-muted-foreground mt-1">
                            {recommendation.description}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Badge className={getImpactColor(recommendation.impact)}>
                          {recommendation.impact} impact
                        </Badge>
                        <Badge variant="outline" className={getEffortColor(recommendation.effort)}>
                          {recommendation.effort} effort
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  
                  <CardContent className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-muted-foreground">Confidence:</span>
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-green-500 h-2 rounded-full" 
                          style={{ width: `${recommendation.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium">
                        {(recommendation.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    
                    <div>
                      <h5 className="font-medium text-sm mb-1">AI Reasoning:</h5>
                      <p className="text-sm text-muted-foreground">
                        {recommendation.reasoning}
                      </p>
                    </div>
                    
                    <div>
                      <h5 className="font-medium text-sm mb-2">Implementation:</h5>
                      <div className="bg-slate-50 p-3 rounded-lg">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                          <div>
                            <span className="text-muted-foreground">Steps:</span>
                            <div className="font-medium">{recommendation.implementation.steps.length} steps</div>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Time:</span>
                            <div className="font-medium">{recommendation.implementation.estimatedTime}</div>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Skills:</span>
                            <div className="font-medium">
                              {recommendation.implementation.requiredSkills.length > 0
                                ? recommendation.implementation.requiredSkills.join(', ')
                                : '—'}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap gap-1">
                      {recommendation.tags.map(tag => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                    
                    <div className="flex space-x-2 pt-2">
                      <Button 
                        size="sm" 
                        onClick={() => onApplyRecommendation?.(recommendation)}
                      >
                        Apply Recommendation
                      </Button>
                      <Button variant="outline" size="sm">
                        View Details
                      </Button>
                      <Button variant="ghost" size="sm">
                        <ThumbsUp className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <ThumbsDown className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="chat" className="space-y-4">
          <Card className="h-[600px] flex flex-col">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center space-x-2">
                <Bot className="w-5 h-5" />
                <span>AI Assistant Chat</span>
              </CardTitle>
            </CardHeader>
            
            <CardContent className="flex-1 flex flex-col space-y-4">
              <ScrollArea className="flex-1 pr-4">
                <div className="space-y-4">
                  {chatMessages.map(message => (
                    <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[80%] rounded-lg p-3 ${
                        message.type === 'user' 
                          ? 'bg-blue-500 text-white' 
                          : 'bg-slate-100 text-slate-900'
                      }`}>
                        <div className="text-sm whitespace-pre-wrap">{message.message}</div>
                        {message.suggestions && (
                          <div className="mt-3 space-y-1">
                            {message.suggestions.map((suggestion, index) => (
                              <Button
                                key={index}
                                variant="ghost"
                                size="sm"
                                className="h-auto p-2 text-xs justify-start bg-white/20 hover:bg-white/30"
                                onClick={() => setCurrentMessage(suggestion)}
                              >
                                {suggestion}
                              </Button>
                            ))}
                          </div>
                        )}
                        <div className="text-xs opacity-70 mt-2">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {isGenerating && (
                    <div className="flex justify-start">
                      <div className="bg-slate-100 text-slate-900 rounded-lg p-3">
                        <div className="flex items-center space-x-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-600"></div>
                          <span className="text-sm">AI is thinking...</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>
              
              <div className="flex space-x-2">
                <Input
                  placeholder="Ask me anything about your workflow..."
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  disabled={isGenerating}
                />
                <Button 
                  onClick={handleSendMessage} 
                  disabled={isGenerating || !currentMessage.trim()}
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="generator" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Zap className="w-5 h-5 text-yellow-500" />
                <span>AI Workflow Generator</span>
              </CardTitle>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Describe your workflow in natural language:
                </label>
                <Textarea
                  placeholder="Example: Create a workflow that fetches customer data from our API, validates the email addresses, sends personalized welcome emails, and logs the results to our database..."
                  rows={4}
                  className="resize-none"
                  value={generatorPrompt}
                  onChange={(e) => setGeneratorPrompt(e.target.value)}
                />
              </div>
              
              <div className="flex space-x-2">
                <Button
                  className="flex-1"
                  onClick={handleGenerateWorkflow}
                  disabled={isGeneratingWorkflow || !generatorPrompt.trim()}
                >
                  {isGeneratingWorkflow ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4 mr-2" />
                  )}
                  Generate Workflow
                </Button>
                <Button variant="outline" disabled>
                  <Target className="w-4 h-4 mr-2" />
                  Use Template
                </Button>
              </div>

              {generatorResult && (
                <div className="text-sm bg-slate-50 p-4 rounded-lg whitespace-pre-wrap border">
                  {generatorResult}
                </div>
              )}
              
              <div className="text-sm text-muted-foreground bg-blue-50 p-3 rounded-lg">
                <div className="flex items-start space-x-2">
                  <Lightbulb className="w-4 h-4 text-blue-500 mt-0.5" />
                  <div>
                    <strong>Tip:</strong> Be specific about your requirements, data sources, 
                    and desired outcomes. The more details you provide, the better the AI 
                    can generate a tailored workflow for your needs.
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default AIWorkflowAssistant

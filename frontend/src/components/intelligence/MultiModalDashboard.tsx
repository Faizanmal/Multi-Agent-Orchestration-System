"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  getMultiModalSessions,
  processMultiModalIntelligence,
  getMultiModalSessionDetail,
  getAIModels,
  type MultiModalSession,
  type AIModelConfig,
  type MultiModalResult
} from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { 
  Image, 
  FileAudio, 
  FileVideo, 
  FileText, 
  Brain, 
  Zap,
  Eye,
  Sparkles,
  TrendingUp
} from 'lucide-react';

type MultiModalSessionDetail = {
  id: string;
  name: string;
  status: string;
  input_modalities: string[];
  results: Record<string, unknown>;
  modality_results: Array<Record<string, unknown>>;
  cross_modal_insights: Array<Record<string, unknown>>;
  created_at: string;
};

type CrossModalInsight = {
  type: string;
  modalities: string[];
  description: string;
  confidence: number;
};

export default function MultiModalDashboard() {
  const [sessions, setSessions] = useState<MultiModalSession[]>([]);
  const [models, setModels] = useState<AIModelConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [selectedAudio, setSelectedAudio] = useState<File | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<File | null>(null);
  const [sessionName, setSessionName] = useState('');
  const [processingResult, setProcessingResult] = useState<MultiModalResult | null>(null);
  const [selectedSession, setSelectedSession] = useState<MultiModalSessionDetail | null>(null);
  const { toast } = useToast();

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [sessionsData, modelsData] = await Promise.all([
        getMultiModalSessions(),
        getAIModels()
      ]);
      setSessions(sessionsData.sessions);
      setModels(modelsData.models);
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to load multi-modal data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    setTimeout(() => { loadData(); }, 0)
  }, [loadData]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, type: 'image' | 'audio' | 'video') => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (type === 'image') setSelectedImage(file);
      else if (type === 'audio') setSelectedAudio(file);
      else if (type === 'video') setSelectedVideo(file);
    }
  };

  const handleProcess = async () => {
    if (!textInput && !selectedImage && !selectedAudio && !selectedVideo) {
      toast({
        title: 'Error',
        description: 'Please provide at least one input (text, image, audio, or video)',
        variant: 'destructive',
      });
      return;
    }

    try {
      setLoading(true);
      const formData = new FormData();
      
      if (textInput) formData.append('text', textInput);
      if (selectedImage) formData.append('image', selectedImage);
      if (selectedAudio) formData.append('audio', selectedAudio);
      if (selectedVideo) formData.append('video', selectedVideo);
      if (sessionName) formData.append('session_name', sessionName);
      
      formData.append('processing_options', JSON.stringify({
        analyze_sentiment: true,
        generate_caption: true,
        detect_objects: true,
        extract_text: true,
        speech_to_text: true
      }));

      const result = await processMultiModalIntelligence(formData);
      setProcessingResult(result);
      
      toast({
        title: 'Success',
        description: `Processed ${result.input_modalities.length} modalities successfully`,
      });

      // Reload sessions
      await loadData();
      
      // Clear inputs
      setTextInput('');
      setSelectedImage(null);
      setSelectedAudio(null);
      setSelectedVideo(null);
      setSessionName('');
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to process multi-modal input',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleViewSession = async (sessionId: string) => {
    try {
      setLoading(true);
      const detail = await getMultiModalSessionDetail(sessionId);
      setSelectedSession(detail);
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to load session details',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const getModalityIcon = (modality: string) => {
    switch (modality.toLowerCase()) {
      case 'text': return <FileText className="h-4 w-4" />;
      case 'image': return <Image className="h-4 w-4" />; // eslint-disable-line jsx-a11y/alt-text
      case 'audio': return <FileAudio className="h-4 w-4" />;
      case 'video': return <FileVideo className="h-4 w-4" />;
      default: return <Brain className="h-4 w-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'default';
      case 'processing': return 'secondary';
      case 'failed': return 'destructive';
      default: return 'outline';
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Multi-Modal Intelligence</h1>
          <p className="text-muted-foreground">Process and analyze text, images, audio, and video with AI</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sessions</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{sessions.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">AI Models</CardTitle>
            <Sparkles className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{models.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {sessions.filter(s => s.status === 'completed').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Insights</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {sessions.reduce((sum, s) => sum + (s.insights_count || 0), 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle>Process Multi-Modal Input</CardTitle>
          <CardDescription>Upload text, images, audio, or video for AI analysis</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="sessionName">Session Name (Optional)</Label>
            <Input
              id="sessionName"
              placeholder="e.g., Customer Feedback Analysis"
              value={sessionName}
              onChange={(e) => setSessionName(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="textInput">
              <FileText className="inline h-4 w-4 mr-2" />
              Text Input
            </Label>
            <Textarea
              id="textInput"
              placeholder="Enter text to analyze..."
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              rows={4}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="imageInput">
                <Image className="inline h-4 w-4 mr-2" /> {/* eslint-disable-line jsx-a11y/alt-text */}
                Image
              </Label>
              <Input
                id="imageInput"
                type="file"
                accept="image/*"
                onChange={(e) => handleFileChange(e, 'image')}
              />
              {selectedImage && (
                <p className="text-sm text-muted-foreground">{selectedImage.name}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="audioInput">
                <FileAudio className="inline h-4 w-4 mr-2" />
                Audio
              </Label>
              <Input
                id="audioInput"
                type="file"
                accept="audio/*"
                onChange={(e) => handleFileChange(e, 'audio')}
              />
              {selectedAudio && (
                <p className="text-sm text-muted-foreground">{selectedAudio.name}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="videoInput">
                <FileVideo className="inline h-4 w-4 mr-2" />
                Video
              </Label>
              <Input
                id="videoInput"
                type="file"
                accept="video/*"
                onChange={(e) => handleFileChange(e, 'video')}
              />
              {selectedVideo && (
                <p className="text-sm text-muted-foreground">{selectedVideo.name}</p>
              )}
            </div>
          </div>

          <Button onClick={handleProcess} disabled={loading} className="w-full">
            <Zap className="mr-2 h-4 w-4" />
            Process Multi-Modal Input
          </Button>
        </CardContent>
      </Card>

      {/* Processing Results */}
      {processingResult && (
        <Card>
          <CardHeader>
            <CardTitle>Processing Results</CardTitle>
            <CardDescription>AI-powered multi-modal analysis</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex gap-2">
                {processingResult.input_modalities.map((modality: string) => (
                  <Badge key={modality} variant="outline">
                    {getModalityIcon(modality)}
                    <span className="ml-2">{modality}</span>
                  </Badge>
                ))}
                <Badge variant={getStatusColor(processingResult.status)}>
                  {processingResult.status}
                </Badge>
              </div>

              {processingResult.results && (
                <div className="space-y-3">
                  {Object.entries(processingResult.results).map(([key, value]: [string, unknown]) => (
                    <div key={key} className="p-3 border rounded">
                      <div className="font-medium capitalize mb-2">{key} Analysis</div>
                      <pre className="text-sm bg-muted p-2 rounded overflow-auto max-h-40">
                        {JSON.stringify(value, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              )}

              {processingResult.cross_modal_insights && processingResult.cross_modal_insights.length > 0 && (
                <div className="border-t pt-4">
                  <h3 className="font-medium mb-3 flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    Cross-Modal Insights
                  </h3>
                  <div className="space-y-2">
                    {processingResult.cross_modal_insights.map((insight: CrossModalInsight, index: number) => (
                      <div key={index} className="p-3 bg-muted rounded">
                        <div className="flex justify-between items-start mb-2">
                          <Badge>{insight.type}</Badge>
                          <Badge variant="outline">
                            {(insight.confidence * 100).toFixed(1)}% confidence
                          </Badge>
                        </div>
                        <p className="text-sm">{insight.description}</p>
                        <div className="flex gap-1 mt-2">
                          {insight.modalities.map((m: string) => (
                            <Badge key={m} variant="secondary" className="text-xs">
                              {m}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sessions List */}
      <Card>
        <CardHeader>
          <CardTitle>Processing Sessions</CardTitle>
          <CardDescription>All multi-modal processing sessions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="flex items-center justify-between p-4 border rounded-lg cursor-pointer hover:bg-muted/50"
                onClick={() => handleViewSession(session.id)}
              >
                <div className="flex items-center gap-4">
                  <Brain className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <h3 className="font-medium">{session.name}</h3>
                    <div className="flex gap-2 mt-1 flex-wrap">
                      {session.input_modalities.map((modality) => (
                        <Badge key={modality} variant="outline" className="text-xs">
                          {getModalityIcon(modality)}
                          <span className="ml-1">{modality}</span>
                        </Badge>
                      ))}
                      <Badge variant={getStatusColor(session.status)}>
                        {session.status}
                      </Badge>
                    </div>
                  </div>
                </div>
                <div className="text-sm text-muted-foreground text-right">
                  <div>Insights: {session.insights_count || 0}</div>
                  <div className="text-xs">{new Date(session.created_at).toLocaleDateString()}</div>
                </div>
              </div>
            ))}
            {sessions.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No sessions yet. Process multi-modal input to get started!
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Selected Session Details */}
      {selectedSession && (
        <Card>
          <CardHeader>
            <CardTitle>Session Details: {selectedSession.name}</CardTitle>
            <CardDescription>Detailed analysis results</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex gap-2">
                {selectedSession.input_modalities.map((modality: string) => (
                  <Badge key={modality} variant="outline">
                    {getModalityIcon(modality)}
                    <span className="ml-2">{modality}</span>
                  </Badge>
                ))}
              </div>
              <pre className="text-sm bg-muted p-4 rounded overflow-auto max-h-96">
                {JSON.stringify(selectedSession, null, 2)}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

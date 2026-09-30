"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { 
  getCoordinationSessions, 
  createCoordinationSession, 
  coordinateAgents, 
  getAgents,
  type CoordinationSession,
  type Agent,
  type CoordinationResult 
} from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { Activity, GitBranch, Network, Zap, TrendingUp, Users } from 'lucide-react';

export default function CoordinationDashboard() {
  const [sessions, setSessions] = useState<CoordinationSession[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedSession, setSelectedSession] = useState<CoordinationSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const [selectedStrategy, setSelectedStrategy] = useState<'sequential' | 'parallel' | 'hierarchical' | 'collaborative'>('sequential');
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [taskDescription, setTaskDescription] = useState('');
  const [coordinationResult, setCoordinationResult] = useState<CoordinationResult | null>(null);
  const { toast } = useToast();

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [sessionsData, agentsData] = await Promise.all([
        getCoordinationSessions(),
        getAgents()
      ]);
      setSessions(sessionsData.sessions);
      setAgents(agentsData.results);
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to load coordination data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    setTimeout(() => { loadData(); }, 0)
  }, [loadData]);

  const handleCreateSession = async () => {
    if (!newSessionName.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a session name',
        variant: 'destructive',
      });
      return;
    }

    try {
      setLoading(true);
      await createCoordinationSession(newSessionName, selectedStrategy);
      toast({
        title: 'Success',
        description: 'Coordination session created successfully',
      });
      setNewSessionName('');
      await loadData();
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to create coordination session',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCoordinateAgents = async () => {
    if (!selectedSession || selectedAgents.length === 0 || !taskDescription.trim()) {
      toast({
        title: 'Error',
        description: 'Please select a session, agents, and enter a task description',
        variant: 'destructive',
      });
      return;
    }

    try {
      setLoading(true);
      const result = await coordinateAgents(
        selectedSession.id,
        selectedAgents,
        taskDescription,
        selectedStrategy
      );
      setCoordinationResult(result);
      toast({
        title: 'Success',
        description: `${result.results.length} agents coordinated successfully`,
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to coordinate agents',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const getStrategyIcon = (strategy: string) => {
    switch (strategy) {
      case 'sequential': return <Activity className="h-4 w-4" />;
      case 'parallel': return <Network className="h-4 w-4" />;
      case 'hierarchical': return <GitBranch className="h-4 w-4" />;
      case 'collaborative': return <Users className="h-4 w-4" />;
      default: return <Zap className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Multi-Agent Coordination</h1>
          <p className="text-muted-foreground">Coordinate multiple agents with different strategies</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sessions</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{sessions.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agents.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Interactions</CardTitle>
            <Network className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {sessions.reduce((sum, s) => sum + s.interaction_count, 0)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Metrics</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {sessions.reduce((sum, s) => sum + s.metrics_count, 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Create New Session */}
        <Card>
          <CardHeader>
            <CardTitle>Create Coordination Session</CardTitle>
            <CardDescription>Set up a new multi-agent coordination session</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="sessionName">Session Name</Label>
              <Input
                id="sessionName"
                placeholder="e.g., Customer Support Workflow"
                value={newSessionName}
                onChange={(e) => setNewSessionName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="strategy">Coordination Strategy</Label>
              <Select value={selectedStrategy} onValueChange={(value: 'sequential' | 'parallel' | 'hierarchical' | 'collaborative') => setSelectedStrategy(value)}>
                <SelectTrigger id="strategy">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sequential">
                    <div className="flex items-center gap-2">
                      <Activity className="h-4 w-4" />
                      Sequential
                    </div>
                  </SelectItem>
                  <SelectItem value="parallel">
                    <div className="flex items-center gap-2">
                      <Network className="h-4 w-4" />
                      Parallel
                    </div>
                  </SelectItem>
                  <SelectItem value="hierarchical">
                    <div className="flex items-center gap-2">
                      <GitBranch className="h-4 w-4" />
                      Hierarchical
                    </div>
                  </SelectItem>
                  <SelectItem value="collaborative">
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4" />
                      Collaborative
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleCreateSession} disabled={loading} className="w-full">
              Create Session
            </Button>
          </CardContent>
        </Card>

        {/* Coordinate Agents */}
        <Card>
          <CardHeader>
            <CardTitle>Coordinate Agents</CardTitle>
            <CardDescription>Execute multi-agent coordination</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Select Session</Label>
              <Select onValueChange={(value) => setSelectedSession(sessions.find(s => s.id === value) || null)}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a session" />
                </SelectTrigger>
                <SelectContent>
                  {sessions.map((session) => (
                    <SelectItem key={session.id} value={session.id}>
                      {session.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Select Agents</Label>
              <div className="grid grid-cols-2 gap-2">
                {agents.slice(0, 6).map((agent) => (
                  <Button
                    key={agent.id}
                    variant={selectedAgents.includes(agent.id) ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => {
                      setSelectedAgents(prev =>
                        prev.includes(agent.id)
                          ? prev.filter(id => id !== agent.id)
                          : [...prev, agent.id]
                      );
                    }}
                  >
                    {agent.name}
                  </Button>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="taskDesc">Task Description</Label>
              <Input
                id="taskDesc"
                placeholder="Describe the task..."
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
              />
            </div>
            <Button onClick={handleCoordinateAgents} disabled={loading} className="w-full">
              <Zap className="mr-2 h-4 w-4" />
              Coordinate
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Sessions List */}
      <Card>
        <CardHeader>
          <CardTitle>Active Sessions</CardTitle>
          <CardDescription>All coordination sessions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sessions.map((session) => (
              <div key={session.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  {getStrategyIcon(session.strategy)}
                  <div>
                    <h3 className="font-medium">{session.name}</h3>
                    <div className="flex gap-2 mt-1">
                      <Badge variant="outline">{session.strategy}</Badge>
                      <Badge variant={session.is_active ? 'default' : 'secondary'}>
                        {session.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">
                  <div>Interactions: {session.interaction_count}</div>
                  <div>Metrics: {session.metrics_count}</div>
                </div>
              </div>
            ))}
            {sessions.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No coordination sessions yet. Create one to get started!
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Coordination Results */}
      {coordinationResult && (
        <Card>
          <CardHeader>
            <CardTitle>Coordination Results</CardTitle>
            <CardDescription>Latest coordination execution</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Badge>{coordinationResult.strategy}</Badge>
                <Badge className="ml-2" variant={coordinationResult.status === 'completed' ? 'default' : 'destructive'}>
                  {coordinationResult.status}
                </Badge>
              </div>
              <div className="space-y-2">
                {coordinationResult.results.map((result: CoordinationResult['results'][number], index: number) => (
                  <div key={index} className="p-3 border rounded">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium">{result.agent_name}</div>
                        <div className="text-sm text-muted-foreground">{result.agent_type}</div>
                      </div>
                      <Badge variant="outline">{result.timestamp}</Badge>
                    </div>
                    <p className="mt-2 text-sm">{result.output}</p>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

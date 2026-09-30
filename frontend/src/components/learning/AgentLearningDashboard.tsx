'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Brain, 
  TrendingUp, 
  Award, 
  Target, 
  Activity
} from 'lucide-react';
import { 
  getLearningProfiles, 
  getTopPerformers, 
  getAdaptiveStrategies,
  getTopStrategies
} from '@/lib/api';
import { toast } from 'sonner';

interface LearningProfile {
  id: string;
  agent: {
    id: string;
    name: string;
    agent_type: string;
  };
  algorithm: string;
  total_tasks_completed: number;
  success_rate: number;
  average_response_time: number;
  specialized_capabilities: Record<string, number>;
  skills?: Array<{
    skill_name: string;
    expertise_level: number;
    attempts_count: number;
    success_count: number;
  }>;
}

interface Strategy {
  id: string;
  name: string;
  description: string;
  strategy_type: string;
  success_rate: number;
  confidence_score: number;
  times_used: number;
  avg_completion_time: number;
}

export default function AgentLearningDashboard() {
  const [profiles, setProfiles] = useState<LearningProfile[]>([]);
  const [topPerformers, setTopPerformers] = useState<LearningProfile[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [topStrategies, setTopStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProfile, setSelectedProfile] = useState<LearningProfile | null>(null);
  const loadData = async () => {
    try {
      setLoading(true);
      const [profilesRes, performersRes, strategiesRes, topStrategiesRes] = await Promise.all([
        getLearningProfiles(),
        getTopPerformers(),
        getAdaptiveStrategies(),
        getTopStrategies()
      ]);

      setProfiles(profilesRes.data.results || profilesRes.data);
      setTopPerformers(performersRes.data.results || performersRes.data);
      setStrategies(strategiesRes.data.results || strategiesRes.data);
      setTopStrategies(topStrategiesRes.data.results || topStrategiesRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load learning data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setTimeout(() => {
      loadData();
    }, 0);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Activity className="h-12 w-12 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading learning data...</p>
        </div>
      </div>
    );
  }


  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Brain className="h-8 w-8 text-purple-500" />
            Agent Learning & Adaptation
          </h1>
          <p className="text-gray-600 mt-2">
            Monitor and manage agent learning profiles, skills, and strategies
          </p>
        </div>
        <Button onClick={loadData}>
          <Activity className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Agents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{profiles.length}</div>
            <p className="text-xs text-gray-500 mt-1">Learning profiles active</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Avg Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {profiles.length > 0 
                ? Math.round((profiles.reduce((sum, p) => sum + p.success_rate, 0) / profiles.length) * 100)
                : 0}%
            </div>
            <p className="text-xs text-gray-500 mt-1">Across all agents</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {profiles.reduce((sum, p) => sum + p.total_tasks_completed, 0)}
            </div>
            <p className="text-xs text-gray-500 mt-1">Completed tasks</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Active Strategies</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">{strategies.length}</div>
            <p className="text-xs text-gray-500 mt-1">Learned strategies</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="profiles" className="space-y-4">
        <TabsList>
          <TabsTrigger value="profiles">Learning Profiles</TabsTrigger>
          <TabsTrigger value="performers">Top Performers</TabsTrigger>
          <TabsTrigger value="strategies">Strategies</TabsTrigger>
          <TabsTrigger value="skills">Skills Matrix</TabsTrigger>
        </TabsList>

        <TabsContent value="profiles" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {profiles.map((profile) => (
              <Card key={profile.id} className="hover:shadow-lg transition-shadow cursor-pointer"
                    onClick={() => setSelectedProfile(profile)}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{profile.agent.name}</CardTitle>
                    <Badge variant="outline">{profile.agent.agent_type}</Badge>
                  </div>
                  <CardDescription>Algorithm: {profile.algorithm}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Success Rate</span>
                      <span className="font-semibold">{Math.round(profile.success_rate * 100)}%</span>
                    </div>
                    <Progress value={profile.success_rate * 100} className="h-2" />
                  </div>

                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Tasks Completed</span>
                    <span className="font-semibold">{profile.total_tasks_completed}</span>
                  </div>

                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Avg Response Time</span>
                    <span className="font-semibold">{profile.average_response_time.toFixed(2)}s</span>
                  </div>

                  {profile.specialized_capabilities && Object.keys(profile.specialized_capabilities).length > 0 && (
                    <div className="pt-2 border-t">
                      <p className="text-xs text-gray-500 mb-2">Specializations</p>
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(profile.specialized_capabilities).map(([key, value]) => (
                          <Badge key={key} variant="secondary" className="text-xs">
                            {key}: {Math.round((value as number) * 100)}%
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="performers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="h-5 w-5 text-yellow-500" />
                Top Performing Agents
              </CardTitle>
              <CardDescription>Agents with highest success rates and performance</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topPerformers.map((profile, index) => (
                  <div key={profile.id} className="flex items-center gap-4 p-4 border rounded-lg hover:bg-gray-50">
                    <div className="flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 text-white font-bold">
                      #{index + 1}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold">{profile.agent.name}</h3>
                        <Badge variant="outline">{profile.agent.agent_type}</Badge>
                      </div>
                      <div className="flex gap-4 text-sm text-gray-600">
                        <span>Success: {Math.round(profile.success_rate * 100)}%</span>
                        <span>Tasks: {profile.total_tasks_completed}</span>
                        <span>Response: {profile.average_response_time.toFixed(2)}s</span>
                      </div>
                    </div>
                    <TrendingUp className="h-5 w-5 text-green-500" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="strategies" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {topStrategies.map((strategy) => (
              <Card key={strategy.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{strategy.name}</CardTitle>
                    <Badge variant={strategy.confidence_score > 0.8 ? 'default' : 'secondary'}>
                      {Math.round(strategy.confidence_score * 100)}% confidence
                    </Badge>
                  </div>
                  <CardDescription>{strategy.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Type</span>
                    <Badge variant="outline">{strategy.strategy_type}</Badge>
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Success Rate</span>
                      <span className="font-semibold">{Math.round(strategy.success_rate * 100)}%</span>
                    </div>
                    <Progress value={strategy.success_rate * 100} className="h-2" />
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Times Used</span>
                      <p className="font-semibold">{strategy.times_used}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Avg Time</span>
                      <p className="font-semibold">{strategy.avg_completion_time.toFixed(2)}s</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="skills" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-blue-500" />
                Skills Matrix
              </CardTitle>
              <CardDescription>Agent skills and expertise levels</CardDescription>
            </CardHeader>
            <CardContent>
              {selectedProfile ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-lg">{selectedProfile.agent.name}</h3>
                    <Button variant="outline" size="sm" onClick={() => setSelectedProfile(null)}>
                      View All
                    </Button>
                  </div>
                  {selectedProfile.skills && selectedProfile.skills.length > 0 ? (
                    <div className="space-y-3">
                      {selectedProfile.skills.map((skill) => (
                        <div key={skill.skill_name} className="p-3 border rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium">{skill.skill_name}</span>
                            <Badge>{Math.round(skill.expertise_level * 100)}% expert</Badge>
                          </div>
                          <Progress value={skill.expertise_level * 100} className="h-2 mb-2" />
                          <div className="flex gap-4 text-xs text-gray-600">
                            <span>Attempts: {skill.attempts_count}</span>
                            <span>Success: {skill.success_count}</span>
                            <span>Rate: {skill.attempts_count > 0 
                              ? Math.round((skill.success_count / skill.attempts_count) * 100)
                              : 0}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center text-gray-500 py-8">No skills recorded yet</p>
                  )}
                </div>
              ) : (
                <p className="text-center text-gray-500 py-8">
                  Select an agent from the Learning Profiles tab to view skills
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

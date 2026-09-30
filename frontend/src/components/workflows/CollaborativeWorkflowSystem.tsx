'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import {
  Users,
  MessageSquare,
  Share2,
  UserPlus,
  Video,
  Phone,
  Send,
  Paperclip,
  MoreHorizontal,
  CheckCircle2,
  AlertCircle,
  History,
  Lock,
  Unlock,
  Activity
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import apiClient from '@/lib/api'

export interface RawMember {
  id?: string;
  name?: string;
  email?: string;
  avatar?: string;
  role?: string;
  status?: string;
  last_active?: string;
  lastActive?: string;
  permissions?: string[];
}

export interface RawComment {
  id?: string;
  author_id?: string;
  authorId?: string;
  author_name?: string;
  authorName?: string;
  content?: string;
  timestamp?: string;
  created_at?: string;
  resolved?: boolean;
  is_resolved?: boolean;
  node_id?: string;
}

interface TeamMember {
  id: string
  name: string
  email: string
  avatar?: string
  role: 'owner' | 'editor' | 'viewer'
  status: 'online' | 'offline' | 'away'
  lastActive: string
  permissions: string[]
}

interface Comment {
  id: string
  authorId: string
  authorName: string
  content: string
  timestamp: string
  replies?: Comment[]
  resolved: boolean
  nodeId?: string
}

interface WorkflowActivity {
  id: string
  userId: string
  userName: string
  action: string
  description: string
  timestamp: string
  type: 'edit' | 'comment' | 'share' | 'execute'
}

export interface CollaborationUpdate {
  event: string
  payload?: unknown
}

interface CollaborativeWorkflowSystemProps {
  currentUserId: string
  workflowId?: string
  onCollaborationUpdate?: (data: CollaborationUpdate) => void
}

const CollaborativeWorkflowSystem: React.FC<CollaborativeWorkflowSystemProps> = ({
  currentUserId,
  workflowId,
  onCollaborationUpdate
}) => {
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([])
  const [comments, setComments] = useState<Comment[]>([])
  const [activities, setActivities] = useState<WorkflowActivity[]>([])
  const [loading, setLoading] = useState(true)

  const [newComment, setNewComment] = useState('')
  const [newMemberEmail, setNewMemberEmail] = useState('')
  const [selectedRole, setSelectedRole] = useState<string>('viewer')
  const [isLocked, setIsLocked] = useState(false)
  const [realTimeEnabled, setRealTimeEnabled] = useState(true)

  const { toast } = useToast()

  useEffect(() => {
    let cancelled = false

    const loadCollaboration = async () => {
      setLoading(true)
      try {
        const [membersRes, commentsRes] = await Promise.allSettled([
          apiClient.getTeamMembers(),
          apiClient.getComments(),
        ])

        if (!cancelled && membersRes.status === 'fulfilled') {
          const raw = membersRes.value?.members ?? (membersRes.value as { members?: unknown[] })?.members ?? []
          const list = Array.isArray(raw) ? raw : []
          setTeamMembers((list as RawMember[]).map((m, i: number) => ({
            id: String(m.id ?? `member-${i}`),
            name: String(m.name || m.email || 'Member'),
            email: String(m.email || ''),
            avatar: m.avatar ? String(m.avatar) : undefined,
            role: (['owner', 'editor', 'viewer'].includes(String(m.role))
              ? String(m.role) as TeamMember['role']
              : 'viewer'),
            status: (['online', 'offline', 'away'].includes(String(m.status))
              ? String(m.status) as TeamMember['status']
              : 'offline'),
            lastActive: String(m.last_active || m.lastActive || 'Unknown'),
            permissions: Array.isArray(m.permissions) ? (m.permissions as string[]) : ['read'],
          })))
        }

        if (!cancelled && commentsRes.status === 'fulfilled') {
          const raw = commentsRes.value?.comments ?? []
          const list = Array.isArray(raw) ? raw : []
          setComments((list as RawComment[]).map((c, i: number) => ({
            id: String(c.id ?? `comment-${i}`),
            authorId: String(c.author_id || c.authorId || ''),
            authorName: String(c.author_name || c.authorName || 'User'),
            content: String(c.content || ''),
            timestamp: String(c.timestamp || c.created_at || ''),
            resolved: Boolean(c.resolved),
            nodeId: c.node_id ? String(c.node_id) : undefined,
          })))
        }

        // Activity feed requires a collaboration session; leave empty until available
        if (!cancelled) setActivities([])
      } catch (err) {
        console.error('Failed to load collaboration data', err)
        if (!cancelled) {
          setTeamMembers([])
          setComments([])
          setActivities([])
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadCollaboration()
    return () => { cancelled = true }
  }, [workflowId])

  // Soft refresh of members/comments when real-time toggle is on (no fake activity)
  useEffect(() => {
    if (!realTimeEnabled) return
    const interval = setInterval(async () => {
      try {
        const [membersRes, commentsRes] = await Promise.allSettled([
          apiClient.getTeamMembers(),
          apiClient.getComments(),
        ])
        if (membersRes.status === 'fulfilled') {
          const raw = membersRes.value?.members ?? []
          if (Array.isArray(raw)) {
            setTeamMembers((raw as RawMember[]).map((m, i: number) => ({
              id: String(m.id ?? `member-${i}`),
              name: String(m.name || m.email || 'Member'),
              email: String(m.email || ''),
              avatar: m.avatar ? String(m.avatar) : undefined,
              role: (['owner', 'editor', 'viewer'].includes(String(m.role))
                ? String(m.role) as TeamMember['role']
                : 'viewer'),
              status: (['online', 'offline', 'away'].includes(String(m.status))
                ? String(m.status) as TeamMember['status']
                : 'offline'),
              lastActive: String(m.last_active || m.lastActive || 'Unknown'),
              permissions: Array.isArray(m.permissions) ? (m.permissions as string[]) : ['read'],
            })))
          }
        }
        if (commentsRes.status === 'fulfilled') {
          const raw = commentsRes.value?.comments ?? []
          if (Array.isArray(raw)) {
            setComments((raw as RawComment[]).map((c, i: number) => ({
              id: String(c.id ?? `comment-${i}`),
              authorId: String(c.author_id || c.authorId || ''),
              authorName: String(c.author_name || c.authorName || 'User'),
              content: String(c.content || ''),
              timestamp: String(c.timestamp || c.created_at || ''),
              resolved: Boolean(c.resolved),
              nodeId: c.node_id ? String(c.node_id) : undefined,
            })))
          }
        }
      } catch {
        // ignore polling errors
      }
    }, 15000)
    return () => clearInterval(interval)
  }, [realTimeEnabled])

  const addComment = async () => {
    if (!newComment.trim()) return
    const content = newComment.trim()

    try {
      const saved = await apiClient.addComment(content)
      const comment: Comment = {
        id: String(saved.id || `comment_${Date.now()}`),
        authorId: String(saved.author_id || currentUserId),
        authorName: String(saved.author_name || 'Current User'),
        content: String(saved.content || content),
        timestamp: String(saved.timestamp || 'Just now'),
        resolved: Boolean(saved.resolved),
        nodeId: saved.node_id ? String(saved.node_id) : undefined,
      }
      setComments(prev => [comment, ...prev])
      setNewComment('')
      toast({
        title: 'Comment Added',
        description: 'Your comment has been posted successfully',
      })
      onCollaborationUpdate?.({ event: 'comment_added', payload: comment })
    } catch (err) {
      console.error(err)
      toast({
        title: 'Failed to add comment',
        description: 'Could not reach the collaboration API',
        variant: 'destructive',
      })
    }
  }

  const inviteMember = async () => {
    if (!newMemberEmail.trim()) return
    const email = newMemberEmail.trim()

    try {
      const saved = await apiClient.inviteTeamMember(
        email,
        selectedRole,
        selectedRole === 'owner' ? ['read', 'write', 'delete', 'share'] :
        selectedRole === 'editor' ? ['read', 'write', 'comment'] :
        ['read', 'comment']
      )
      const newMember: TeamMember = {
        id: String(saved.id || `member_${Date.now()}`),
        name: String(saved.name || email.split('@')[0]),
        email: String(saved.email || email),
        role: (['owner', 'editor', 'viewer'].includes(String(saved.role))
          ? String(saved.role) as TeamMember['role']
          : selectedRole as TeamMember['role']),
        status: 'offline',
        lastActive: String(saved.last_active || 'Never'),
        permissions: Array.isArray(saved.permissions) ? saved.permissions : ['read', 'comment'],
      }
      setTeamMembers(prev => [...prev, newMember])
      setNewMemberEmail('')
      toast({
        title: 'Invitation Sent',
        description: `Invitation sent to ${email}`,
      })
      onCollaborationUpdate?.({ event: 'member_invited', payload: newMember })
    } catch (err) {
      console.error(err)
      toast({
        title: 'Invite failed',
        description: 'Could not invite team member',
        variant: 'destructive',
      })
    }
  }

  const toggleCommentResolution = (commentId: string) => {
    setComments(prev => 
      prev.map(comment => 
        comment.id === commentId 
          ? { ...comment, resolved: !comment.resolved }
          : comment
      )
    )
  }

  const updateMemberRole = (memberId: string, newRole: string) => {
    setTeamMembers(prev => 
      prev.map(member => 
        member.id === memberId 
          ? { 
              ...member, 
              role: newRole as TeamMember['role'],
              permissions: newRole === 'owner' ? ['read', 'write', 'delete', 'share'] :
                          newRole === 'editor' ? ['read', 'write', 'comment'] :
                          ['read', 'comment']
            }
          : member
      )
    )

    toast({
      title: 'Role Updated',
      description: `Member role updated to ${newRole}`,
    })

    if (onCollaborationUpdate) {
      onCollaborationUpdate({ event: 'member_role_changed', payload: { memberId, newRole } })
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-500'
      case 'away': return 'bg-yellow-500'
      case 'offline': return 'bg-gray-400'
      default: return 'bg-gray-400'
    }
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'owner': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
      case 'editor': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'viewer': return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Users className="w-6 h-6" />
            Collaborative Workspace
          </h2>
          <p className="text-muted-foreground">
            Real-time collaboration and team workflow management
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {workflowId && (
            <div className="text-xs text-muted-foreground mr-3">Workflow: <span className="font-medium">{workflowId}</span></div>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={() => setIsLocked(!isLocked)}
            className={isLocked ? 'text-red-600' : 'text-green-600'}
          >
            {isLocked ? <Lock className="w-4 h-4 mr-2" /> : <Unlock className="w-4 h-4 mr-2" />}
            {isLocked ? 'Locked' : 'Unlocked'}
          </Button>
          
          <Button size="sm" variant="outline">
            <Video className="w-4 h-4 mr-2" />
            Start Meeting
          </Button>
          
          <Button size="sm">
            <Share2 className="w-4 h-4 mr-2" />
            Share Workflow
          </Button>
        </div>
      </div>

      <Tabs defaultValue="team" className="w-full">
        <TabsList className="grid grid-cols-4 w-full">
          <TabsTrigger value="team">Team Members</TabsTrigger>
          <TabsTrigger value="comments">Comments</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="team" className="space-y-4">
          {/* Team Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-2xl font-bold">{teamMembers.length}</p>
                    <p className="text-xs text-muted-foreground">Team Members</p>
                  </div>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-2xl font-bold">
                      {teamMembers.filter(m => m.status === 'online').length}
                    </p>
                    <p className="text-xs text-muted-foreground">Online Now</p>
                  </div>
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-2xl font-bold">{activities.length}</p>
                    <p className="text-xs text-muted-foreground">Recent Activities</p>
                  </div>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Add Member Form */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <UserPlus className="w-5 h-5" />
                Invite Team Member
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <div className="flex-1">
                  <Input
                    placeholder="Enter email address"
                    value={newMemberEmail}
                    onChange={(e) => setNewMemberEmail(e.target.value)}
                  />
                </div>
                <Select value={selectedRole} onValueChange={setSelectedRole}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="viewer">Viewer</SelectItem>
                    <SelectItem value="editor">Editor</SelectItem>
                    <SelectItem value="owner">Owner</SelectItem>
                  </SelectContent>
                </Select>
                <Button onClick={inviteMember}>Invite</Button>
              </div>
            </CardContent>
          </Card>

          {/* Team Members List */}
          <div className="space-y-3">
            {loading ? (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  Loading team…
                </CardContent>
              </Card>
            ) : teamMembers.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  No team members yet. Invite someone to collaborate.
                </CardContent>
              </Card>
            ) : null}
            {teamMembers.map((member) => (
              <Card key={member.id}>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="relative">
                        <Avatar>
                          <AvatarImage src={member.avatar} alt={member.name} />
                          <AvatarFallback>
                            {member.name.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full ${getStatusColor(member.status)} border-2 border-white`} />
                      </div>
                      
                      <div>
                        <h4 className="font-semibold">{member.name}</h4>
                        <p className="text-sm text-muted-foreground">{member.email}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge className={getRoleColor(member.role)}>
                            {member.role}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {member.lastActive}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Select
                        value={member.role}
                        onValueChange={(value) => updateMemberRole(member.id, value)}
                        disabled={member.id === currentUserId}
                      >
                        <SelectTrigger className="w-28">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="viewer">Viewer</SelectItem>
                          <SelectItem value="editor">Editor</SelectItem>
                          <SelectItem value="owner">Owner</SelectItem>
                        </SelectContent>
                      </Select>
                      
                      <Button size="sm" variant="ghost">
                        <Phone className="w-4 h-4" />
                      </Button>
                      
                      <Button size="sm" variant="ghost">
                        <MessageSquare className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="comments" className="space-y-4">
          {/* New Comment Form */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Add Comment</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Textarea
                  placeholder="Share your thoughts about this workflow..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  rows={3}
                />
                <div className="flex justify-between items-center">
                  <Button variant="outline" size="sm">
                    <Paperclip className="w-4 h-4 mr-2" />
                    Attach File
                  </Button>
                  <Button onClick={addComment}>
                    <Send className="w-4 h-4 mr-2" />
                    Post Comment
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Comments List */}
          <div className="space-y-3">
            {comments.map((comment) => (
              <Card key={comment.id} className={comment.resolved ? 'opacity-60' : ''}>
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        <Avatar className="w-8 h-8">
                          <AvatarFallback>
                            {comment.authorName.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h5 className="font-medium text-sm">{comment.authorName}</h5>
                            <span className="text-xs text-muted-foreground">
                              {comment.timestamp}
                            </span>
                            {comment.nodeId && (
                              <Badge variant="outline" className="text-xs">
                                Node: {comment.nodeId}
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm mt-1">{comment.content}</p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => toggleCommentResolution(comment.id)}
                        >
                          {comment.resolved ? (
                            <CheckCircle2 className="w-4 h-4 text-green-500" />
                          ) : (
                            <AlertCircle className="w-4 h-4 text-yellow-500" />
                          )}
                        </Button>
                        
                        <Button size="sm" variant="ghost">
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="activity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="w-5 h-5" />
                Recent Activity
              </CardTitle>
              <CardDescription>
                Track all team activities and workflow changes
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-3">
                  {activities.length === 0 && (
                    <p className="text-sm text-muted-foreground text-center py-8">
                      No activity yet
                    </p>
                  )}
                  {activities.map((activity, index) => (
                    <div key={activity.id}>
                      <div className="flex items-start space-x-3">
                        <Avatar className="w-8 h-8">
                          <AvatarFallback>
                            {activity.userName.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        
                        <div className="flex-1">
                          <p className="text-sm">
                            <span className="font-medium">{activity.userName}</span>
                            {' '}
                            <span className="text-muted-foreground">{activity.action}</span>
                            {' '}
                            <span>{activity.description}</span>
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {activity.timestamp}
                          </p>
                        </div>
                        
                        <Badge variant="outline" className="text-xs">
                          {activity.type}
                        </Badge>
                      </div>
                      
                      {index < activities.length - 1 && (
                        <Separator className="my-3" />
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Collaboration Settings</CardTitle>
              <CardDescription>
                Configure collaboration preferences and permissions
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Real-time Updates</Label>
                    <p className="text-sm text-muted-foreground">
                      Enable live collaboration and activity updates
                    </p>
                  </div>
                  <Button
                    variant={realTimeEnabled ? "default" : "outline"}
                    onClick={() => setRealTimeEnabled(!realTimeEnabled)}
                  >
                    {realTimeEnabled ? 'Enabled' : 'Disabled'}
                  </Button>
                </div>

                <Separator />

                <div className="space-y-3">
                  <Label>Default Member Role</Label>
                  <Select defaultValue="viewer">
                    <SelectTrigger className="w-48">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="viewer">Viewer</SelectItem>
                      <SelectItem value="editor">Editor</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Separator />

                <div className="space-y-3">
                  <Label>Notification Preferences</Label>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" id="email-notifications" defaultChecked />
                      <label htmlFor="email-notifications" className="text-sm">
                        Email notifications for comments
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" id="workflow-changes" defaultChecked />
                      <label htmlFor="workflow-changes" className="text-sm">
                        Notify on workflow changes
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" id="execution-alerts" />
                      <label htmlFor="execution-alerts" className="text-sm">
                        Execution status alerts
                      </label>
                    </div>
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

export default CollaborativeWorkflowSystem
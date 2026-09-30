'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { Progress } from '@/components/ui/progress'
import {
  GitBranch,
  GitCommit,
  GitMerge,
  Tag,
  Clock,
  User,
  FileText,
  ArrowRight,
  Plus,
  Minus,
  RotateCcw,
  Download,
  Upload,
  Eye,
  Star,
  Copy
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import apiClient from '@/lib/api'

interface WorkflowVersion {
  id: string
  version: string
  branch: string
  author: string
  timestamp: string
  message: string
  changes: {
    added: number
    modified: number
    removed: number
  }
  status: 'draft' | 'published' | 'archived'
  tags: string[]
  performance: {
    executionTime: number
    successRate: number
    nodeCount: number
  }
  isPrimary?: boolean
}

interface Branch {
  name: string
  isActive: boolean
  lastCommit: string
  author: string
  ahead: number
  behind: number
  status: 'active' | 'merged' | 'stale'
}

interface ComparisonData {
  fromVersion: string
  toVersion: string
  differences: {
    nodesAdded: string[]
    nodesRemoved: string[]
    nodesModified: string[]
    edgesChanged: string[]
    configChanges: Record<string, unknown>
  }
}

interface SmartVersionControlProps {
  currentVersion?: string
  onVersionChange?: (versionId: string) => void
  onBranchSwitch?: (branchName: string) => void
  workflowId?: string
}

const SmartVersionControl: React.FC<SmartVersionControlProps> = ({
  currentVersion = 'v1.0.0',
  onVersionChange,
  onBranchSwitch,
  workflowId
}) => {
  const [versions, setVersions] = useState<WorkflowVersion[]>([])
  const [branches, setBranches] = useState<Branch[]>([])
  const [loading, setLoading] = useState(Boolean(workflowId))
  const [selectedVersions, setSelectedVersions] = useState<string[]>([])
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null)
  const [newBranchName, setNewBranchName] = useState('')
  const [commitMessage, setCommitMessage] = useState('')
  const [autoVersioning, setAutoVersioning] = useState(true)
  const [smartMerging, setSmartMerging] = useState(true)

  const { toast } = useToast()

  useEffect(() => {
    let cancelled = false

    const loadVersions = async () => {
      if (!workflowId) {
        setVersions([])
        setBranches([])
        setLoading(false)
        return
      }

      setLoading(true)
      try {
        const res = await apiClient.getWorkflowVersions(workflowId)
        const rawList = Array.isArray(res?.versions)
          ? res.versions
          : Array.isArray((res as unknown as { results?: unknown[] })?.results)
            ? (res as unknown as { results: unknown[] }).results
            : []

        const mapped: WorkflowVersion[] = rawList.map((v, i) => {
          const raw = v as unknown as Record<string, unknown>
          const changes = (raw.changes && typeof raw.changes === 'object'
            ? raw.changes
            : { added: 0, modified: 0, removed: 0 }) as WorkflowVersion['changes']
          const nodesSnap = Array.isArray(raw.nodes_snapshot) ? raw.nodes_snapshot : []
          return {
            id: String(raw.id ?? `v-${i}`),
            version: String(raw.version || raw.version_number || `1.${i}.0`),
            branch: String(raw.branch || 'main'),
            author: String(raw.author || raw.created_by_username || 'Unknown'),
            timestamp: String(raw.timestamp || raw.created_at || ''),
            message: String(raw.message || raw.change_description || 'Version snapshot'),
            changes: {
              added: Number(changes.added ?? 0),
              modified: Number(changes.modified ?? 0),
              removed: Number(changes.removed ?? 0),
            },
            status: (['draft', 'published', 'archived'].includes(String(raw.status))
              ? String(raw.status) as WorkflowVersion['status']
              : 'draft'),
            tags: Array.isArray(raw.tags) ? (raw.tags as string[]) : [],
            performance: {
              executionTime: Number((raw.performance as Record<string, unknown>)?.executionTime ?? 0),
              successRate: Number((raw.performance as Record<string, unknown>)?.successRate ?? 0),
              nodeCount: Number((raw.performance as Record<string, unknown>)?.nodeCount ?? nodesSnap.length),
            },
            isPrimary: i === 0,
          }
        })

        if (!cancelled) {
          setVersions(mapped)
          const branchNames = [...new Set(mapped.map(v => v.branch))]
          setBranches(branchNames.length > 0
            ? branchNames.map((name, i) => ({
                name,
                isActive: name === 'main' || i === 0,
                lastCommit: mapped.find(v => v.branch === name)?.timestamp || '',
                author: mapped.find(v => v.branch === name)?.author || '',
                ahead: 0,
                behind: 0,
                status: 'active' as const,
              }))
            : [{ name: 'main', isActive: true, lastCommit: '', author: '', ahead: 0, behind: 0, status: 'active' as const }])
        }
      } catch (err) {
        console.error('Failed to load workflow versions', err)
        if (!cancelled) {
          setVersions([])
          setBranches([{ name: 'main', isActive: true, lastCommit: '', author: '', ahead: 0, behind: 0, status: 'active' }])
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadVersions()
    return () => { cancelled = true }
  }, [workflowId])

  const generateComparison = useCallback((fromId: string, toId: string) => {
    const fromVersion = versions.find(v => v.id === fromId)
    const toVersion = versions.find(v => v.id === toId)
    
    if (!fromVersion || !toVersion) return

    const comparison: ComparisonData = {
      fromVersion: fromVersion.version,
      toVersion: toVersion.version,
      differences: {
        nodesAdded: [],
        nodesRemoved: [],
        nodesModified: [],
        edgesChanged: [],
        configChanges: {
          message: {
            from: fromVersion.message,
            to: toVersion.message,
          },
          changes: {
            from: fromVersion.changes,
            to: toVersion.changes,
          },
        }
      }
    }

    setComparisonData(comparison)
  }, [versions])

  useEffect(() => {
    if (selectedVersions.length === 2) {
      setTimeout(() => { generateComparison(selectedVersions[0], selectedVersions[1]) }, 0)
    }
  }, [selectedVersions, generateComparison])

  const createVersion = async () => {
    if (!commitMessage.trim()) {
      toast({
        title: 'Commit Message Required',
        description: 'Please provide a commit message for this version',
        variant: 'destructive'
      })
      return
    }

    if (!workflowId) {
      toast({
        title: 'No workflow selected',
        description: 'Open a saved workflow to create versions',
        variant: 'destructive'
      })
      return
    }

    try {
      const saved = await apiClient.saveWorkflowVersion(workflowId, {
        message: commitMessage.trim(),
      })
      const newVersion: WorkflowVersion = {
        id: String(saved.id || `v${Date.now()}`),
        version: String(saved.version || `1.${versions.length + 1}.0`),
        branch: String(saved.branch || branches.find(b => b.isActive)?.name || 'main'),
        author: String(saved.author || 'Current User'),
        timestamp: String(saved.timestamp || 'Just now'),
        message: String(saved.message || commitMessage),
        changes: saved.changes || { added: 0, modified: 0, removed: 0 },
        status: saved.status || 'draft',
        tags: saved.tags || [],
        performance: { executionTime: 0, successRate: 0, nodeCount: 0 }
      }

      setVersions(prev => [newVersion, ...prev])
      setCommitMessage('')
      toast({
        title: 'Version Created',
        description: `Version ${newVersion.version} has been created successfully`,
      })
    } catch (err) {
      console.error(err)
      toast({
        title: 'Failed to create version',
        description: 'Could not save workflow version',
        variant: 'destructive'
      })
    }
  }

  const createBranch = () => {
    if (!newBranchName.trim()) return

    const newBranch: Branch = {
      name: newBranchName,
      isActive: false,
      lastCommit: 'Just created',
      author: 'Current User',
      ahead: 0,
      behind: 0,
      status: 'active'
    }

    setBranches(prev => [...prev, newBranch])
    setNewBranchName('')

    toast({
      title: 'Branch Created',
      description: `Branch ${newBranchName} has been created successfully`,
    })
  }

  const switchBranch = (branchName: string) => {
    setBranches(prev => 
      prev.map(branch => ({
        ...branch,
        isActive: branch.name === branchName
      }))
    )

    if (onBranchSwitch) {
      onBranchSwitch(branchName)
    }

    toast({
      title: 'Branch Switched',
      description: `Switched to branch: ${branchName}`,
    })
  }

  const rollbackToVersion = (versionId: string) => {
    const version = versions.find(v => v.id === versionId)
    if (!version) return

    if (onVersionChange) {
      onVersionChange(versionId)
    }

    toast({
      title: 'Rollback Complete',
      description: `Rolled back to version ${version.version}`,
    })
  }

  const toggleVersionSelection = (versionId: string) => {
    setSelectedVersions(prev => {
      if (prev.includes(versionId)) {
        return prev.filter(id => id !== versionId)
      } else if (prev.length < 2) {
        return [...prev, versionId]
      } else {
        return [prev[1], versionId] // Replace oldest selection
      }
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'draft': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      case 'archived': return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
      default: return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
    }
  }

  const getBranchStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600'
      case 'merged': return 'text-blue-600'
      case 'stale': return 'text-orange-600'
      default: return 'text-gray-600'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <GitBranch className="w-6 h-6" />
            Smart Version Control
          </h2>
          <p className="text-muted-foreground">
            Advanced workflow versioning with intelligent branching and automated optimization
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-sm">
            Current: {currentVersion}
          </Badge>
          <Button size="sm" variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button size="sm" variant="outline">
            <Upload className="w-4 h-4 mr-2" />
            Import
          </Button>
        </div>
      </div>

      <Tabs defaultValue="versions" className="w-full">
        <TabsList className="grid grid-cols-4 w-full">
          <TabsTrigger value="versions">Version History</TabsTrigger>
          <TabsTrigger value="branches">Branches</TabsTrigger>
          <TabsTrigger value="compare">Compare</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="versions" className="space-y-4">
          {/* Create Version */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <GitCommit className="w-5 h-5" />
                Create New Version
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="commit-message">Commit Message</Label>
                  <Textarea
                    id="commit-message"
                    placeholder="Describe your changes..."
                    value={commitMessage}
                    onChange={(e) => setCommitMessage(e.target.value)}
                    rows={3}
                  />
                </div>
                <div className="flex gap-2">
                  <Button onClick={createVersion}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Version
                  </Button>
                  <Button variant="outline">
                    <Tag className="w-4 h-4 mr-2" />
                    Add Tag
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Version List */}
          <div className="space-y-3">
            {loading && (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  Loading versions…
                </CardContent>
              </Card>
            )}
            {!loading && versions.length === 0 && (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  {workflowId
                    ? 'No versions yet. Create one to start tracking changes.'
                    : 'Select a saved workflow to view version history.'}
                </CardContent>
              </Card>
            )}
            {versions.map((version) => (
              <Card 
                key={version.id} 
                className={`cursor-pointer transition-all ${
                  selectedVersions.includes(version.id) 
                    ? 'ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-950' 
                    : ''
                } ${version.isPrimary ? 'border-green-200 bg-green-50 dark:bg-green-950' : ''}`}
                onClick={() => toggleVersionSelection(version.id)}
              >
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-semibold text-lg">{version.version}</h4>
                        <Badge className={getStatusColor(version.status)}>
                          {version.status}
                        </Badge>
                        {version.isPrimary && (
                          <Badge variant="outline">
                            <Star className="w-3 h-3 mr-1" />
                            Current
                          </Badge>
                        )}
                        <Badge variant="outline">
                          <GitBranch className="w-3 h-3 mr-1" />
                          {version.branch}
                        </Badge>
                      </div>
                      
                      <p className="text-sm text-muted-foreground mb-3">
                        {version.message}
                      </p>
                      
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {version.author}
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {version.timestamp}
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="flex items-center gap-1 text-green-600">
                            <Plus className="w-3 h-3" />
                            {version.changes.added}
                          </span>
                          <span className="flex items-center gap-1 text-blue-600">
                            <FileText className="w-3 h-3" />
                            {version.changes.modified}
                          </span>
                          <span className="flex items-center gap-1 text-red-600">
                            <Minus className="w-3 h-3" />
                            {version.changes.removed}
                          </span>
                        </div>
                      </div>
                      
                      {version.tags.length > 0 && (
                        <div className="flex gap-1 mt-2">
                          {version.tags.map((tag) => (
                            <Badge key={tag} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col items-end gap-2">
                      <div className="text-right text-xs">
                        <div>Execution: {version.performance.executionTime}s</div>
                        <div className="text-green-600">Success: {version.performance.successRate}%</div>
                        <div>Nodes: {version.performance.nodeCount}</div>
                      </div>
                      
                      <div className="flex gap-1">
                        <Button size="sm" variant="ghost">
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button 
                          size="sm" 
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation()
                            rollbackToVersion(version.id)
                          }}
                        >
                          <RotateCcw className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="ghost">
                          <Copy className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="branches" className="space-y-4">
          {/* Create Branch */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <GitBranch className="w-5 h-5" />
                Create New Branch
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <Input
                  placeholder="Branch name (e.g., feature/new-feature)"
                  value={newBranchName}
                  onChange={(e) => setNewBranchName(e.target.value)}
                />
                <Button onClick={createBranch}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Branch
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Branch List */}
          <div className="space-y-3">
            {branches.map((branch) => (
              <Card 
                key={branch.name} 
                className={branch.isActive ? 'border-blue-200 bg-blue-50 dark:bg-blue-950' : ''}
              >
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <GitBranch className={`w-5 h-5 ${getBranchStatusColor(branch.status)}`} />
                      <div>
                        <h4 className="font-semibold flex items-center gap-2">
                          {branch.name}
                          {branch.isActive && (
                            <Badge variant="default" className="text-xs">Active</Badge>
                          )}
                        </h4>
                        <p className="text-sm text-muted-foreground">
                          Last commit by {branch.author} • {branch.lastCommit}
                        </p>
                        {(branch.ahead > 0 || branch.behind > 0) && (
                          <div className="flex items-center gap-2 mt-1 text-xs">
                            {branch.ahead > 0 && (
                              <span className="text-green-600">↑{branch.ahead} ahead</span>
                            )}
                            {branch.behind > 0 && (
                              <span className="text-red-600">↓{branch.behind} behind</span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Badge variant="outline" className={getBranchStatusColor(branch.status)}>
                        {branch.status}
                      </Badge>
                      
                      {!branch.isActive && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => switchBranch(branch.name)}
                        >
                          Switch
                        </Button>
                      )}
                      
                      {branch.status === 'active' && branch.name !== 'main' && (
                        <Button size="sm" variant="outline">
                          <GitMerge className="w-4 h-4 mr-2" />
                          Merge
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="compare" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Version Comparison</CardTitle>
              <CardDescription>
                {selectedVersions.length === 0 && 'Select two versions from the Version History tab to compare'}
                {selectedVersions.length === 1 && 'Select one more version to compare'}
                {selectedVersions.length === 2 && `Comparing ${selectedVersions[0]} with ${selectedVersions[1]}`}
              </CardDescription>
            </CardHeader>
            
            {comparisonData && (
              <CardContent className="space-y-6">
                <div className="flex items-center justify-center gap-4">
                  <Badge variant="outline" className="text-lg py-2 px-4">
                    {comparisonData.fromVersion}
                  </Badge>
                  <ArrowRight className="w-6 h-6 text-muted-foreground" />
                  <Badge variant="outline" className="text-lg py-2 px-4">
                    {comparisonData.toVersion}
                  </Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card className="border-green-200">
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          +{comparisonData.differences.nodesAdded.length}
                        </div>
                        <p className="text-sm text-muted-foreground">Nodes Added</p>
                        {comparisonData.differences.nodesAdded.length > 0 && (
                          <div className="mt-2 text-xs">
                            {comparisonData.differences.nodesAdded.map(node => (
                              <Badge key={node} variant="outline" className="mr-1 mb-1 text-green-700">
                                {node}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-blue-200">
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">
                          ~{comparisonData.differences.nodesModified.length}
                        </div>
                        <p className="text-sm text-muted-foreground">Nodes Modified</p>
                        {comparisonData.differences.nodesModified.length > 0 && (
                          <div className="mt-2 text-xs">
                            {comparisonData.differences.nodesModified.map(node => (
                              <Badge key={node} variant="outline" className="mr-1 mb-1 text-blue-700">
                                {node}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-red-200">
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-red-600">
                          -{comparisonData.differences.nodesRemoved.length}
                        </div>
                        <p className="text-sm text-muted-foreground">Nodes Removed</p>
                        {comparisonData.differences.nodesRemoved.length > 0 && (
                          <div className="mt-2 text-xs">
                            {comparisonData.differences.nodesRemoved.map(node => (
                              <Badge key={node} variant="outline" className="mr-1 mb-1 text-red-700">
                                {node}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {Object.keys(comparisonData.differences.configChanges).length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Configuration Changes</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {Object.entries(comparisonData.differences.configChanges).map(([key, change]) => (
                          <div key={key} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                            <code className="text-sm font-mono">{key}</code>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline" className="text-red-600">
                                {JSON.stringify((change as { from: unknown; to: unknown }).from)}
                              </Badge>
                              <ArrowRight className="w-4 h-4" />
                              <Badge variant="outline" className="text-green-600">
                                {JSON.stringify((change as { from: unknown; to: unknown }).to)}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </CardContent>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Version Control Settings</CardTitle>
              <CardDescription>
                Configure automatic versioning and intelligent merging options
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Automatic Versioning</Label>
                    <p className="text-sm text-muted-foreground">
                      Automatically create versions on workflow changes
                    </p>
                  </div>
                  <Button
                    variant={autoVersioning ? "default" : "outline"}
                    onClick={() => setAutoVersioning(!autoVersioning)}
                  >
                    {autoVersioning ? 'Enabled' : 'Disabled'}
                  </Button>
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Smart Merging</Label>
                    <p className="text-sm text-muted-foreground">
                      Use AI to intelligently merge conflicting changes
                    </p>
                  </div>
                  <Button
                    variant={smartMerging ? "default" : "outline"}
                    onClick={() => setSmartMerging(!smartMerging)}
                  >
                    {smartMerging ? 'Enabled' : 'Disabled'}
                  </Button>
                </div>

                <Separator />

                <div className="space-y-3">
                  <Label>Version Retention Policy</Label>
                  <Select defaultValue="30">
                    <SelectTrigger className="w-64">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="7">Keep for 7 days</SelectItem>
                      <SelectItem value="30">Keep for 30 days</SelectItem>
                      <SelectItem value="90">Keep for 90 days</SelectItem>
                      <SelectItem value="365">Keep for 1 year</SelectItem>
                      <SelectItem value="-1">Keep forever</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Separator />

                <div className="space-y-3">
                  <Label>Performance Tracking</Label>
                  <Progress value={75} className="w-full" />
                  <p className="text-sm text-muted-foreground">
                    Performance metrics collection: 75% storage used
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default SmartVersionControl
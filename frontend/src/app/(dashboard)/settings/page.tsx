"use client";

import React, { useCallback, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Settings,
  User,
  Shield,
  Bell,
  Palette,
  Key,
  Globe,
  CreditCard,
  Building2,
  Eye,
  EyeOff,
  Save,
  Trash2,
  Plus,
  Copy,
  Check,
  Moon,
  Sun,
  Monitor,
  Zap,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { cn } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';
import apiClient from '@/lib/api';

type ApiKeyRecord = {
  id: string;
  name: string;
  key: string;
  created_at: string;
  last_used?: string | null;
  is_active?: boolean;
};

type BillingStatus = {
  plan: string;
  subscription_status?: string | null;
  current_period_end?: string | null;
  usage: {
    used_tokens: number;
    total_tokens: number | null;
    percentage: number;
  };
};

function normalizeApiKeys(payload: unknown): ApiKeyRecord[] {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload as ApiKeyRecord[];
  if (typeof payload === 'object') {
    const obj = payload as Record<string, unknown>;
    if (Array.isArray(obj.api_keys)) return obj.api_keys as ApiKeyRecord[];
    if (Array.isArray(obj.results)) return obj.results as ApiKeyRecord[];
  }
  return [];
}

function maskKey(key: string): string {
  if (!key || key.length < 12) return key || '••••';
  return `${key.slice(0, 7)}...${key.slice(-4)}`;
}

function formatDate(value?: string | null): string {
  if (!value) return 'Never';
  try {
    return new Date(value).toLocaleDateString();
  } catch {
    return value;
  }
}

export default function SettingsPage() {
  const { user, updateProfile, accessToken } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [theme, setTheme] = useState('system');
  const [showKey, setShowKey] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [bio, setBio] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const [apiKeys, setApiKeys] = useState<ApiKeyRecord[]>([]);
  const [apiKeysLoading, setApiKeysLoading] = useState(false);
  const [apiKeysError, setApiKeysError] = useState<string | null>(null);
  const [creatingKey, setCreatingKey] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [showCreateKey, setShowCreateKey] = useState(false);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null);

  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [billingLoading, setBillingLoading] = useState(false);

  useEffect(() => {
    if (!user) return;
    setTimeout(() => { setFirstName(user.first_name || ''); }, 0)
    setTimeout(() => {
        setLastName(user.last_name || '');
      }, 0)
    setTimeout(() => setEmail(user.email || ''), 0);
  }, [user]);

  const loadApiKeys = useCallback(async () => {
    setApiKeysLoading(true);
    setApiKeysError(null);
    try {
      const data = await apiClient.getAPIKeys();
      setApiKeys(normalizeApiKeys(data));
    } catch {
      setApiKeysError('Could not load API keys.');
      setApiKeys([]);
    } finally {
      setApiKeysLoading(false);
    }
  }, []);

  const loadBilling = useCallback(async () => {
      setBillingLoading(true);
      try {
        const base = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
        const token = accessToken || (typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null);
        const res = await fetch(`${base}/api/billing/status/`, {
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });
        if (!res.ok) throw new Error('Failed');
        const data = await res.json();
        setBilling({
          plan: data.plan || user?.subscription_tier || 'free',
          subscription_status: data.subscription_status ?? null,
          current_period_end: data.current_period_end ?? null,
          usage: {
            used_tokens: data.usage?.used_tokens ?? 0,
            total_tokens: data.usage?.total_tokens ?? null,
            percentage: data.usage?.percentage ?? 0,
          },
        });
      } catch {
        setBilling({
          plan: user?.subscription_tier || 'free',
          usage: { used_tokens: 0, total_tokens: null, percentage: 0 },
        });
      } finally {
        setBillingLoading(false);
      }
    }, [accessToken, user]);

  useEffect(() => {
    if (activeTab === 'api-keys') {
      setTimeout(() => { loadApiKeys(); }, 0)
    }
    if (activeTab === 'billing') {
      setTimeout(() => {
          loadBilling();
        }, 0)
    }
  }, [activeTab, loadApiKeys, loadBilling]);

  const displayName =
    user?.display_name ||
    [firstName, lastName].filter(Boolean).join(' ') ||
    user?.username ||
    'User';
  const initials = displayName
    .split(/\s+/)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || 'U';

  const copyToClipboard = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    setSaveMessage(null);
    try {
      const ok = await updateProfile({
        first_name: firstName,
        last_name: lastName,
      } as Parameters<typeof updateProfile>[0]);
      setSaveMessage(ok ? 'Profile updated.' : 'Could not update profile.');
    } catch {
      setSaveMessage('Could not update profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleCreateKey = async () => {
    const name = newKeyName.trim() || 'API Key';
    setCreatingKey(true);
    try {
      const created = await apiClient.createAPIKey(name);
      setNewlyCreatedKey(created.key);
      setNewKeyName('');
      setShowCreateKey(false);
      await loadApiKeys();
    } catch {
      setApiKeysError('Could not create API key.');
    } finally {
      setCreatingKey(false);
    }
  };

  const handleDeleteKey = async (keyId: string) => {
    try {
      await apiClient.deleteAPIKey(keyId);
      setApiKeys((prev) => prev.filter((k) => k.id !== keyId));
    } catch {
      setApiKeysError('Could not delete API key.');
    }
  };

  const planLabel = (billing?.plan || user?.subscription_tier || 'free').replace(/^\w/, (c) => c.toUpperCase());
  const usedTokens = billing?.usage.used_tokens ?? 0;
  const totalTokens = billing?.usage.total_tokens;
  const usagePct =
    totalTokens && totalTokens > 0
      ? Math.min(100, (usedTokens / totalTokens) * 100)
      : billing?.usage.percentage ?? 0;

  return (
    <AppLayout>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Settings className="h-8 w-8 text-primary" />
            Settings
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage your account settings and preferences
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar Navigation */}
          <Card className="lg:w-64 shrink-0">
            <CardContent className="p-2">
              <nav className="space-y-1">
                {[
                  { id: 'profile', icon: User, label: 'Profile' },
                  { id: 'security', icon: Shield, label: 'Security' },
                  { id: 'notifications', icon: Bell, label: 'Notifications' },
                  { id: 'appearance', icon: Palette, label: 'Appearance' },
                  { id: 'api-keys', icon: Key, label: 'API Keys' },
                  { id: 'billing', icon: CreditCard, label: 'Billing' },
                  { id: 'team', icon: Building2, label: 'Team' },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                      activeTab === item.id
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                    {item.label}
                  </button>
                ))}
              </nav>
            </CardContent>
          </Card>

          {/* Main Content */}
          <div className="flex-1 space-y-6">
            {/* Profile Settings */}
            {activeTab === 'profile' && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
              >
                <Card>
                  <CardHeader>
                    <CardTitle>Profile Information</CardTitle>
                    <CardDescription>Update your personal information</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Avatar */}
                    <div className="flex items-center gap-6">
                      <Avatar className="h-20 w-20">
                        <AvatarImage src={user?.avatar || undefined} />
                        <AvatarFallback className="text-2xl">{initials}</AvatarFallback>
                      </Avatar>
                      <div className="space-y-2">
                        <Button variant="outline" size="sm">Change Avatar</Button>
                        <p className="text-xs text-muted-foreground">JPG, PNG or GIF. Max 2MB.</p>
                      </div>
                    </div>

                    <Separator />

                    {/* Form */}
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="firstName">First Name</Label>
                        <Input
                          id="firstName"
                          value={firstName}
                          onChange={(e) => setFirstName(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="lastName">Last Name</Label>
                        <Input
                          id="lastName"
                          value={lastName}
                          onChange={(e) => setLastName(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2 sm:col-span-2">
                        <Label htmlFor="email">Email</Label>
                        <Input id="email" type="email" value={email} disabled />
                      </div>
                      <div className="space-y-2 sm:col-span-2">
                        <Label htmlFor="bio">Bio</Label>
                        <Textarea
                          id="bio"
                          placeholder="Tell us about yourself..."
                          value={bio}
                          onChange={(e) => setBio(e.target.value)}
                        />
                      </div>
                    </div>
                  </CardContent>
                  <CardFooter className="border-t pt-6 flex justify-end gap-3">
                    {saveMessage && (
                      <p className="mr-auto text-sm text-muted-foreground self-center">{saveMessage}</p>
                    )}
                    <Button variant="outline" type="button" onClick={() => {
                      setFirstName(user?.first_name || '');
                      setLastName(user?.last_name || '');
                      setBio('');
                      setSaveMessage(null);
                    }}>
                      Cancel
                    </Button>
                    <Button className="gap-2" onClick={handleSaveProfile} disabled={saving}>
                      <Save className="h-4 w-4" />
                      {saving ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </CardFooter>
                </Card>
              </motion.div>
            )}

            {/* Security Settings */}
            {activeTab === 'security' && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
              >
                <Card>
                  <CardHeader>
                    <CardTitle>Password</CardTitle>
                    <CardDescription>Change your password</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="currentPassword">Current Password</Label>
                      <Input id="currentPassword" type="password" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="newPassword">New Password</Label>
                      <Input id="newPassword" type="password" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="confirmPassword">Confirm New Password</Label>
                      <Input id="confirmPassword" type="password" />
                    </div>
                  </CardContent>
                  <CardFooter className="border-t pt-6">
                    <Button>Update Password</Button>
                  </CardFooter>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Two-Factor Authentication</CardTitle>
                    <CardDescription>Add an extra layer of security</CardDescription>
                  </CardHeader>
                  <CardContent className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                        <Shield className="h-5 w-5 text-green-500" />
                      </div>
                      <div>
                        <p className="font-medium">Two-Factor Authentication</p>
                        <p className="text-sm text-muted-foreground">Currently enabled</p>
                      </div>
                    </div>
                    <Switch defaultChecked />
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Active Sessions</CardTitle>
                    <CardDescription>Manage your active sessions</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {[
                      { device: 'Chrome on MacOS', location: 'San Francisco, US', current: true },
                      { device: 'Safari on iPhone', location: 'San Francisco, US', current: false },
                    ].map((session, index) => (
                      <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                        <div className="flex items-center gap-3">
                          <Globe className="h-5 w-5 text-muted-foreground" />
                          <div>
                            <p className="font-medium flex items-center gap-2">
                              {session.device}
                              {session.current && <Badge variant="secondary" className="text-xs">Current</Badge>}
                            </p>
                            <p className="text-sm text-muted-foreground">{session.location}</p>
                          </div>
                        </div>
                        {!session.current && (
                          <Button variant="ghost" size="sm" className="text-destructive">
                            Revoke
                          </Button>
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Appearance Settings */}
            {activeTab === 'appearance' && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
              >
                <Card>
                  <CardHeader>
                    <CardTitle>Theme</CardTitle>
                    <CardDescription>Choose your preferred theme</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-4">
                      {[
                        { id: 'light', icon: Sun, label: 'Light' },
                        { id: 'dark', icon: Moon, label: 'Dark' },
                        { id: 'system', icon: Monitor, label: 'System' },
                      ].map((option) => (
                        <button
                          key={option.id}
                          onClick={() => setTheme(option.id)}
                          className={cn(
                            "flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all",
                            theme === option.id
                              ? "border-primary bg-primary/5"
                              : "border-border hover:border-primary/50"
                          )}
                        >
                          <option.icon className={cn(
                            "h-6 w-6",
                            theme === option.id ? "text-primary" : "text-muted-foreground"
                          )} />
                          <span className="font-medium">{option.label}</span>
                        </button>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Preferences</CardTitle>
                    <CardDescription>Customize your experience</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Reduce Motion</p>
                        <p className="text-sm text-muted-foreground">Minimize animations</p>
                      </div>
                      <Switch />
                    </div>
                    <Separator />
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Compact Mode</p>
                        <p className="text-sm text-muted-foreground">Show more content on screen</p>
                      </div>
                      <Switch />
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* API Keys Settings */}
            {activeTab === 'api-keys' && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
              >
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                      <CardTitle>API Keys</CardTitle>
                      <CardDescription>Manage your API keys for authentication</CardDescription>
                    </div>
                    <Button className="gap-2" onClick={() => setShowCreateKey((v) => !v)}>
                      <Plus className="h-4 w-4" />
                      Create Key
                    </Button>
                  </CardHeader>
                  <CardContent>
                    {showCreateKey && (
                      <div className="flex flex-col sm:flex-row gap-3 mb-6 p-4 rounded-xl border">
                        <Input
                          placeholder="Key name"
                          value={newKeyName}
                          onChange={(e) => setNewKeyName(e.target.value)}
                        />
                        <Button onClick={handleCreateKey} disabled={creatingKey}>
                          {creatingKey ? 'Creating...' : 'Create'}
                        </Button>
                      </div>
                    )}
                    {newlyCreatedKey && (
                      <div className="mb-4 p-3 rounded-lg bg-muted/50 text-sm">
                        <p className="font-medium mb-1">New key created — copy it now:</p>
                        <code className="font-mono break-all">{newlyCreatedKey}</code>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="ml-2"
                          onClick={() => copyToClipboard('new', newlyCreatedKey)}
                        >
                          {copied === 'new' ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                        </Button>
                      </div>
                    )}
                    {apiKeysError && (
                      <p className="text-sm text-destructive mb-4">{apiKeysError}</p>
                    )}
                    {apiKeysLoading ? (
                      <p className="text-sm text-muted-foreground">Loading API keys...</p>
                    ) : apiKeys.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No API keys yet. Create one to get started.</p>
                    ) : (
                      <div className="space-y-4">
                        {apiKeys.map((key) => {
                          const status = key.is_active === false ? 'inactive' : 'active';
                          return (
                            <div key={key.id} className="flex items-center gap-4 p-4 rounded-xl bg-muted/50">
                              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                                <Key className="h-5 w-5 text-primary" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="font-medium flex items-center gap-2">
                                  {key.name}
                                  <Badge variant={status === 'active' ? 'default' : 'secondary'}>
                                    {status}
                                  </Badge>
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                  <code className="text-sm text-muted-foreground font-mono">
                                    {showKey === key.id ? key.key : maskKey(key.key)}
                                  </code>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-6 w-6"
                                    onClick={() => setShowKey(showKey === key.id ? null : key.id)}
                                  >
                                    {showKey === key.id ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-6 w-6"
                                    onClick={() => copyToClipboard(key.id, key.key)}
                                  >
                                    {copied === key.id ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                                  </Button>
                                </div>
                              </div>
                              <div className="hidden sm:block text-right text-sm text-muted-foreground">
                                <p>Created {formatDate(key.created_at)}</p>
                                <p>Last used {formatDate(key.last_used)}</p>
                              </div>
                              <AlertDialog>
                                <AlertDialogTrigger asChild>
                                  <Button variant="ghost" size="icon" className="text-destructive">
                                    <Trash2 className="h-4 w-4" />
                                  </Button>
                                </AlertDialogTrigger>
                                <AlertDialogContent>
                                  <AlertDialogHeader>
                                    <AlertDialogTitle>Delete API Key?</AlertDialogTitle>
                                    <AlertDialogDescription>
                                      This action cannot be undone. Any applications using this key will lose access.
                                    </AlertDialogDescription>
                                  </AlertDialogHeader>
                                  <AlertDialogFooter>
                                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                                    <AlertDialogAction
                                      className="bg-destructive text-destructive-foreground"
                                      onClick={() => handleDeleteKey(key.id)}
                                    >
                                      Delete
                                    </AlertDialogAction>
                                  </AlertDialogFooter>
                                </AlertDialogContent>
                              </AlertDialog>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Notifications Settings */}
            {activeTab === 'notifications' && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
              >
                <Card>
                  <CardHeader>
                    <CardTitle>Notification Preferences</CardTitle>
                    <CardDescription>Choose how you want to be notified</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {[
                      { title: 'Email Notifications', description: 'Receive updates via email', enabled: true },
                      { title: 'Push Notifications', description: 'Browser push notifications', enabled: true },
                      { title: 'Agent Alerts', description: 'Get notified when agents fail', enabled: true },
                      { title: 'Weekly Digest', description: 'Summary of your activity', enabled: false },
                      { title: 'Marketing', description: 'Product updates and news', enabled: false },
                    ].map((item, index) => (
                      <React.Fragment key={item.title}>
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">{item.title}</p>
                            <p className="text-sm text-muted-foreground">{item.description}</p>
                          </div>
                          <Switch defaultChecked={item.enabled} />
                        </div>
                        {index < 4 && <Separator />}
                      </React.Fragment>
                    ))}
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Billing Settings */}
            {activeTab === 'billing' && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
              >
                <Card>
                  <CardHeader>
                    <CardTitle>Current Plan</CardTitle>
                    <CardDescription>Manage your subscription</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-primary/20">
                      <div className="flex items-center gap-4">
                        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500">
                          <Zap className="h-6 w-6 text-white" />
                        </div>
                        <div>
                          <p className="text-lg font-bold">
                            {billingLoading ? 'Loading...' : `${planLabel} Plan`}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {billing?.subscription_status
                              ? `Status: ${billing.subscription_status}`
                              : 'No active Stripe subscription'}
                            {billing?.current_period_end
                              ? ` • Renews ${formatDate(billing.current_period_end)}`
                              : ''}
                          </p>
                        </div>
                      </div>
                      <Button variant="outline">Manage Plan</Button>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Usage</CardTitle>
                    <CardDescription>Current billing period usage</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {billingLoading ? (
                      <p className="text-sm text-muted-foreground">Loading usage...</p>
                    ) : (
                      <div>
                        <div className="flex justify-between text-sm mb-2">
                          <span>Messages</span>
                          <span className="text-muted-foreground">
                            {usedTokens.toLocaleString()}
                            {totalTokens != null ? ` / ${totalTokens.toLocaleString()}` : ' / —'}
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full bg-primary rounded-full transition-all"
                            style={{ width: `${usagePct}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Team Settings */}
            {activeTab === 'team' && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
              >
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                      <CardTitle>Team Members</CardTitle>
                      <CardDescription>Manage your team and permissions</CardDescription>
                    </div>
                    <Button className="gap-2">
                      <Plus className="h-4 w-4" />
                      Invite Member
                    </Button>
                  </CardHeader>
                  <CardContent>
                    {!user ? (
                      <p className="text-sm text-muted-foreground">No team members yet</p>
                    ) : (
                      <div className="space-y-4">
                        <div className="flex items-center gap-4 p-4 rounded-xl bg-muted/50">
                          <Avatar>
                            <AvatarImage src={user.avatar || undefined} />
                            <AvatarFallback>{initials}</AvatarFallback>
                          </Avatar>
                          <div className="flex-1">
                            <p className="font-medium">{displayName}</p>
                            <p className="text-sm text-muted-foreground">{user.email}</p>
                          </div>
                          <Select defaultValue={(user.role === 'admin' ? 'admin' : 'member')}>
                            <SelectTrigger className="w-32">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="admin">Admin</SelectItem>
                              <SelectItem value="member">Member</SelectItem>
                              <SelectItem value="viewer">Viewer</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </div>
        </div>
      </motion.div>
    </AppLayout>
  );
}

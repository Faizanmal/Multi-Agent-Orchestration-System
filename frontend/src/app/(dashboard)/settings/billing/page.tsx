"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, Zap, CreditCard, ArrowUpRight } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { AppLayout } from '@/components/layout/AppLayout';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export default function BillingSettingsPage() {
  const [isUpgrading, setIsUpgrading] = useState(false);
  const [plan, setPlan] = useState('free');
  const [usagePercentage, setUsagePercentage] = useState(0);
  const [usedMessages, setUsedMessages] = useState('0');
  const [totalMessages, setTotalMessages] = useState('100');
  const [stripeConfigured, setStripeConfigured] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(`${API_BASE}/api/billing/status/`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (!res.ok) return;
        const data = await res.json();
        setPlan(data.plan || 'free');
        setUsagePercentage(data.usage?.percentage ?? 0);
        // Backend meters messages; fields are still named *_tokens for API compat
        setUsedMessages(Number(data.usage?.used_tokens ?? data.usage?.used ?? 0).toLocaleString());
        setTotalMessages(Number(data.usage?.total_tokens ?? data.usage?.limit ?? 100).toLocaleString());
        setStripeConfigured(!!data.stripe_configured);
      } catch {
        /* keep defaults */
      }
    };
    load();
  }, []);

  const handleUpgrade = async (priceId: string) => {
    setIsUpgrading(true);
    try {
      const { trackEvent } = await import('@/lib/analytics');
      trackEvent('upgrade_clicked', { source: 'billing_page', priceId });
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE}/api/billing/create-checkout-session/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ priceId }),
      });
      const data = await response.json();
      if (data.url && typeof data.url === 'string' && data.url.startsWith('http')) {
        window.location.href = data.url;
        return;
      }
      toast({
        title: stripeConfigured ? 'Checkout unavailable' : 'Stripe not configured',
        description: data.error || 'Set STRIPE_SECRET_KEY on the backend to enable paid plans.',
        variant: 'destructive',
      });
    } catch (error) {
      console.error('Error creating checkout session:', error);
      toast({ title: 'Billing error', description: 'Could not start checkout.', variant: 'destructive' });
    } finally {
      setIsUpgrading(false);
    }
  };

  const currentPlan = plan.charAt(0).toUpperCase() + plan.slice(1);

  return (
    <AppLayout>
      <div className="container mx-auto max-w-5xl py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Billing & Usage</h1>
          <p className="text-muted-foreground mt-1">
            Manage your workspace subscription and monitor monthly message usage.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-12">
          <Card className="md:col-span-2 shadow-sm border-slate-200 dark:border-slate-800">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl">Current Billing Cycle Usage</CardTitle>
                  <CardDescription>Resets on the 1st of each month</CardDescription>
                </div>
                <Badge variant="outline" className="bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200 dark:border-blue-800">
                  {currentPlan} Plan
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="font-medium text-slate-700 dark:text-slate-300">Messages this month</span>
                <span className="font-semibold text-slate-900 dark:text-white">
                  {usedMessages} <span className="text-muted-foreground font-normal">/ {totalMessages}</span>
                </span>
              </div>
              <Progress value={usagePercentage} className={`h-3 ${usagePercentage > 80 ? 'bg-red-100 dark:bg-red-950/50 [&>div]:bg-red-500' : ''}`} />

              {usagePercentage > 80 && (
                <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/30 rounded-md flex items-start gap-3">
                  <Zap className="h-5 w-5 text-red-600 mt-0.5 shrink-0" />
                  <div>
                    <h4 className="text-sm font-semibold text-red-800 dark:text-red-400">Approaching Limit</h4>
                    <p className="text-xs text-red-600/80 dark:text-red-400/80 mt-1">
                      You have used {usagePercentage}% of your monthly quota. Upgrade to Pro for higher limits.
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="shadow-sm border-slate-200 dark:border-slate-800">
            <CardHeader>
              <CardTitle className="text-xl">Payment Method</CardTitle>
              <CardDescription>Securely managed by Stripe</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center justify-center py-6 text-center">
              <div className="h-12 w-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-3">
                <CreditCard className="h-6 w-6 text-slate-400" />
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                {stripeConfigured ? 'No payment method on file' : 'Stripe keys not configured yet'}
              </p>
              <Button variant="outline" className="w-full" disabled={!stripeConfigured}>
                Add Payment Method
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="mb-6">
          <h2 className="text-2xl font-bold tracking-tight">Upgrade Your Plan</h2>
          <p className="text-muted-foreground mt-1">
            Scale your multi-agent workflows with higher limits and advanced features.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <Card className="border-slate-200 dark:border-slate-800 opacity-80">
            <CardHeader>
              <CardTitle>Free</CardTitle>
              <div className="text-3xl font-bold mt-2">$0<span className="text-sm text-muted-foreground font-normal">/month</span></div>
              <CardDescription className="pt-2">For individuals trying out the platform.</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3 text-sm">
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-slate-400" /> 1 Workspace</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-slate-400" /> Up to 3 Agents</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-slate-400" /> 100 messages / month</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-slate-400" /> Community Support</li>
              </ul>
            </CardContent>
            <CardFooter>
              <Button variant="outline" className="w-full" disabled>
                {plan === 'free' ? 'Current Plan' : 'Free'}
              </Button>
            </CardFooter>
          </Card>

          <Card className="border-blue-500 shadow-md relative">
            <div className="absolute top-0 right-0 transform translate-x-2 -translate-y-2">
              <Badge className="bg-gradient-to-r from-blue-600 to-purple-600 border-0">Recommended</Badge>
            </div>
            <CardHeader>
              <CardTitle>Pro</CardTitle>
              <div className="text-3xl font-bold mt-2">$49<span className="text-sm text-muted-foreground font-normal">/month</span></div>
              <CardDescription className="pt-2">For startups building production workflows.</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3 text-sm">
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-blue-500" /> Unlimited Workspaces</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-blue-500" /> Unlimited Agents</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-blue-500" /> 10,000 messages / month</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-blue-500" /> Priority Email Support</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-blue-500" /> Advanced Plugins Access</li>
              </ul>
            </CardContent>
            <CardFooter>
              <Button
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                onClick={() => handleUpgrade(process.env.NEXT_PUBLIC_STRIPE_PRICE_PRO || 'price_pro')}
                disabled={isUpgrading || plan === 'pro'}
              >
                {plan === 'pro' ? 'Current Plan' : isUpgrading ? 'Loading...' : 'Upgrade to Pro'}
              </Button>
            </CardFooter>
          </Card>

          <Card className="border-slate-200 dark:border-slate-800">
            <CardHeader>
              <CardTitle>Premium</CardTitle>
              <div className="text-3xl font-bold mt-2">Custom</div>
              <CardDescription className="pt-2">For large-scale, custom infrastructure.</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3 text-sm">
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-slate-400" /> 1,000,000 messages / month</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-slate-400" /> Dedicated Groq Instances</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-slate-400" /> SSO & Audit Logs</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-slate-400" /> Dedicated Support</li>
              </ul>
            </CardContent>
            <CardFooter>
              <Button variant="outline" className="w-full gap-2" asChild>
                <a href="mailto:support@multiagent.ai">
                  Contact Sales <ArrowUpRight className="h-4 w-4" />
                </a>
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
}

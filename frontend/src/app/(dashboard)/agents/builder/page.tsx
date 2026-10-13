'use client';

import { AppLayout } from '@/components/layout/AppLayout';
import { AgentTemplateBuilder } from '@/components/agents/AgentTemplateBuilder';

export default function AgentBuilderPage() {
  return (
    <AppLayout>
      <div className="p-6 space-y-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Agent Template Builder</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Create custom agents with system prompts and tool access.
          </p>
        </div>
        <AgentTemplateBuilder />
      </div>
    </AppLayout>
  );
}

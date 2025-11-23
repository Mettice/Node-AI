/**
 * Home Page (Main Application)
 */

import { WorkflowHeader } from '@/components/Header/WorkflowHeader';
import { MainLayout } from '@/components/Layout/MainLayout';
import { SSEProcessor } from '@/components/Execution/SSEProcessor';

export function HomePage() {
  return (
    <div className="min-h-screen bg-slate-900">
      <div className="h-screen flex flex-col">
        {/* Header with Workflow Management */}
        <WorkflowHeader />

        {/* Main Content */}
        <main className="flex-1 overflow-hidden">
          <MainLayout />
        </main>
      </div>

      {/* Background SSE Processor - Always runs to update node statuses */}
      <SSEProcessor />
    </div>
  );
}


/**
 * Left sidebar: list of recent Temporal workflow executions.
 */
import { useWorkflowStore } from '../store/workflowStore'
import { useWorkflows } from '../hooks/useWorkflows'
import { StatusBadge } from './StatusBadge'
import type { NodeStatus } from '../lib/api'

function formatTime(ts: number | null): string {
  if (ts === null) return '—'
  return new Date(ts * 1000).toLocaleString()
}

export function WorkflowList() {
  useWorkflows()

  const { workflows, workflowsLoading, workflowsError, selectedWorkflowId, selectWorkflow } =
    useWorkflowStore()

  return (
    <aside className="w-72 h-full bg-gray-50 border-r border-gray-200 flex flex-col overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 bg-white">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
          Workflows
        </h2>
        {workflowsLoading && (
          <span className="text-xs text-gray-400 animate-pulse">refreshing…</span>
        )}
      </div>

      {workflowsError && (
        <div className="px-4 py-2 text-xs text-red-600 bg-red-50 border-b border-red-200">
          {workflowsError}
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {workflows.length === 0 && !workflowsLoading && (
          <div className="px-4 py-6 text-sm text-gray-400 text-center">
            No workflows found.
            <br />
            <span className="text-xs">Check your Temporal connection.</span>
          </div>
        )}
        {workflows.map((wf) => (
          <button
            key={wf.workflow_id}
            onClick={() => selectWorkflow(wf.workflow_id)}
            className={`w-full text-left px-4 py-3 border-b border-gray-100 hover:bg-blue-50 transition-colors ${
              selectedWorkflowId === wf.workflow_id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
            }`}
          >
            <div className="flex items-center justify-between gap-2 mb-0.5">
              <span className="text-xs font-semibold text-gray-700 truncate flex-1">
                {wf.workflow_type}
              </span>
              <StatusBadge status={wf.status as NodeStatus} />
            </div>
            <div className="text-xs text-gray-400 truncate">{wf.workflow_id}</div>
            <div className="text-xs text-gray-400 mt-0.5">{formatTime(wf.start_time)}</div>
          </button>
        ))}
      </div>
    </aside>
  )
}

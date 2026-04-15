/**
 * Right sidebar: metadata for the selected DAG node.
 */
import { useWorkflowStore } from '../store/workflowStore'
import { StatusBadge } from './StatusBadge'
import type { NodeStatus } from '../lib/api'

function Row({ label, value }: { label: string; value: unknown }) {
  if (value === null || value === undefined || value === '') return null
  const display =
    typeof value === 'number'
      ? String(value)
      : typeof value === 'object'
      ? JSON.stringify(value, null, 2)
      : String(value)
  return (
    <div className="flex flex-col py-1.5 border-b border-gray-100 last:border-0">
      <span className="text-xs text-gray-400 uppercase tracking-wide">{label}</span>
      <span className="text-xs text-gray-700 font-mono break-all whitespace-pre-wrap mt-0.5">
        {display}
      </span>
    </div>
  )
}

function formatTs(ts: number | null | undefined): string | null {
  if (!ts) return null
  return new Date(ts * 1000).toLocaleString()
}

export function DetailPanel() {
  const { selectedNode, selectNode } = useWorkflowStore()

  if (!selectedNode) {
    return (
      <aside className="w-72 h-full bg-gray-50 border-l border-gray-200 flex items-center justify-center">
        <p className="text-xs text-gray-400 text-center px-4">
          Click a node to see its details
        </p>
      </aside>
    )
  }

  const { label, type, status, metadata } = selectedNode

  return (
    <aside className="w-72 h-full bg-white border-l border-gray-200 flex flex-col overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-800 truncate">{label}</h2>
          <div className="text-xs text-gray-400 capitalize">{type.replace('_', ' ')}</div>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={status as NodeStatus} />
          <button
            onClick={() => selectNode(null)}
            className="text-gray-400 hover:text-gray-600 text-sm ml-1"
            aria-label="Close panel"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-2">
        {/* Common fields */}
        <Row label="ID" value={selectedNode.id} />

        {/* Type-specific metadata */}
        {type === 'workflow' && (
          <>
            <Row label="Workflow ID" value={metadata.workflow_id as string} />
            <Row label="Run ID" value={metadata.run_id as string} />
            <Row label="Task Queue" value={metadata.task_queue as string} />
            <Row label="Start Time" value={formatTs(metadata.start_time as number)} />
            <Row label="Close Time" value={formatTs(metadata.close_time as number)} />
          </>
        )}

        {(type === 'activity' || type === 'hitl_gate') && (
          <>
            <Row label="Activity ID" value={metadata.activity_id as string} />
            <Row label="Activity Type" value={metadata.activity_type as string} />
            <Row label="Attempt" value={metadata.attempt as number} />
            <Row label="Scheduled" value={formatTs(metadata.scheduled_time as number)} />
            <Row label="Started" value={formatTs(metadata.started_time as number)} />
            <Row label="Closed" value={formatTs(metadata.close_time as number)} />
            <Row label="Duration" value={metadata.duration_s ? `${metadata.duration_s}s` : null} />
            {metadata.failure_message && (
              <Row label="Failure" value={metadata.failure_message as string} />
            )}
          </>
        )}

        {type === 'llm_span' && (
          <>
            <Row label="Span ID" value={metadata.span_id as string} />
            <Row label="Trace ID" value={metadata.trace_id as string} />
            <Row label="Model" value={metadata.model as string} />
            <Row label="Prompt Tokens" value={metadata.prompt_tokens as number} />
            <Row label="Completion Tokens" value={metadata.completion_tokens as number} />
            <Row label="Total Tokens" value={metadata.total_tokens as number} />
            <Row
              label="Cost"
              value={
                metadata.cost_usd != null
                  ? `$${(metadata.cost_usd as number).toFixed(6)}`
                  : null
              }
            />
            <Row label="Latency" value={metadata.latency_ms ? `${metadata.latency_ms}ms` : null} />
            <Row label="Start Time" value={formatTs(metadata.start_time as number)} />
            <Row label="End Time" value={formatTs(metadata.end_time as number)} />
          </>
        )}

        {type === 'opa_gate' && (
          <>
            <Row label="Policy ID" value={metadata.policy_id as string} />
            <Row label="Result" value={metadata.result as string} />
          </>
        )}
      </div>
    </aside>
  )
}

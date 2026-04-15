import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'
import { StatusBadge } from '../StatusBadge'
import type { NodeStatus } from '../../lib/api'

interface LLMSpanNodeData extends Record<string, unknown> {
  label: string
  status: NodeStatus
  metadata: Record<string, unknown>
}

const BORDER: Record<NodeStatus, string> = {
  pending: 'border-gray-300',
  running: 'border-blue-400 status-pulse-running',
  success: 'border-purple-400',
  failed: 'border-red-400',
  waiting: 'border-amber-400 status-pulse-waiting',
  cancelled: 'border-gray-300',
}

function LLMSpanNode({ data }: NodeProps<LLMSpanNodeData>) {
  const { label, status, metadata } = data
  const model = metadata.model as string | undefined
  const totalTokens = metadata.total_tokens as number | undefined
  const costUsd = metadata.cost_usd as number | undefined
  const latencyMs = metadata.latency_ms as number | undefined

  return (
    <div className={`bg-purple-50 rounded-md border-2 shadow px-3 py-2 w-52 ${BORDER[status]}`}>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <div className="flex items-center gap-2 mb-1">
        <span className="text-base">🧠</span>
        <span className="font-medium text-purple-900 text-sm truncate flex-1">{label}</span>
      </div>
      <StatusBadge status={status} />
      {model && (
        <div className="mt-1 text-xs text-purple-600 truncate">{model}</div>
      )}
      <div className="flex flex-wrap gap-2 mt-1 text-xs text-gray-500">
        {totalTokens !== undefined && totalTokens > 0 && (
          <span>{totalTokens.toLocaleString()} tok</span>
        )}
        {latencyMs !== undefined && (
          <span>{latencyMs}ms</span>
        )}
        {costUsd !== undefined && costUsd !== null && (
          <span>${(costUsd as number).toFixed(4)}</span>
        )}
      </div>
    </div>
  )
}

export default memo(LLMSpanNode)

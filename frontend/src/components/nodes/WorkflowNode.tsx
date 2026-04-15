import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'
import { StatusBadge } from '../StatusBadge'
import type { NodeStatus } from '../../lib/api'

interface WorkflowNodeData extends Record<string, unknown> {
  label: string
  status: NodeStatus
  metadata: Record<string, unknown>
}

const BORDER: Record<NodeStatus, string> = {
  pending: 'border-gray-300',
  running: 'border-blue-500 status-pulse-running',
  success: 'border-green-500',
  failed: 'border-red-500',
  waiting: 'border-amber-500 status-pulse-waiting',
  cancelled: 'border-gray-400',
}

function WorkflowNode({ data }: NodeProps<WorkflowNodeData>) {
  const { label, status, metadata } = data
  return (
    <div
      className={`bg-white rounded-lg border-2 shadow-md px-4 py-3 w-56 ${BORDER[status]}`}
    >
      <Handle type="source" position={Position.Bottom} />
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">🔷</span>
        <span className="font-semibold text-gray-800 text-sm truncate flex-1">{label}</span>
      </div>
      <StatusBadge status={status} />
      {metadata.task_queue && (
        <div className="mt-1 text-xs text-gray-400 truncate">
          queue: {String(metadata.task_queue)}
        </div>
      )}
    </div>
  )
}

export default memo(WorkflowNode)

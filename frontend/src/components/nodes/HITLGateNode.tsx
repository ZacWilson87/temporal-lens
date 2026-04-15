import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'
import { StatusBadge } from '../StatusBadge'
import type { NodeStatus } from '../../lib/api'

interface HITLGateNodeData extends Record<string, unknown> {
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

function HITLGateNode({ data }: NodeProps<HITLGateNodeData>) {
  const { label, status } = data

  return (
    <div
      className={`bg-amber-50 rounded-md border-2 shadow px-3 py-2 w-52 ${BORDER[status]}`}
    >
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <div className="flex items-center gap-2 mb-1">
        <span className="text-base">🙋</span>
        <span className="font-medium text-amber-900 text-sm truncate flex-1">{label}</span>
      </div>
      <StatusBadge status={status} />
      <div className="mt-1 text-xs text-amber-600">
        {status === 'waiting' ? 'Awaiting human approval' : 'Human-in-the-loop gate'}
      </div>
    </div>
  )
}

export default memo(HITLGateNode)

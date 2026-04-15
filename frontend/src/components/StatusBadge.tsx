import type { NodeStatus } from '../lib/api'

interface Props {
  status: NodeStatus
  size?: 'sm' | 'md'
}

const LABEL: Record<NodeStatus, string> = {
  pending: 'pending',
  running: 'running',
  success: 'success',
  failed: 'failed',
  waiting: 'waiting',
  cancelled: 'cancelled',
}

const COLOR: Record<NodeStatus, string> = {
  pending: 'bg-gray-200 text-gray-700',
  running: 'bg-blue-100 text-blue-800',
  success: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  waiting: 'bg-amber-100 text-amber-800',
  cancelled: 'bg-gray-100 text-gray-500',
}

export function StatusBadge({ status, size = 'sm' }: Props) {
  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm'
  return (
    <span className={`inline-block rounded-full font-medium ${padding} ${COLOR[status]}`}>
      {LABEL[status]}
    </span>
  )
}

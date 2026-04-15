/**
 * Typed API client for temporal-lens backend.
 * All requests go to VITE_API_URL (default: http://localhost:8000).
 */

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) || 'http://localhost:8000'

export type NodeStatus = 'pending' | 'running' | 'success' | 'failed' | 'waiting' | 'cancelled'
export type NodeType = 'workflow' | 'activity' | 'llm_span' | 'hitl_gate' | 'opa_gate'
export type EdgeType = 'dependency' | 'spawn' | 'signal'

export interface GraphNode {
  id: string
  type: NodeType
  label: string
  status: NodeStatus
  metadata: Record<string, unknown>
  position: { x: number; y: number } | null
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  type: EdgeType
}

export interface GraphSnapshot {
  workflow_id: string
  workflow_name: string
  status: string
  nodes: GraphNode[]
  edges: GraphEdge[]
  snapshot_at: number
}

export interface WorkflowSummary {
  workflow_id: string
  run_id: string
  workflow_type: string
  status: string
  start_time: number | null
  close_time: number | null
  task_queue: string
}

export interface HealthStatus {
  status: string
  temporal: boolean
  langfuse: boolean
}

async function get<T>(path: string): Promise<T> {
  const url = `${BASE_URL}${path}`
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`GET ${url} → ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () => get<HealthStatus>('/health'),
  listWorkflows: (limit = 50) => get<WorkflowSummary[]>(`/workflows?limit=${limit}`),
  getWorkflow: (id: string) => get<WorkflowSummary>(`/workflows/${encodeURIComponent(id)}`),
  getGraph: (id: string) => get<GraphSnapshot>(`/workflows/${encodeURIComponent(id)}/graph`),
  graphStreamUrl: (id: string) =>
    `${BASE_URL}/workflows/${encodeURIComponent(id)}/graph/stream`,
}

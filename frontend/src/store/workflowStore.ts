/**
 * Zustand store — workflow list + selected workflow DAG state.
 */
import { create } from 'zustand'
import type { GraphSnapshot, WorkflowSummary, GraphNode } from '../lib/api'

interface WorkflowState {
  // Sidebar list
  workflows: WorkflowSummary[]
  workflowsLoading: boolean
  workflowsError: string | null
  setWorkflows: (ws: WorkflowSummary[]) => void
  setWorkflowsLoading: (v: boolean) => void
  setWorkflowsError: (e: string | null) => void

  // Selected workflow
  selectedWorkflowId: string | null
  selectWorkflow: (id: string | null) => void

  // DAG snapshot
  snapshot: GraphSnapshot | null
  setSnapshot: (s: GraphSnapshot) => void
  clearSnapshot: () => void

  // Selected node (for DetailPanel)
  selectedNode: GraphNode | null
  selectNode: (node: GraphNode | null) => void

  // Config modal (shown when backend is not yet configured)
  showConfigModal: boolean
  setShowConfigModal: (v: boolean) => void
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  workflows: [],
  workflowsLoading: false,
  workflowsError: null,
  setWorkflows: (ws) => set({ workflows: ws }),
  setWorkflowsLoading: (v) => set({ workflowsLoading: v }),
  setWorkflowsError: (e) => set({ workflowsError: e }),

  selectedWorkflowId: null,
  selectWorkflow: (id) => set({ selectedWorkflowId: id, selectedNode: null, snapshot: null }),

  snapshot: null,
  setSnapshot: (s) => set({ snapshot: s }),
  clearSnapshot: () => set({ snapshot: null }),

  selectedNode: null,
  selectNode: (node) => set({ selectedNode: node }),

  showConfigModal: false,
  setShowConfigModal: (v) => set({ showConfigModal: v }),
}))

/**
 * Main React Flow canvas — renders the DAG with dagre auto-layout.
 * Subscribes to the SSE stream and re-renders on each snapshot update.
 */
import { useCallback, useEffect, useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
} from '@xyflow/react'
import type { Node, Edge, Connection, NodeMouseHandler } from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { useWorkflowStore } from '../store/workflowStore'
import { useGraphStream } from '../hooks/useGraphStream'
import { applyDagreLayout } from '../lib/layout'
import type { GraphNode, GraphEdge } from '../lib/api'

import WorkflowNode from './nodes/WorkflowNode'
import ActivityNode from './nodes/ActivityNode'
import LLMSpanNode from './nodes/LLMSpanNode'
import HITLGateNode from './nodes/HITLGateNode'
import OPAGateNode from './nodes/OPAGateNode'

const nodeTypes = {
  workflow: WorkflowNode,
  activity: ActivityNode,
  llm_span: LLMSpanNode,
  hitl_gate: HITLGateNode,
  opa_gate: OPAGateNode,
}

function snapshotToFlow(
  graphNodes: GraphNode[],
  graphEdges: GraphEdge[],
): { nodes: Node[]; edges: Edge[] } {
  const rfNodes: Node[] = graphNodes.map((n) => ({
    id: n.id,
    type: n.type,
    position: n.position ?? { x: 0, y: 0 },
    data: {
      label: n.label,
      status: n.status,
      metadata: n.metadata,
    },
  }))

  const rfEdges: Edge[] = graphEdges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: 'smoothstep',
    markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
    style:
      e.type === 'signal'
        ? { stroke: '#f59e0b', strokeDasharray: '5 3' }
        : e.type === 'spawn'
        ? { stroke: '#a78bfa' }
        : { stroke: '#94a3b8' },
    label: e.type !== 'dependency' ? e.type : undefined,
  }))

  // Apply dagre layout
  const laidOut = applyDagreLayout(rfNodes, rfEdges)
  return { nodes: laidOut, edges: rfEdges }
}

export function DAGCanvas() {
  const { selectedWorkflowId, snapshot, selectNode } = useWorkflowStore()

  // Subscribe to the SSE stream for the selected workflow
  useGraphStream(selectedWorkflowId)

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  // Re-layout whenever the snapshot changes
  useEffect(() => {
    if (!snapshot) {
      setNodes([])
      setEdges([])
      return
    }
    const { nodes: newNodes, edges: newEdges } = snapshotToFlow(
      snapshot.nodes,
      snapshot.edges,
    )
    setNodes(newNodes)
    setEdges(newEdges)
  }, [snapshot, setNodes, setEdges])

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  )

  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      // Find the full GraphNode from the snapshot
      const gn = snapshot?.nodes.find((n) => n.id === node.id)
      if (gn) selectNode(gn)
    },
    [snapshot, selectNode],
  )

  if (!selectedWorkflowId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-4xl mb-3">🔭</div>
          <p className="text-gray-500 text-sm">Select a workflow to visualize its DAG</p>
        </div>
      </div>
    )
  }

  if (selectedWorkflowId && !snapshot) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-2xl mb-2 animate-pulse">⏳</div>
          <p className="text-gray-400 text-sm">Loading DAG…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={2}
      >
        <Background color="#e2e8f0" gap={20} />
        <Controls />
        <MiniMap
          nodeColor={(n) => {
            const status = (n.data as { status: string }).status
            const colors: Record<string, string> = {
              pending: '#d1d5db',
              running: '#3b82f6',
              success: '#22c55e',
              failed: '#ef4444',
              waiting: '#f59e0b',
              cancelled: '#9ca3af',
            }
            return colors[status] ?? '#d1d5db'
          }}
        />
      </ReactFlow>
    </div>
  )
}

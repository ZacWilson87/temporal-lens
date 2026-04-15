import { useEffect } from 'react'
import { WorkflowList } from './components/WorkflowList'
import { DAGCanvas } from './components/DAGCanvas'
import { DetailPanel } from './components/DetailPanel'
import { ConfigModal } from './components/ConfigModal'
import { useWorkflowStore } from './store/workflowStore'
import { api } from './lib/api'

function App() {
  const { selectedNode, setShowConfigModal } = useWorkflowStore()

  // On mount, check backend health; show config modal if not reachable
  useEffect(() => {
    api
      .health()
      .then((h) => {
        if (!h.temporal) {
          setShowConfigModal(true)
        }
      })
      .catch(() => setShowConfigModal(true))
  }, [setShowConfigModal])

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 h-10 bg-gray-900 text-white flex items-center px-4 z-10 gap-3">
        <span className="font-semibold text-sm tracking-tight">🔭 temporal-lens</span>
        <span className="text-gray-500 text-xs">Real-time AI agent DAG visualizer</span>
        <button
          onClick={() => setShowConfigModal(true)}
          className="ml-auto text-xs text-gray-400 hover:text-white"
        >
          Configure
        </button>
      </div>

      {/* Main layout below header */}
      <div className="flex flex-1 overflow-hidden mt-10">
        <WorkflowList />
        <DAGCanvas />
        {selectedNode && <DetailPanel />}
      </div>

      <ConfigModal />
    </div>
  )
}

export default App

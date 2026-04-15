/**
 * Config modal — shown when the backend cannot be reached.
 * Lets users set TEMPORAL_ADDRESS and LANGFUSE_HOST in localStorage
 * for demo/dev mode (these values are only used by the frontend to display,
 * not passed as query params; actual connection happens on the backend).
 */
import { useState } from 'react'
import { useWorkflowStore } from '../store/workflowStore'

export function ConfigModal() {
  const { showConfigModal, setShowConfigModal } = useWorkflowStore()
  const [temporalAddr, setTemporalAddr] = useState(
    () => localStorage.getItem('tl_temporal_address') ?? 'localhost:7233',
  )
  const [langfuseHost, setLangfuseHost] = useState(
    () => localStorage.getItem('tl_langfuse_host') ?? 'http://localhost:3000',
  )

  if (!showConfigModal) return null

  function save() {
    localStorage.setItem('tl_temporal_address', temporalAddr)
    localStorage.setItem('tl_langfuse_host', langfuseHost)
    setShowConfigModal(false)
    window.location.reload()
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold text-gray-800 mb-1">Configure temporal-lens</h2>
        <p className="text-sm text-gray-500 mb-4">
          These values are stored in localStorage for this session.
          In production, set them as environment variables on the backend container.
        </p>

        <label className="block mb-3">
          <span className="text-xs font-medium text-gray-600">TEMPORAL_ADDRESS</span>
          <input
            className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-400"
            value={temporalAddr}
            onChange={(e) => setTemporalAddr(e.target.value)}
          />
        </label>

        <label className="block mb-5">
          <span className="text-xs font-medium text-gray-600">LANGFUSE_HOST</span>
          <input
            className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-400"
            value={langfuseHost}
            onChange={(e) => setLangfuseHost(e.target.value)}
          />
        </label>

        <div className="flex justify-end gap-3">
          <button
            onClick={() => setShowConfigModal(false)}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            onClick={save}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Save & reload
          </button>
        </div>
      </div>
    </div>
  )
}

/**
 * Polls GET /workflows every 10 seconds and updates the Zustand store.
 */
import { useEffect } from 'react'
import { api } from '../lib/api'
import { useWorkflowStore } from '../store/workflowStore'

const REFRESH_INTERVAL_MS = 10_000

export function useWorkflows() {
  const { setWorkflows, setWorkflowsLoading, setWorkflowsError } = useWorkflowStore()

  useEffect(() => {
    let cancelled = false

    async function load() {
      setWorkflowsLoading(true)
      try {
        const data = await api.listWorkflows()
        if (!cancelled) {
          setWorkflows(data)
          setWorkflowsError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setWorkflowsError(err instanceof Error ? err.message : String(err))
        }
      } finally {
        if (!cancelled) setWorkflowsLoading(false)
      }
    }

    load()
    const timer = setInterval(load, REFRESH_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [setWorkflows, setWorkflowsLoading, setWorkflowsError])
}

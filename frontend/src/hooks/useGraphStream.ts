/**
 * Opens an SSE connection to /workflows/{id}/graph/stream.
 * On each event, diffs the incoming GraphSnapshot against current state
 * and updates the Zustand store. Closes when workflow reaches terminal state
 * or the selected workflow changes.
 */
import { useEffect, useRef } from 'react'
import { api } from '../lib/api'
import { useWorkflowStore } from '../store/workflowStore'
import type { GraphSnapshot } from '../lib/api'

const TERMINAL_STATUSES = new Set(['completed', 'failed', 'cancelled', 'terminated', 'timed_out'])

export function useGraphStream(workflowId: string | null) {
  const { setSnapshot, clearSnapshot } = useWorkflowStore()
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!workflowId) {
      clearSnapshot()
      return
    }

    // Close any existing connection
    if (esRef.current) {
      esRef.current.close()
      esRef.current = null
    }
    clearSnapshot()

    const url = api.graphStreamUrl(workflowId)
    const es = new EventSource(url)
    esRef.current = es

    es.onmessage = (event) => {
      try {
        const snapshot = JSON.parse(event.data) as GraphSnapshot
        setSnapshot(snapshot)

        // Once the workflow is terminal, close the stream
        if (TERMINAL_STATUSES.has(snapshot.status.toLowerCase())) {
          es.close()
          esRef.current = null
        }
      } catch (err) {
        console.error('SSE parse error', err)
      }
    }

    es.addEventListener('error', (event) => {
      console.warn('SSE stream error', event)
      // The browser will attempt reconnection automatically for EventSource
    })

    return () => {
      es.close()
      esRef.current = null
    }
  }, [workflowId, setSnapshot, clearSnapshot])
}

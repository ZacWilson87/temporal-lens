import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { WorkflowList } from '../WorkflowList'
import { useWorkflowStore } from '../../store/workflowStore'

// Prevent the useWorkflows hook from hitting the network
vi.mock('../../hooks/useWorkflows', () => ({
  useWorkflows: () => undefined,
}))

const WORKFLOWS = [
  {
    workflow_id: 'wf-001',
    run_id: 'run-001',
    workflow_type: 'OrderWorkflow',
    status: 'running',
    start_time: 1700000000,
    close_time: null,
    task_queue: 'default',
  },
  {
    workflow_id: 'wf-002',
    run_id: 'run-002',
    workflow_type: 'InferenceWorkflow',
    status: 'success',
    start_time: 1700000100,
    close_time: 1700000200,
    task_queue: 'default',
  },
]

beforeEach(() => {
  useWorkflowStore.setState({
    workflows: [],
    workflowsLoading: false,
    workflowsError: null,
    selectedWorkflowId: null,
  })
})

describe('WorkflowList', () => {
  it('shows empty state when no workflows', () => {
    render(<WorkflowList />)
    expect(screen.getByText(/No workflows found/)).toBeInTheDocument()
  })

  it('renders workflow type names from store', () => {
    useWorkflowStore.setState({ workflows: WORKFLOWS })
    render(<WorkflowList />)
    expect(screen.getByText('OrderWorkflow')).toBeInTheDocument()
    expect(screen.getByText('InferenceWorkflow')).toBeInTheDocument()
  })

  it('renders workflow IDs', () => {
    useWorkflowStore.setState({ workflows: WORKFLOWS })
    render(<WorkflowList />)
    expect(screen.getByText('wf-001')).toBeInTheDocument()
  })

  it('shows error banner when workflowsError is set', () => {
    useWorkflowStore.setState({ workflowsError: 'Connection refused' })
    render(<WorkflowList />)
    expect(screen.getByText('Connection refused')).toBeInTheDocument()
  })

  it('shows refreshing indicator when loading', () => {
    useWorkflowStore.setState({ workflowsLoading: true })
    render(<WorkflowList />)
    expect(screen.getByText(/refreshing/i)).toBeInTheDocument()
  })

  it('calls selectWorkflow when a workflow row is clicked', async () => {
    const user = userEvent.setup()
    useWorkflowStore.setState({ workflows: WORKFLOWS })
    render(<WorkflowList />)
    await user.click(screen.getByText('OrderWorkflow'))
    expect(useWorkflowStore.getState().selectedWorkflowId).toBe('wf-001')
  })
})

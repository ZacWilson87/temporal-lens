import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { StatusBadge } from '../StatusBadge'
import type { NodeStatus } from '../../lib/api'

const statuses: NodeStatus[] = ['pending', 'running', 'success', 'failed', 'waiting', 'cancelled']

describe('StatusBadge', () => {
  it.each(statuses)('renders label for status "%s"', (status) => {
    render(<StatusBadge status={status} />)
    expect(screen.getByText(status)).toBeInTheDocument()
  })

  it('applies sm padding by default', () => {
    render(<StatusBadge status="running" />)
    const badge = screen.getByText('running')
    expect(badge.className).toContain('text-xs')
  })

  it('applies md padding when size=md', () => {
    render(<StatusBadge status="running" size="md" />)
    const badge = screen.getByText('running')
    expect(badge.className).toContain('text-sm')
  })

  it('applies blue color for running status', () => {
    render(<StatusBadge status="running" />)
    const badge = screen.getByText('running')
    expect(badge.className).toContain('text-blue-800')
  })

  it('applies green color for success status', () => {
    render(<StatusBadge status="success" />)
    const badge = screen.getByText('success')
    expect(badge.className).toContain('text-green-800')
  })

  it('applies red color for failed status', () => {
    render(<StatusBadge status="failed" />)
    const badge = screen.getByText('failed')
    expect(badge.className).toContain('text-red-800')
  })

  it('applies amber color for waiting status', () => {
    render(<StatusBadge status="waiting" />)
    const badge = screen.getByText('waiting')
    expect(badge.className).toContain('text-amber-800')
  })
})

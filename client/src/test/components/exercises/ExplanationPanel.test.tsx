// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { ExplanationPanel } from '@/components/exercises/ExplanationPanel'

describe('ExplanationPanel', () => {
  it('renders nothing when explanation is null', () => {
    const { container } = render(<ExplanationPanel explanation={null} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('starts collapsed by default', () => {
    render(<ExplanationPanel explanation="<p>Grammar rule here</p>" />)
    expect(screen.queryByText(/grammar rule here/i)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /show explanation/i })).toBeInTheDocument()
  })

  it('shows explanation after clicking Show', async () => {
    const user = userEvent.setup()

    render(<ExplanationPanel explanation="<p>Grammar note</p>" />)

    await user.click(screen.getByRole('button', { name: /show explanation/i }))

    expect(screen.getByText('Grammar note')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /hide explanation/i })).toBeInTheDocument()
  })

  it('auto-opens when defaultOpen is true', () => {
    render(<ExplanationPanel explanation="<p>Auto-shown note</p>" defaultOpen />)
    expect(screen.getByText('Auto-shown note')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /hide explanation/i })).toBeInTheDocument()
  })

  it('collapses on second click', async () => {
    const user = userEvent.setup()

    render(<ExplanationPanel explanation="<p>Toggle me</p>" />)

    await user.click(screen.getByRole('button', { name: /show explanation/i }))
    await user.click(screen.getByRole('button', { name: /hide explanation/i }))

    expect(screen.queryByText(/toggle me/i)).not.toBeInTheDocument()
  })
})

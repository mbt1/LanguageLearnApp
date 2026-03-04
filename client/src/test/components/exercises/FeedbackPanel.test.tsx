// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { FeedbackPanel } from '@/components/exercises/FeedbackPanel'

describe('FeedbackPanel', () => {
  it('shows correct message when answer is correct', () => {
    render(
      <FeedbackPanel
        correct={true}
        correctAnswer="hola"
        normalizedUserAnswer="hola"
        onNext={vi.fn()}
      />,
    )
    expect(screen.getByText(/correct/i)).toBeInTheDocument()
    expect(screen.queryByText(/correct answer/i)).not.toBeInTheDocument()
  })

  it('shows correct answer when answer is incorrect', () => {
    render(
      <FeedbackPanel
        correct={false}
        correctAnswer="hola"
        normalizedUserAnswer="hello"
        onNext={vi.fn()}
      />,
    )
    expect(screen.getByText(/incorrect/i)).toBeInTheDocument()
    expect(screen.getByText('hola')).toBeInTheDocument()
    expect(screen.getByText(/your answer/i)).toBeInTheDocument()
  })

  it('calls onNext when feedback box is clicked', async () => {
    const user = userEvent.setup()
    const onNext = vi.fn()

    render(
      <FeedbackPanel
        correct={true}
        correctAnswer="hola"
        normalizedUserAnswer="hola"
        onNext={onNext}
      />,
    )

    await user.click(screen.getByRole('button', { name: /click to continue/i }))

    expect(onNext).toHaveBeenCalled()
  })
})

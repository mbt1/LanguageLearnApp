// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { SessionSummary } from '@/components/exercises/SessionSummary'
import type { ExerciseSubmitResponse } from '@/api/types'

function makeResult(overrides: Partial<ExerciseSubmitResponse> = {}): ExerciseSubmitResponse {
  return {
    correct: true,
    correct_answer: 'hola',
    normalized_user_answer: 'hola',
    new_exercise_difficulty: 'multiple_choice',
    consecutive_correct: 1,
    is_mastered: false,
    fsrs_due: null,
    difficulty_advanced: false,
    mastery_changed: false,
    ...overrides,
  }
}

describe('SessionSummary', () => {
  it('shows accuracy percentage', () => {
    const results = [
      makeResult({ correct: true }),
      makeResult({ correct: true }),
      makeResult({ correct: false }),
    ]
    render(<SessionSummary results={results} onFinish={vi.fn()} />)
    expect(screen.getByText('67%')).toBeInTheDocument()
  })

  it('shows concept count', () => {
    const results = [makeResult(), makeResult(), makeResult()]
    render(<SessionSummary results={results} onFinish={vi.fn()} />)
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText(/concepts reviewed/i)).toBeInTheDocument()
  })

  it('shows difficulty advancement count', () => {
    const results = [
      makeResult({ difficulty_advanced: true }),
      makeResult({ difficulty_advanced: true }),
      makeResult({ difficulty_advanced: false }),
    ]
    render(<SessionSummary results={results} onFinish={vi.fn()} />)
    // "2 concepts advanced to a harder exercise type."
    expect(screen.getByText(/advanced to a harder exercise type/i)).toBeInTheDocument()
  })

  it('shows newly mastered count', () => {
    const results = [
      makeResult({ mastery_changed: true, is_mastered: true }),
      makeResult({ mastery_changed: false, is_mastered: false }),
    ]
    render(<SessionSummary results={results} onFinish={vi.fn()} />)
    expect(screen.getByText(/newly mastered/i)).toBeInTheDocument()
  })

  it('calls onFinish when Back to Courses is clicked', async () => {
    const user = userEvent.setup()
    const onFinish = vi.fn()

    render(<SessionSummary results={[makeResult()]} onFinish={onFinish} />)

    await user.click(screen.getByRole('button', { name: /back to courses/i }))

    expect(onFinish).toHaveBeenCalled()
  })

  it('shows 100% accuracy when all correct', () => {
    const results = [makeResult({ correct: true }), makeResult({ correct: true })]
    render(<SessionSummary results={results} onFinish={vi.fn()} />)
    expect(screen.getByText('100%')).toBeInTheDocument()
  })
})

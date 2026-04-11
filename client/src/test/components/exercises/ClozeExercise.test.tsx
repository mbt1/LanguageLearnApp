// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ClozeExercise } from '@/components/exercises/ClozeExercise'

describe('ClozeExercise', () => {
  it('renders the sentence parts around the input', () => {
    render(<ClozeExercise sentenceTemplate="Yo ___ una manzana." onAnswer={vi.fn()} />)
    expect(screen.getByText(/Yo/)).toBeInTheDocument()
    expect(screen.getByText(/una manzana\./)).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('calls onAnswer with trimmed input when Enter is pressed', async () => {
    const user = userEvent.setup()
    const onAnswer = vi.fn()

    render(<ClozeExercise sentenceTemplate="Yo ___ esto." onAnswer={onAnswer} />)

    await user.type(screen.getByRole('textbox'), 'como{Enter}')

    expect(onAnswer).toHaveBeenCalledWith('como')
  })

  it('calls onAnswer on Submit button click', async () => {
    const user = userEvent.setup()
    const onAnswer = vi.fn()

    render(<ClozeExercise sentenceTemplate="Ella ___ aquí." onAnswer={onAnswer} />)

    await user.type(screen.getByRole('textbox'), 'está')
    await user.click(screen.getByRole('button', { name: /submit/i }))

    expect(onAnswer).toHaveBeenCalledWith('está')
  })

  it('disables input and hides submit button after submission', async () => {
    const user = userEvent.setup()

    render(<ClozeExercise sentenceTemplate="Él ___ allí." onAnswer={vi.fn()} />)

    await user.type(screen.getByRole('textbox'), 'está')
    await user.click(screen.getByRole('button', { name: /submit/i }))

    expect(screen.getByRole('textbox')).toBeDisabled()
    expect(screen.queryByRole('button', { name: /submit/i })).not.toBeInTheDocument()
  })
})

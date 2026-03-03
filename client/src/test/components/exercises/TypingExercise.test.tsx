// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { TypingExercise } from '@/components/exercises/TypingExercise'

describe('TypingExercise', () => {
  it('renders the prompt', () => {
    render(<TypingExercise prompt="Translate: hello" onAnswer={vi.fn()} />)
    expect(screen.getByText('Translate: hello')).toBeInTheDocument()
  })

  it('calls onAnswer with trimmed value when Enter is pressed', async () => {
    const user = userEvent.setup()
    const onAnswer = vi.fn()

    render(<TypingExercise prompt="Translate: hello" onAnswer={onAnswer} />)

    await user.type(screen.getByRole('textbox'), '  hola  {Enter}')

    expect(onAnswer).toHaveBeenCalledWith('hola')
  })

  it('calls onAnswer when Submit button is clicked', async () => {
    const user = userEvent.setup()
    const onAnswer = vi.fn()

    render(<TypingExercise prompt="Translate: goodbye" onAnswer={onAnswer} />)

    await user.type(screen.getByRole('textbox'), 'adiós')
    await user.click(screen.getByRole('button', { name: /submit/i }))

    expect(onAnswer).toHaveBeenCalledWith('adiós')
  })

  it('disables input and button after submission', async () => {
    const user = userEvent.setup()

    render(<TypingExercise prompt="Translate: yes" onAnswer={vi.fn()} />)

    await user.type(screen.getByRole('textbox'), 'sí')
    await user.click(screen.getByRole('button', { name: /submit/i }))

    expect(screen.getByRole('textbox')).toBeDisabled()
    expect(screen.getByRole('button', { name: /submit/i })).toBeDisabled()
  })
})

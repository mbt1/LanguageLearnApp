// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { MultipleChoiceExercise } from '@/components/exercises/MultipleChoiceExercise'

describe('MultipleChoiceExercise', () => {
  it('renders the prompt', () => {
    render(
      <MultipleChoiceExercise
        prompt="What is 'hello' in Spanish?"
        options={['hola', 'adiós', 'gracias', 'por favor']}
        onAnswer={vi.fn()}
      />,
    )
    expect(screen.getByText("What is 'hello' in Spanish?")).toBeInTheDocument()
  })

  it('renders all options as buttons', () => {
    render(
      <MultipleChoiceExercise
        prompt="Translate"
        options={['hola', 'adiós', 'gracias', 'por favor']}
        onAnswer={vi.fn()}
      />,
    )
    expect(screen.getByRole('button', { name: 'hola' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'adiós' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'gracias' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'por favor' })).toBeInTheDocument()
  })

  it('calls onAnswer with the clicked option', async () => {
    const user = userEvent.setup()
    const onAnswer = vi.fn()

    render(
      <MultipleChoiceExercise
        prompt="Translate"
        options={['hola', 'adiós', 'gracias']}
        onAnswer={onAnswer}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'hola' }))

    expect(onAnswer).toHaveBeenCalledWith('hola')
  })

  it('disables all buttons after selection', async () => {
    const user = userEvent.setup()

    render(
      <MultipleChoiceExercise
        prompt="Translate"
        options={['hola', 'adiós']}
        onAnswer={vi.fn()}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'hola' }))

    expect(screen.getByRole('button', { name: 'adiós' })).toBeDisabled()
  })
})

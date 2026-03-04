// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useEffect } from 'react'

interface FeedbackPanelProps {
  correct: boolean
  correctAnswer: string
  normalizedUserAnswer: string
  onNext: () => void
}

export function FeedbackPanel({
  correct,
  correctAnswer,
  normalizedUserAnswer,
  onNext,
}: FeedbackPanelProps) {
  // Allow Enter / Space / click anywhere to advance
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        onNext()
      }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onNext])

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={correct ? 'Correct — click to continue' : 'Incorrect — click to continue'}
      onClick={onNext}
      className={`cursor-pointer rounded-lg border p-4 transition-opacity hover:opacity-90 ${
        correct
          ? 'border-green-300 bg-green-50 dark:border-green-700 dark:bg-green-950'
          : 'border-red-300 bg-red-50 dark:border-red-700 dark:bg-red-950'
      }`}
    >
      <p className="text-lg font-semibold">
        {correct ? '✓ Correct!' : '✗ Incorrect'}
      </p>
      {!correct && (
        <p className="mt-1 text-sm">
          Correct answer:{' '}
          <span className="font-medium">{correctAnswer}</span>
        </p>
      )}
      {!correct && normalizedUserAnswer && (
        <p className="mt-1 text-sm text-muted-foreground">
          Your answer: {normalizedUserAnswer}
        </p>
      )}
      <p className="text-muted-foreground mt-2 text-xs">Click or press Enter to continue</p>
    </div>
  )
}

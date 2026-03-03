// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useEffect } from 'react'

import { Button } from '@/components/ui/button'

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
  // Allow Enter key to advance
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Enter') onNext()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onNext])

  return (
    <div
      className={`rounded-lg border p-4 ${
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
      <Button className="mt-3" onClick={onNext}>
        Next
      </Button>
    </div>
  )
}

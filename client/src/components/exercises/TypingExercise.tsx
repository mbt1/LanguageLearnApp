// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

interface TypingExerciseProps {
  prompt: string
  onAnswer: (answer: string) => void
  feedback?: { correct: boolean } | null
}

export function TypingExercise({ prompt, onAnswer, feedback }: TypingExerciseProps) {
  const [value, setValue] = useState('')
  const [submitted, setSubmitted] = useState(false)

  function submit() {
    if (submitted || !value.trim()) return
    setSubmitted(true)
    onAnswer(value.trim())
  }

  const inputColor = feedback
    ? feedback.correct
      ? 'border-green-600 ring-1 ring-green-600'
      : 'border-red-600 ring-1 ring-red-600'
    : ''

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="pt-6">
          <p className="text-lg font-medium">{prompt}</p>
        </CardContent>
      </Card>
      <div className="flex flex-col gap-2 sm:flex-row">
        <Input
          aria-label="Your answer"
          value={value}
          onChange={(e) => { setValue(e.target.value); }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') submit()
          }}
          disabled={submitted}
          placeholder="Type your answer…"
          autoFocus
          className={inputColor}
        />
        {!submitted && (
          <Button aria-label="Submit answer" onClick={submit} disabled={!value.trim()}>
            Submit
          </Button>
        )}
      </div>
    </div>
  )
}

// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'

interface ClozeExerciseProps {
  sentenceTemplate: string
  onAnswer: (answer: string) => void
  feedback?: { correct: boolean } | null
}

export function ClozeExercise({ sentenceTemplate, onAnswer, feedback }: ClozeExerciseProps) {
  const [value, setValue] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const parts = sentenceTemplate.split('___')
  const before = parts[0] ?? ''
  const after = parts[1] ?? ''

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
          <p className="text-lg font-medium">
            {before}
            <Input
              ref={inputRef}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') submit()
              }}
              aria-label="Fill in the blank"
              disabled={submitted}
              className={`mx-2 inline-block min-w-16 max-w-48 ${inputColor}`}
              autoFocus
            />
            {after}
          </p>
        </CardContent>
      </Card>
      {!submitted && (
        <Button onClick={submit} disabled={!value.trim()}>
          Submit
        </Button>
      )}
    </div>
  )
}

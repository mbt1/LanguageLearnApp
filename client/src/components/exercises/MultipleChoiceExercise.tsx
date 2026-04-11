// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

interface MultipleChoiceExerciseProps {
  prompt: string
  options: string[]
  onAnswer: (answer: string) => void
  feedback?: { correct: boolean; correctAnswer: string } | null
}

export function MultipleChoiceExercise({
  prompt,
  options,
  onAnswer,
  feedback,
}: MultipleChoiceExerciseProps) {
  const [selected, setSelected] = useState<string | null>(null)

  function handleSelect(option: string) {
    if (selected !== null) return
    setSelected(option)
    onAnswer(option)
  }

  function buttonVariant(option: string) {
    if (!feedback || selected === null) {
      // Pre-feedback: highlight selected
      return selected === option ? 'default' : 'outline'
    }
    // Post-feedback: color by correctness
    if (option === selected && feedback.correct) return 'default' // will get green class
    if (option === selected && !feedback.correct) return 'default' // will get red class
    if (option === feedback.correctAnswer && !feedback.correct) return 'default' // show correct
    return 'outline'
  }

  function buttonColor(option: string): string {
    if (!feedback || selected === null) return ''
    if (option === selected && feedback.correct) {
      return 'bg-green-600 hover:bg-green-600 border-green-600 text-white'
    }
    if (option === selected && !feedback.correct) {
      return 'bg-red-600 hover:bg-red-600 border-red-600 text-white'
    }
    if (option === feedback.correctAnswer && !feedback.correct) {
      return 'bg-green-600 hover:bg-green-600 border-green-600 text-white'
    }
    return ''
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="pt-6">
          <p className="text-lg font-medium">{prompt}</p>
        </CardContent>
      </Card>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {options.map((option) => (
          <Button
            key={option}
            aria-label={option}
            variant={buttonVariant(option)}
            disabled={selected !== null}
            onClick={() => {
              handleSelect(option)
            }}
            className={`h-auto min-h-10 py-2 text-left ${buttonColor(option)}`}
          >
            {option}
          </Button>
        ))}
      </div>
    </div>
  )
}

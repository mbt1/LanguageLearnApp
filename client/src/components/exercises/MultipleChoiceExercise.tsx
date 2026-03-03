// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

interface MultipleChoiceExerciseProps {
  prompt: string
  options: string[]
  onAnswer: (answer: string) => void
}

export function MultipleChoiceExercise({ prompt, options, onAnswer }: MultipleChoiceExerciseProps) {
  const [selected, setSelected] = useState<string | null>(null)

  function handleSelect(option: string) {
    if (selected !== null) return
    setSelected(option)
    onAnswer(option)
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
            variant={selected === option ? 'default' : 'outline'}
            disabled={selected !== null}
            onClick={() => handleSelect(option)}
            className="h-auto min-h-10 py-2 text-left"
          >
            {option}
          </Button>
        ))}
      </div>
    </div>
  )
}

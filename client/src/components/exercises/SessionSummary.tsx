// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import type { ExerciseSubmitResponse } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface SessionSummaryProps {
  results: ExerciseSubmitResponse[]
  onFinish: () => void
}

export function SessionSummary({ results, onFinish }: SessionSummaryProps) {
  const total = results.length
  const correct = results.filter((r) => r.correct).length
  const accuracyPct = total > 0 ? Math.round((correct / total) * 100) : 0
  const advancedCount = results.filter((r) => r.difficulty_advanced).length
  const masteredCount = results.filter((r) => r.mastery_changed && r.is_mastered).length

  return (
    <Card className="mx-auto max-w-lg">
      <CardHeader>
        <CardTitle>Session complete!</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2">
          <div>
            <p className="text-3xl font-bold">{accuracyPct}%</p>
            <p className="text-muted-foreground text-sm">Accuracy</p>
          </div>
          <div>
            <p className="text-3xl font-bold">{total}</p>
            <p className="text-muted-foreground text-sm">
              {total === 1 ? 'Concept' : 'Concepts'} reviewed
            </p>
          </div>
        </div>

        {advancedCount > 0 && (
          <p className="text-sm">
            <span className="font-medium">{advancedCount}</span>{' '}
            {advancedCount === 1 ? 'concept' : 'concepts'} advanced to a harder exercise type.
          </p>
        )}

        {masteredCount > 0 && (
          <p className="text-sm">
            <span className="font-medium">{masteredCount}</span>{' '}
            {masteredCount === 1 ? 'concept' : 'concepts'} newly mastered!
          </p>
        )}

        <Button className="w-full" onClick={onFinish}>
          Back to Courses
        </Button>
      </CardContent>
    </Card>
  )
}

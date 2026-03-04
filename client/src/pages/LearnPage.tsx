// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { getErrorMessage } from '@/api/client'
import { submitExercise, studySession } from '@/api/study'
import type { ExerciseSubmitResponse, StudySessionItem, StudySessionResponse } from '@/api/types'
import { ClozeExercise } from '@/components/exercises/ClozeExercise'
import { ExplanationPanel } from '@/components/exercises/ExplanationPanel'
import { FeedbackPanel } from '@/components/exercises/FeedbackPanel'
import { MultipleChoiceExercise } from '@/components/exercises/MultipleChoiceExercise'
import { SessionSummary } from '@/components/exercises/SessionSummary'
import { TypingExercise } from '@/components/exercises/TypingExercise'
import { Card, CardContent } from '@/components/ui/card'

type State = 'loading' | 'exercise' | 'feedback' | 'summary' | 'error'

export function LearnPage() {
  const { courseId } = useParams<{ courseId: string }>()
  const navigate = useNavigate()

  const [state, setState] = useState<State>('loading')
  const [session, setSession] = useState<StudySessionResponse | null>(null)
  const [index, setIndex] = useState(0)
  const [results, setResults] = useState<ExerciseSubmitResponse[]>([])
  const [lastResult, setLastResult] = useState<ExerciseSubmitResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!courseId) return
    const sessionSize = parseInt(localStorage.getItem('sessionSize') ?? '20', 10)

    studySession(courseId, sessionSize)
      .then((s) => {
        setSession(s)
        if (s.items.length === 0) {
          setState('summary')
        } else {
          setState('exercise')
        }
      })
      .catch((err: unknown) => {
        setError(getErrorMessage(err, 'Failed to load session. Please try again.'))
        setState('error')
      })
  }, [courseId])

  function currentItem(): StudySessionItem | null {
    return session?.items[index] ?? null
  }

  async function handleAnswer(userAnswer: string) {
    const item = currentItem()
    if (!item) return

    try {
      const result = await submitExercise({
        concept_id: item.concept_id,
        exercise_type: item.exercise_type,
        user_answer: userAnswer,
        ...(item.exercise_id ? { exercise_id: item.exercise_id } : {}),
      })
      setLastResult(result)
      setResults((prev) => [...prev, result])
      setState('feedback')
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to submit answer. Please try again.'))
      setState('error')
    }
  }

  function handleNext() {
    const nextIndex = index + 1
    if (!session || nextIndex >= session.items.length) {
      setState('summary')
    } else {
      setIndex(nextIndex)
      setLastResult(null)
      setState('exercise')
    }
  }

  function handleFinish() {
    void navigate('/')
  }

  if (state === 'loading') {
    return (
      <p role="status" aria-live="polite" className="text-muted-foreground">
        Loading session...
      </p>
    )
  }

  if (state === 'error') {
    return <p className="text-destructive">{error}</p>
  }

  if (state === 'summary') {
    return <SessionSummary results={results} onFinish={handleFinish} />
  }

  const item = currentItem()
  if (!item) return null

  const isGrammar = item.concept_type === 'grammar'
  // Auto-open explanation for grammar concepts on first encounter in this session
  const hasSeenConceptBefore = session?.items.slice(0, index).some(
    (i) => i.concept_id === item.concept_id,
  )
  const autoOpenExplanation = isGrammar && !hasSeenConceptBefore

  const progress = session ? `${index + 1} / ${session.items.length}` : ''

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-muted-foreground text-sm">{progress}</p>
      </div>

      {state === 'exercise' && (
        <>
          {item.exercise_type === 'multiple_choice' && (
            <MultipleChoiceExercise
              prompt={item.prompt}
              options={shuffled([...(item.distractors ?? []), item.correct_answer ?? item.target])}
              onAnswer={(a) => void handleAnswer(a)}
            />
          )}
          {item.exercise_type === 'cloze' && item.sentence_template && (
            <ClozeExercise
              sentenceTemplate={item.sentence_template}
              onAnswer={(a) => void handleAnswer(a)}
            />
          )}
          {(item.exercise_type === 'typing' || item.exercise_type === 'reverse_typing') && (
            <TypingExercise
              prompt={item.prompt}
              onAnswer={(a) => void handleAnswer(a)}
            />
          )}
          <ExplanationPanel
            explanation={item.explanation ?? null}
            defaultOpen={autoOpenExplanation}
          />
        </>
      )}

      {state === 'feedback' && lastResult && (
        <>
          <Card>
            <CardContent className="pt-6">
              <p className="text-lg font-medium">{item.prompt}</p>
            </CardContent>
          </Card>
          <FeedbackPanel
            correct={lastResult.correct}
            correctAnswer={lastResult.correct_answer}
            normalizedUserAnswer={lastResult.normalized_user_answer}
            onNext={handleNext}
          />
          <ExplanationPanel
            explanation={item.explanation ?? null}
          />
        </>
      )}
    </div>
  )
}

function shuffled<T>(arr: T[]): T[] {
  const copy = [...arr]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j]!, copy[i]!]
  }
  return copy
}

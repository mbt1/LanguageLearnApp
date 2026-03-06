// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { getErrorMessage } from '@/api/client'
import { submitExercise, studySession } from '@/api/study'
import type { ExerciseSubmitResponse, StudySessionResponse } from '@/api/types'
import { ClozeExercise } from '@/components/exercises/ClozeExercise'
import { ExplanationPanel } from '@/components/exercises/ExplanationPanel'
import { FeedbackPanel } from '@/components/exercises/FeedbackPanel'
import { MultipleChoiceExercise } from '@/components/exercises/MultipleChoiceExercise'
import { SessionSummary } from '@/components/exercises/SessionSummary'
import { TypingExercise } from '@/components/exercises/TypingExercise'
import { Button } from '@/components/ui/button'

type State = 'loading' | 'exercise' | 'feedback' | 'summary' | 'error'

export function LearnPage() {
  const { courseId } = useParams<{ courseId: string }>()
  const [searchParams] = useSearchParams()
  const conceptId = searchParams.get('conceptId')
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

    const conceptIds = conceptId ? [conceptId] : undefined
    studySession(courseId, sessionSize, conceptIds)
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
  }, [courseId, conceptId])

  async function handleAnswer(userAnswer: string) {
    const current = session?.items[index]
    if (!current) return

    try {
      const result = await submitExercise({
        concept_id: current.concept_id,
        exercise_type: current.exercise_type,
        user_answer: userAnswer,
        ...(current.exercise_id ? { exercise_id: current.exercise_id } : {}),
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
    void navigate(conceptId ? '/review-schedule' : '/')
  }

  function handleCancel() {
    void navigate(conceptId ? '/review-schedule' : '/')
  }

  // Memoize MC options so they don't reshuffle on exercise→feedback transition
  const item = session?.items[index] ?? null
  const isForward = item?.exercise_type === 'forward_mc' || item?.exercise_type === 'cloze' || item?.exercise_type === 'forward_typing'
  const prompt = item ? (isForward ? item.source_text : item.target_text) : ''
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const mcOptions = useMemo(() => {
    if (!item || (item.exercise_type !== 'forward_mc' && item.exercise_type !== 'reverse_mc')) return []
    const answer = item.correct_answer ?? (isForward ? item.target_text : item.source_text)
    return shuffled([...(item.distractors ?? []), answer])
  }, [index, session])

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

  if (!item) return null

  const isGrammar = item.concept_type === 'grammar'
  // Auto-open explanation for grammar concepts on first encounter in this session
  const hasSeenConceptBefore = session?.items.slice(0, index).some(
    (i) => i.concept_id === item.concept_id,
  )
  const autoOpenExplanation = isGrammar && !hasSeenConceptBefore

  const progress = session ? `${index + 1} / ${session.items.length}` : ''
  const showingFeedback = state === 'feedback' && lastResult !== null
  const feedbackData = showingFeedback ? lastResult : null

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-muted-foreground text-sm">{progress}</p>
        {state === 'exercise' && (
          <Button variant="ghost" size="sm" onClick={handleCancel}>
            Cancel
          </Button>
        )}
      </div>

      {(item.exercise_type === 'forward_mc' || item.exercise_type === 'reverse_mc') && (
        <MultipleChoiceExercise
          key={index}
          prompt={prompt}
          options={mcOptions}
          onAnswer={(a) => void handleAnswer(a)}
          feedback={feedbackData ? { correct: feedbackData.correct, correctAnswer: feedbackData.correct_answer } : null}
        />
      )}
      {(item.exercise_type === 'cloze' || item.exercise_type === 'reverse_cloze') && item.sentence_template && (
        <ClozeExercise
          key={index}
          sentenceTemplate={item.sentence_template}
          onAnswer={(a) => void handleAnswer(a)}
          feedback={feedbackData ? { correct: feedbackData.correct } : null}
        />
      )}
      {(item.exercise_type === 'forward_typing' || item.exercise_type === 'reverse_typing') && (
        <TypingExercise
          key={index}
          prompt={prompt}
          onAnswer={(a) => void handleAnswer(a)}
          feedback={feedbackData ? { correct: feedbackData.correct } : null}
        />
      )}

      {showingFeedback && (
        <FeedbackPanel
          correct={lastResult.correct}
          correctAnswer={lastResult.correct_answer}
          normalizedUserAnswer={lastResult.normalized_user_answer}
          onNext={handleNext}
        />
      )}

      <ExplanationPanel
        explanation={item.explanation ?? null}
        defaultOpen={!showingFeedback ? autoOpenExplanation : undefined}
      />
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

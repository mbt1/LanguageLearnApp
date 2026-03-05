// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  apiRequest: vi.fn(),
  cachedGet: vi.fn(),
  invalidateCache: vi.fn(),
}))

import { getCourseProgress, getReviewSchedule, studySession, submitExercise } from '@/api/study'
import { apiRequest, cachedGet } from '@/api/client'

const mockApiRequest = vi.mocked(apiRequest)
const mockCachedGet = vi.mocked(cachedGet)

describe('studySession', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('posts to /v1/study/session with course_id', async () => {
    mockApiRequest.mockResolvedValueOnce({ items: [], total_due_reviews: 0, new_concepts_added: 0 })

    await studySession('course-abc')

    expect(mockApiRequest).toHaveBeenCalledWith('/v1/study/session', {
      method: 'POST',
      body: JSON.stringify({ course_id: 'course-abc' }),
    })
  })

  it('includes session_size when provided', async () => {
    mockApiRequest.mockResolvedValueOnce({ items: [], total_due_reviews: 0, new_concepts_added: 0 })

    await studySession('course-abc', 10)

    expect(mockApiRequest).toHaveBeenCalledWith('/v1/study/session', {
      method: 'POST',
      body: JSON.stringify({ course_id: 'course-abc', session_size: 10 }),
    })
  })
})

describe('submitExercise', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('posts to /v1/exercises/submit with request body', async () => {
    const req = {
      concept_id: 'concept-1',
      exercise_type: 'multiple_choice' as const,
      user_answer: 'hola',
    }
    mockApiRequest.mockResolvedValueOnce({
      correct: true,
      correct_answer: 'hola',
      normalized_user_answer: 'hola',
      new_exercise_difficulty: 'multiple_choice',
      consecutive_correct: 1,
      is_mastered: false,
      fsrs_due: null,
      difficulty_advanced: false,
      mastery_changed: false,
    })

    const result = await submitExercise(req)

    expect(mockApiRequest).toHaveBeenCalledWith('/v1/exercises/submit', {
      method: 'POST',
      body: JSON.stringify(req),
    })
    expect(result.correct).toBe(true)
  })
})

describe('getCourseProgress', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('gets from /v1/progress/:courseId', async () => {
    mockCachedGet.mockResolvedValueOnce({ course_id: 'course-1', items: [] })

    await getCourseProgress('course-1')

    expect(mockCachedGet).toHaveBeenCalledWith('/v1/progress/course-1')
  })
})

describe('getReviewSchedule', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('gets from /v1/review-schedule/:courseId', async () => {
    mockApiRequest.mockResolvedValueOnce({ course_id: 'course-1', items: [] })

    await getReviewSchedule('course-1')

    expect(mockApiRequest).toHaveBeenCalledWith('/v1/review-schedule/course-1')
  })
})

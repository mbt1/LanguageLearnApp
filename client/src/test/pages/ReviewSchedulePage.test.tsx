// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ReviewSchedulePage } from '@/pages/ReviewSchedulePage'

vi.mock('@/api/courses', () => ({
  listCourses: vi.fn(),
}))

vi.mock('@/api/study', () => ({
  getReviewSchedule: vi.fn(),
}))

import * as coursesApi from '@/api/courses'
import * as studyApi from '@/api/study'

const mockCourse = {
  id: 'course-1',
  slug: 'spanish-basics',
  title: 'Spanish Basics',
  source_language: 'en',
  target_language: 'es',
  created_at: '2026-01-01T00:00:00Z',
}

function renderPage() {
  return render(
    <MemoryRouter>
      <ReviewSchedulePage />
    </MemoryRouter>,
  )
}

describe('ReviewSchedulePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state', () => {
    vi.mocked(coursesApi.listCourses).mockReturnValue(new Promise(() => {}))

    renderPage()

    expect(screen.getByText(/loading review schedule/i)).toBeInTheDocument()
  })

  it('shows error state', async () => {
    vi.mocked(coursesApi.listCourses).mockRejectedValue(new Error('Network error'))

    renderPage()

    expect(await screen.findByText(/failed to load review schedule/i)).toBeInTheDocument()
  })

  it('shows empty state when no concepts started', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getReviewSchedule).mockResolvedValue({
      course_id: 'course-1',
      items: [],
    })

    renderPage()

    expect(await screen.findByText('Spanish Basics')).toBeInTheDocument()
    expect(screen.getByText(/no concepts started/i)).toBeInTheDocument()
  })

  it('displays concept data in the table', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getReviewSchedule).mockResolvedValue({
      course_id: 'course-1',
      items: [
        {
          concept_id: 'c1',
          prompt: 'hello',
          target: 'hola',
          concept_type: 'vocabulary',
          cefr_level: 'A1',
          current_exercise_difficulty: 'multiple_choice',
          consecutive_correct: 3,
          is_mastered: false,
          fsrs_state: 'review',
          fsrs_stability: 5.2,
          fsrs_difficulty: 3.1,
          fsrs_due: '2026-03-10T12:00:00Z',
          fsrs_last_review: '2026-03-01T10:00:00Z',
        },
      ],
    })

    renderPage()

    expect(await screen.findByText('hello')).toBeInTheDocument()
    expect(screen.getByText('hola')).toBeInTheDocument()
    expect(screen.getByText('A1')).toBeInTheDocument()
    expect(screen.getByText('MC')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('5.2')).toBeInTheDocument()
    expect(screen.getByText('3.1')).toBeInTheDocument()
    expect(screen.getByText('1 concept started')).toBeInTheDocument()
  })

  it('highlights overdue items', async () => {
    const pastDate = '2020-01-01T00:00:00Z'
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getReviewSchedule).mockResolvedValue({
      course_id: 'course-1',
      items: [
        {
          concept_id: 'c1',
          prompt: 'hello',
          target: 'hola',
          concept_type: 'vocabulary',
          cefr_level: 'A1',
          current_exercise_difficulty: 'typing',
          consecutive_correct: 5,
          is_mastered: true,
          fsrs_state: 'review',
          fsrs_stability: 10.0,
          fsrs_difficulty: 2.0,
          fsrs_due: pastDate,
          fsrs_last_review: '2019-12-01T10:00:00Z',
        },
      ],
    })

    renderPage()

    await screen.findByText('hello')
    // The due date span should have the orange overdue class
    const dueCell = screen.getByText((_, el) => {
      return el?.tagName === 'SPAN' && el.className.includes('text-orange-500') || false
    })
    expect(dueCell).toBeInTheDocument()
  })
})

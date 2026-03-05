// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { fireEvent, render, screen, within } from '@testing-library/react'
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

const startedConcept = {
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
}

const unstartedConcept = {
  concept_id: 'c2',
  prompt: 'goodbye',
  target: 'adiós',
  concept_type: 'vocabulary',
  cefr_level: 'A1',
  current_exercise_difficulty: null,
  consecutive_correct: null,
  is_mastered: null,
  fsrs_state: null,
  fsrs_stability: null,
  fsrs_difficulty: null,
  fsrs_due: null,
  fsrs_last_review: null,
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

  it('shows empty state when no concepts', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getReviewSchedule).mockResolvedValue({
      course_id: 'course-1',
      items: [],
    })

    renderPage()

    expect(await screen.findByText('Spanish Basics')).toBeInTheDocument()
    expect(screen.getByText(/no concepts in this course/i)).toBeInTheDocument()
  })

  it('displays concept data in the table', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getReviewSchedule).mockResolvedValue({
      course_id: 'course-1',
      items: [startedConcept],
    })

    renderPage()

    expect(await screen.findByText('hello')).toBeInTheDocument()
    // A1 appears in both the badge and filter option; check the badge specifically
    expect(screen.getByText('A1', { selector: 'span' })).toBeInTheDocument()
    expect(screen.getByText('MC')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('5.2')).toBeInTheDocument()
    expect(screen.getByText('3.1')).toBeInTheDocument()
    expect(screen.getByText('1 / 1 started')).toBeInTheDocument()
  })

  it('shows Review button for started concept', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getReviewSchedule).mockResolvedValue({
      course_id: 'course-1',
      items: [startedConcept],
    })

    renderPage()

    expect(await screen.findByRole('button', { name: 'Review' })).toBeInTheDocument()
  })

  it('shows Start button for unstarted concept', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getReviewSchedule).mockResolvedValue({
      course_id: 'course-1',
      items: [unstartedConcept],
    })

    renderPage()

    expect(await screen.findByRole('button', { name: 'Start' })).toBeInTheDocument()
  })

  it('shows started/total count in subtitle', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getReviewSchedule).mockResolvedValue({
      course_id: 'course-1',
      items: [startedConcept, unstartedConcept],
    })

    renderPage()

    expect(await screen.findByText('1 / 2 started')).toBeInTheDocument()
  })

  it('shows dashes for unstarted concept fields', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getReviewSchedule).mockResolvedValue({
      course_id: 'course-1',
      items: [unstartedConcept],
    })

    renderPage()

    await screen.findByText('goodbye')
    expect(screen.getByText('Not started', { selector: 'span' })).toBeInTheDocument()
  })

  it('highlights overdue items', async () => {
    const pastDate = '2020-01-01T00:00:00Z'
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getReviewSchedule).mockResolvedValue({
      course_id: 'course-1',
      items: [
        {
          ...startedConcept,
          fsrs_due: pastDate,
        },
      ],
    })

    renderPage()

    await screen.findByText('hello')
    const dueCell = screen.getByText((_, el) => {
      return el?.tagName === 'SPAN' && el.className.includes('text-orange-500') || false
    })
    expect(dueCell).toBeInTheDocument()
  })

  it('filters by CEFR level', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getReviewSchedule).mockResolvedValue({
      course_id: 'course-1',
      items: [
        startedConcept,
        { ...unstartedConcept, cefr_level: 'B1' },
      ],
    })

    renderPage()
    await screen.findByText('hello')

    // Both visible initially
    expect(screen.getByText('hello')).toBeInTheDocument()
    expect(screen.getByText('goodbye')).toBeInTheDocument()

    // Filter to A1 via the CEFR select
    const cefrSelect = within(
      screen.getByText('CEFR:').closest('label')!,
    ).getByRole('combobox')
    fireEvent.change(cefrSelect, { target: { value: 'A1' } })

    expect(screen.getByText('hello')).toBeInTheDocument()
    expect(screen.queryByText('goodbye')).not.toBeInTheDocument()
  })

  it('filters by status', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getReviewSchedule).mockResolvedValue({
      course_id: 'course-1',
      items: [startedConcept, unstartedConcept],
    })

    renderPage()
    await screen.findByText('hello')

    // Filter to "Not started"
    const statusSelect = within(
      screen.getByText('Status:').closest('label')!,
    ).getByRole('combobox')
    fireEvent.change(statusSelect, { target: { value: 'not_started' } })

    expect(screen.queryByText('hello')).not.toBeInTheDocument()
    expect(screen.getByText('goodbye')).toBeInTheDocument()
  })
})

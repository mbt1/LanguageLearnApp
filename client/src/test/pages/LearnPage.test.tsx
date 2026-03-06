// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { LearnPage } from '@/pages/LearnPage'

vi.mock('@/api/study', () => ({
  studySession: vi.fn(),
  submitExercise: vi.fn(),
}))

import * as studyApi from '@/api/study'

const mockItem = {
  concept_id: 'concept-1',
  exercise_type: 'forward_mc' as const,
  is_review: false,
  source_text: "hello",
  target_text: 'hola',
  concept_type: 'vocabulary' as const,
  cefr_level: 'A1' as const,
  correct_answer: 'hola',
  distractors: ['adiós', 'gracias'],
  sentence_template: null,
  explanation: null,
}

const mockResult = {
  correct: true,
  correct_answer: 'hola',
  normalized_user_answer: 'hola',
  new_forward_difficulty: 'forward_mc' as const,
  forward_consecutive_correct: 1,
  new_reverse_difficulty: 'reverse_mc' as const,
  reverse_consecutive_correct: 0,
  is_mastered: false,
  fsrs_due: null,
  difficulty_advanced: false,
  mastery_changed: false,
}

function renderPage(courseId = 'course-1', conceptId?: string) {
  const path = conceptId
    ? `/learn/${courseId}?conceptId=${conceptId}`
    : `/learn/${courseId}`
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/learn/:courseId" element={<LearnPage />} />
        <Route path="/" element={<div>courses page</div>} />
        <Route path="/review-schedule" element={<div>review schedule page</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('LearnPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default session size preference
    localStorage.setItem('sessionSize', '20')
  })

  it('shows loading state initially', () => {
    vi.mocked(studyApi.studySession).mockReturnValue(new Promise(() => {}))
    renderPage()
    expect(screen.getByText(/loading session/i)).toBeInTheDocument()
  })

  it('renders multiple_choice exercise when session loads', async () => {
    vi.mocked(studyApi.studySession).mockResolvedValue({
      items: [mockItem],
      total_due_reviews: 1,
      new_concepts_added: 0,
    })

    renderPage()

    expect(await screen.findByText("hello")).toBeInTheDocument()
    // Options include target + distractors
    expect(screen.getByRole('button', { name: 'hola' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'adiós' })).toBeInTheDocument()
  })

  it('shows feedback after answer submission', async () => {
    const user = userEvent.setup()
    vi.mocked(studyApi.studySession).mockResolvedValue({
      items: [mockItem],
      total_due_reviews: 1,
      new_concepts_added: 0,
    })
    vi.mocked(studyApi.submitExercise).mockResolvedValue(mockResult)

    renderPage()

    await user.click(await screen.findByRole('button', { name: 'hola' }))

    expect(await screen.findByText(/correct/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /click to continue/i })).toBeInTheDocument()
  })

  it('shows session summary after last item', async () => {
    const user = userEvent.setup()
    vi.mocked(studyApi.studySession).mockResolvedValue({
      items: [mockItem],
      total_due_reviews: 1,
      new_concepts_added: 0,
    })
    vi.mocked(studyApi.submitExercise).mockResolvedValue(mockResult)

    renderPage()

    await user.click(await screen.findByRole('button', { name: 'hola' }))
    await user.click(await screen.findByRole('button', { name: /click to continue/i }))

    expect(await screen.findByText(/session complete/i)).toBeInTheDocument()
    expect(screen.getByText('100%')).toBeInTheDocument()
  })

  it('shows empty summary when session has no items', async () => {
    vi.mocked(studyApi.studySession).mockResolvedValue({
      items: [],
      total_due_reviews: 0,
      new_concepts_added: 0,
    })

    renderPage()

    expect(await screen.findByText(/session complete/i)).toBeInTheDocument()
  })

  it('renders typing exercise for typing type', async () => {
    vi.mocked(studyApi.studySession).mockResolvedValue({
      items: [{ ...mockItem, exercise_type: 'forward_typing' as const }],
      total_due_reviews: 1,
      new_concepts_added: 0,
    })

    renderPage()

    expect(await screen.findByText('hello')).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('passes conceptIds to studySession when conceptId query param set', async () => {
    vi.mocked(studyApi.studySession).mockResolvedValue({
      items: [mockItem],
      total_due_reviews: 0,
      new_concepts_added: 1,
    })

    renderPage('course-1', 'concept-42')

    await screen.findByText("hello")
    expect(studyApi.studySession).toHaveBeenCalledWith('course-1', 20, ['concept-42'])
  })

  it('shows cancel button during exercise state', async () => {
    vi.mocked(studyApi.studySession).mockResolvedValue({
      items: [mockItem],
      total_due_reviews: 0,
      new_concepts_added: 0,
    })

    renderPage()

    await screen.findByText("hello")
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
  })

  it('cancel navigates to review schedule for targeted session', async () => {
    const user = userEvent.setup()
    vi.mocked(studyApi.studySession).mockResolvedValue({
      items: [mockItem],
      total_due_reviews: 0,
      new_concepts_added: 1,
    })

    renderPage('course-1', 'concept-42')

    await user.click(await screen.findByRole('button', { name: /cancel/i }))
    expect(screen.getByText('review schedule page')).toBeInTheDocument()
  })

  it('cancel navigates to home for normal session', async () => {
    const user = userEvent.setup()
    vi.mocked(studyApi.studySession).mockResolvedValue({
      items: [mockItem],
      total_due_reviews: 0,
      new_concepts_added: 0,
    })

    renderPage()

    await user.click(await screen.findByRole('button', { name: /cancel/i }))
    expect(screen.getByText('courses page')).toBeInTheDocument()
  })
})

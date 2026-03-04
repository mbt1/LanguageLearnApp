// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { CourseListPage } from '@/pages/CourseListPage'

vi.mock('@/api/courses', () => ({
  listCourses: vi.fn(),
}))

vi.mock('@/api/study', () => ({
  getAllProgress: vi.fn(),
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
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<CourseListPage />} />
        <Route path="/learn/:courseId" element={<div>learn page</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('CourseListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows empty state when no courses', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([])

    renderPage()

    expect(await screen.findByText(/no courses yet/i)).toBeInTheDocument()
  })

  it('shows course titles after loading', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getAllProgress).mockResolvedValue({
      'course-1': [{ cefr_level: 'A1', total_concepts: 5, mastered_concepts: 2, mastery_percentage: 40 }],
    })

    renderPage()

    expect(await screen.findByText('Spanish Basics')).toBeInTheDocument()
  })

  it('shows mastery summary and CEFR breakdown', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getAllProgress).mockResolvedValue({
      'course-1': [
        { cefr_level: 'A1', total_concepts: 10, mastered_concepts: 4, mastery_percentage: 40 },
        { cefr_level: 'A2', total_concepts: 5, mastered_concepts: 0, mastery_percentage: 0 },
      ],
    })

    renderPage()

    // Wait for data to load
    await screen.findByText('Spanish Basics')
    // Mastery summary shown (4+0/10+5 = 4/15 mastered)
    expect(screen.getByText(/4\/15 mastered/i)).toBeInTheDocument()
    // CEFR level badges shown
    expect(screen.getByText(/^A1:/)).toBeInTheDocument()
    expect(screen.getByText(/^A2:/)).toBeInTheDocument()
  })

  it('navigates to /learn/:courseId on Study click', async () => {
    const { user } = await import('@testing-library/user-event').then((m) => ({
      user: m.default.setup(),
    }))

    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getAllProgress).mockResolvedValue({})

    renderPage()

    await user.click(await screen.findByRole('link', { name: /study/i }))

    expect(screen.getByText('learn page')).toBeInTheDocument()
  })
})

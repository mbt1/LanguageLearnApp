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
    vi.mocked(studyApi.getAllProgress).mockResolvedValue({})

    renderPage()

    expect(await screen.findByText(/no courses yet/i)).toBeInTheDocument()
  })

  it('shows course titles after loading', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getAllProgress).mockResolvedValue({
      'course-1': [
        {
          cefr_level: 'A1',
          total_concepts: 5,
          not_started: 3,
          seen: 1,
          familiar: 1,
          practiced: 0,
          proficient: 0,
          mastered: 0,
        },
      ],
    })

    renderPage()

    expect(await screen.findByText('Spanish Basics')).toBeInTheDocument()
  })

  it('shows CEFR progress bars with started counts', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getAllProgress).mockResolvedValue({
      'course-1': [
        {
          cefr_level: 'A1',
          total_concepts: 10,
          not_started: 3,
          seen: 2,
          familiar: 1,
          practiced: 1,
          proficient: 1,
          mastered: 2,
        },
        {
          cefr_level: 'A2',
          total_concepts: 5,
          not_started: 5,
          seen: 0,
          familiar: 0,
          practiced: 0,
          proficient: 0,
          mastered: 0,
        },
      ],
    })

    renderPage()

    await screen.findByText('Spanish Basics')
    // CEFR level labels
    expect(screen.getByText('A1')).toBeInTheDocument()
    expect(screen.getByText('A2')).toBeInTheDocument()
    // Total shown at end of bar
    expect(screen.getByText('10')).toBeInTheDocument()
    // A1 cumulative: seen=2, familiar=2+1=3, practiced=3+1=4, proficient=4+1=5, mastered=5+2=7
    expect(screen.getByText('7')).toBeInTheDocument()
  })

  it('shows no progress message when levels are empty', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([mockCourse])
    vi.mocked(studyApi.getAllProgress).mockResolvedValue({})

    renderPage()

    await screen.findByText('Spanish Basics')
    expect(screen.getByText(/no progress yet/i)).toBeInTheDocument()
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

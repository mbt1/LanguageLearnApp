// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ProgressPage } from '@/pages/ProgressPage'

vi.mock('@/api/courses', () => ({
  listCourses: vi.fn(),
}))

vi.mock('@/api/study', () => ({
  getAllProgress: vi.fn(),
}))

import * as coursesApi from '@/api/courses'
import * as studyApi from '@/api/study'

function renderPage() {
  return render(
    <MemoryRouter>
      <ProgressPage />
    </MemoryRouter>,
  )
}

describe('ProgressPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state initially', () => {
    vi.mocked(coursesApi.listCourses).mockReturnValue(new Promise(() => {}))
    vi.mocked(studyApi.getAllProgress).mockReturnValue(new Promise(() => {}))
    renderPage()
    expect(screen.getByText(/loading progress/i)).toBeInTheDocument()
  })

  it('shows empty state when no courses', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([])
    vi.mocked(studyApi.getAllProgress).mockResolvedValue({})
    renderPage()
    expect(await screen.findByText(/no courses yet/i)).toBeInTheDocument()
  })

  it('shows CEFR progress bars for a course', async () => {
    vi.mocked(coursesApi.listCourses).mockResolvedValue([
      {
        id: 'course-1',
        slug: 'spanish',
        title: 'Spanish',
        source_language: 'en',
        target_language: 'es',
        created_at: '2026-01-01T00:00:00Z',
      },
    ])
    vi.mocked(studyApi.getAllProgress).mockResolvedValue({
      'course-1': [
        { cefr_level: 'A1', total_concepts: 10, mastered_concepts: 7, mastery_percentage: 70 },
        { cefr_level: 'A2', total_concepts: 5, mastered_concepts: 0, mastery_percentage: 0 },
      ],
    })

    renderPage()

    expect(await screen.findByText('Spanish')).toBeInTheDocument()
    // CEFR rows shown
    expect(screen.getByText('A1')).toBeInTheDocument()
    expect(screen.getByText('A2')).toBeInTheDocument()
    // Mastery info shown
    expect(screen.getByText(/7\/10 mastered/i)).toBeInTheDocument()
    // Progress bars rendered
    const progressBars = screen.getAllByRole('progressbar')
    expect(progressBars.length).toBeGreaterThanOrEqual(2)
  })
})

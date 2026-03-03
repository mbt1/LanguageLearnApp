// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  apiRequest: vi.fn(),
}))

import { listCourses } from '@/api/courses'
import { apiRequest } from '@/api/client'

const mockApiRequest = vi.mocked(apiRequest)

describe('listCourses', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('gets from /v1/courses', async () => {
    mockApiRequest.mockResolvedValueOnce([])

    await listCourses()

    expect(mockApiRequest).toHaveBeenCalledWith('/v1/courses')
  })

  it('returns the course list from the API', async () => {
    const courses = [
      {
        id: 'course-1',
        slug: 'spanish-basics',
        title: 'Spanish Basics',
        source_language: 'en',
        target_language: 'es',
        created_at: '2026-01-01T00:00:00Z',
      },
    ]
    mockApiRequest.mockResolvedValueOnce(courses)

    const result = await listCourses()

    expect(result).toEqual(courses)
  })
})

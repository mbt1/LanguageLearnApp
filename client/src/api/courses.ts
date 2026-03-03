// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { apiRequest } from './client'
import type { CourseResponse } from './types'

export async function listCourses(): Promise<CourseResponse[]> {
  return apiRequest<CourseResponse[]>('/v1/courses')
}

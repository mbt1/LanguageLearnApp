// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { cachedGet } from './client'
import type { CourseResponse } from './types'

export async function listCourses(): Promise<CourseResponse[]> {
  return cachedGet<CourseResponse[]>('/v1/courses')
}

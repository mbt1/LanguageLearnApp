// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { apiRequest } from './client'
import type {
  CefrProgressItem,
  CourseProgressResponse,
  ExerciseSubmitRequest,
  ExerciseSubmitResponse,
  StudySessionResponse,
} from './types'

export async function studySession(
  courseId: string,
  sessionSize?: number,
): Promise<StudySessionResponse> {
  return apiRequest<StudySessionResponse>('/v1/study/session', {
    method: 'POST',
    body: JSON.stringify({
      course_id: courseId,
      ...(sessionSize !== undefined ? { session_size: sessionSize } : {}),
    }),
  })
}

export async function submitExercise(
  req: ExerciseSubmitRequest,
): Promise<ExerciseSubmitResponse> {
  return apiRequest<ExerciseSubmitResponse>('/v1/exercises/submit', {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

export async function getCourseProgress(courseId: string): Promise<CourseProgressResponse> {
  return apiRequest<CourseProgressResponse>(`/v1/progress/${courseId}`)
}

export async function getAllProgress(): Promise<Record<string, CefrProgressItem[]>> {
  const resp = await apiRequest<{ courses: CourseProgressResponse[] }>('/v1/progress')
  const map: Record<string, CefrProgressItem[]> = {}
  for (const c of resp.courses) {
    map[c.course_id] = c.levels
  }
  return map
}

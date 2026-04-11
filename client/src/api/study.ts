// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { apiRequest, cachedGet, invalidateCache } from './client'
import type {
  CefrProgressItem,
  CourseProgressResponse,
  ExerciseSubmitRequest,
  ExerciseSubmitResponse,
  ReviewScheduleResponse,
  StudySessionResponse,
} from './types'

export async function studySession(
  courseId: string,
  sessionSize?: number,
  conceptIds?: string[],
): Promise<StudySessionResponse> {
  const resp = await apiRequest<StudySessionResponse>('/v1/study/session', {
    method: 'POST',
    body: JSON.stringify({
      course_id: courseId,
      ...(sessionSize !== undefined ? { session_size: sessionSize } : {}),
      ...(conceptIds !== undefined ? { concept_ids: conceptIds } : {}),
    }),
  })
  invalidateCache('/v1/progress')
  return resp
}

export async function submitExercise(req: ExerciseSubmitRequest): Promise<ExerciseSubmitResponse> {
  const resp = await apiRequest<ExerciseSubmitResponse>('/v1/exercises/submit', {
    method: 'POST',
    body: JSON.stringify(req),
  })
  invalidateCache('/v1/progress')
  return resp
}

export async function getCourseProgress(courseId: string): Promise<CourseProgressResponse> {
  return cachedGet<CourseProgressResponse>(`/v1/progress/${courseId}`)
}

export async function getAllProgress(): Promise<Record<string, CefrProgressItem[]>> {
  const resp = await cachedGet<{ courses: CourseProgressResponse[] }>('/v1/progress')
  const map: Record<string, CefrProgressItem[]> = {}
  for (const c of resp.courses) {
    map[c.course_id] = c.levels
  }
  return map
}

export async function getReviewSchedule(courseId: string): Promise<ReviewScheduleResponse> {
  return apiRequest<ReviewScheduleResponse>(`/v1/review-schedule/${courseId}`)
}

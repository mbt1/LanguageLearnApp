// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useEffect, useState } from 'react'

import { getErrorMessage } from '@/api/client'
import { listCourses } from '@/api/courses'
import { getReviewSchedule } from '@/api/study'
import type { ConceptProgressDetail, CourseResponse } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface CourseSchedule {
  course: CourseResponse
  items: ConceptProgressDetail[]
}

function formatDate(iso: string | null): string {
  if (!iso) return '--'
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatNum(n: number | null | undefined): string {
  if (n === null || n === undefined) return '--'
  return n.toFixed(1)
}

const STAGE_LABELS: Record<string, string> = {
  multiple_choice: 'MC',
  cloze: 'Cloze',
  reverse_typing: 'Rev Type',
  typing: 'Typing',
}

function DueStatus({ due }: { due: string | null }) {
  if (!due) return <span className="text-muted-foreground">--</span>
  const isOverdue = new Date(due) <= new Date()
  return (
    <span className={isOverdue ? 'font-medium text-orange-500' : ''}>
      {formatDate(due)}
    </span>
  )
}

function ScheduleTable({ items }: { items: ConceptProgressDetail[] }) {
  if (items.length === 0) {
    return <p className="text-muted-foreground text-sm">No concepts started yet.</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-muted-foreground border-b text-left">
            <th className="pb-2 pr-3 font-medium">Prompt</th>
            <th className="pb-2 pr-3 font-medium">Target</th>
            <th className="pb-2 pr-3 font-medium">CEFR</th>
            <th className="pb-2 pr-3 font-medium">Type</th>
            <th className="pb-2 pr-3 font-medium">Stage</th>
            <th className="pb-2 pr-3 font-medium">Mastered</th>
            <th className="pb-2 pr-3 font-medium">Streak</th>
            <th className="pb-2 pr-3 font-medium">Due</th>
            <th className="pb-2 pr-3 font-medium">Stability</th>
            <th className="pb-2 pr-3 font-medium">Difficulty</th>
            <th className="pb-2 font-medium">Last Review</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.concept_id} className="border-b last:border-0">
              <td className="py-2 pr-3 font-medium">{item.prompt}</td>
              <td className="py-2 pr-3">{item.target}</td>
              <td className="py-2 pr-3">
                <Badge variant="outline">{item.cefr_level}</Badge>
              </td>
              <td className="py-2 pr-3">{item.concept_type}</td>
              <td className="py-2 pr-3">
                {STAGE_LABELS[item.current_exercise_difficulty] ?? item.current_exercise_difficulty}
              </td>
              <td className="py-2 pr-3">
                {item.is_mastered ? (
                  <Badge variant="default">Yes</Badge>
                ) : (
                  <Badge variant="secondary">No</Badge>
                )}
              </td>
              <td className="py-2 pr-3 text-center">{item.consecutive_correct}</td>
              <td className="whitespace-nowrap py-2 pr-3">
                <DueStatus due={item.fsrs_due} />
              </td>
              <td className="py-2 pr-3">{formatNum(item.fsrs_stability)}</td>
              <td className="py-2 pr-3">{formatNum(item.fsrs_difficulty)}</td>
              <td className="whitespace-nowrap py-2">{formatDate(item.fsrs_last_review)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function ReviewSchedulePage() {
  const [schedules, setSchedules] = useState<CourseSchedule[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const courses = await listCourses()
        const results = await Promise.all(
          courses.map(async (course) => {
            const data = await getReviewSchedule(course.id)
            return { course, items: data.items }
          }),
        )
        if (!cancelled) setSchedules(results)
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err, 'Failed to load review schedule.'))
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [])

  if (error) {
    return <p className="text-destructive">{error}</p>
  }

  if (schedules === null) {
    return (
      <p role="status" aria-live="polite" className="text-muted-foreground">
        Loading review schedule...
      </p>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Review Schedule</h1>
      <p className="text-muted-foreground text-sm">
        Full SRS details for all concepts you have started.
      </p>
      {schedules.map(({ course, items }) => (
        <Card key={course.id}>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">{course.title}</CardTitle>
            <p className="text-muted-foreground text-sm">
              {items.length} concept{items.length !== 1 ? 's' : ''} started
            </p>
          </CardHeader>
          <CardContent>
            <ScheduleTable items={items} />
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useEffect, useState } from 'react'

import { getErrorMessage } from '@/api/client'
import { listCourses } from '@/api/courses'
import { getAllProgress } from '@/api/study'
import type { CefrProgressItem, CourseResponse } from '@/api/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface CourseLevels {
  course: CourseResponse
  levels: CefrProgressItem[]
}

/**
 * Stages in learning progression, ordered from earliest to most advanced.
 * Each maps to a Tailwind background class and a tooltip label.
 */
const STAGES = [
  { key: 'seen', bg: 'bg-zinc-400', label: 'Seen' },
  { key: 'familiar', bg: 'bg-emerald-200', label: 'Familiar' },
  { key: 'practiced', bg: 'bg-emerald-400', label: 'Practiced' },
  { key: 'proficient', bg: 'bg-emerald-600', label: 'Proficient' },
  { key: 'mastered', bg: 'bg-emerald-800', label: 'Mastered' },
] as const

function StageBar({ item }: { item: CefrProgressItem }) {
  const total = item.total_concepts
  if (total === 0) return null

  const started = total - item.not_started

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">{item.cefr_level}</span>
        <span className="text-muted-foreground">
          {started}/{total}
        </span>
      </div>
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
        {STAGES.map(({ key, bg, label }) => {
          const count = item[key]
          if (count === 0) return null
          const pct = (count / total) * 100
          return (
            <div
              key={key}
              className={`${bg} transition-all`}
              style={{ width: `${pct}%` }}
              title={`${label}: ${count}`}
            />
          )
        })}
      </div>
    </div>
  )
}

function StageLegend() {
  return (
    <div className="flex flex-wrap gap-3 text-xs">
      {STAGES.map(({ key, bg, label }) => (
        <div key={key} className="flex items-center gap-1">
          <div className={`${bg} h-2.5 w-2.5 rounded-sm`} />
          <span className="text-muted-foreground">{label}</span>
        </div>
      ))}
    </div>
  )
}

function CourseProgressCard({ course, levels }: CourseLevels) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{course.title}</CardTitle>
        <p className="text-muted-foreground text-sm">
          {course.source_language.toUpperCase()} → {course.target_language.toUpperCase()}
        </p>
      </CardHeader>
      <CardContent className="space-y-3">
        {levels.length === 0 && (
          <p className="text-muted-foreground text-sm">No progress yet.</p>
        )}
        {levels.map((item) => (
          <StageBar key={item.cefr_level} item={item} />
        ))}
      </CardContent>
    </Card>
  )
}

export function ProgressPage() {
  const [data, setData] = useState<CourseLevels[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [courses, progressMap] = await Promise.all([
          listCourses(),
          getAllProgress(),
        ])
        if (cancelled) return

        const combined: CourseLevels[] = courses.map((course) => ({
          course,
          levels: progressMap[course.id] ?? [],
        }))
        setData(combined)
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err, 'Failed to load progress.'))
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

  if (data === null) {
    return (
      <p role="status" aria-live="polite" className="text-muted-foreground">
        Loading progress...
      </p>
    )
  }

  if (data.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Progress</h1>
        <p className="text-muted-foreground">No courses yet.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Progress</h1>
      <StageLegend />
      <div className="space-y-4">
        {data.map(({ course, levels }) => (
          <CourseProgressCard key={course.id} course={course} levels={levels} />
        ))}
      </div>
    </div>
  )
}

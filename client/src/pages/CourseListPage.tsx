// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getErrorMessage } from '@/api/client'
import { listCourses } from '@/api/courses'
import { getAllProgress } from '@/api/study'
import type { CefrProgressItem, CourseResponse } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const STAGES = [
  { key: 'mastered', bg: 'bg-emerald-800', label: 'Mastered' },
  { key: 'proficient', bg: 'bg-emerald-600', label: 'Proficient' },
  { key: 'practiced', bg: 'bg-emerald-400', label: 'Practiced' },
  { key: 'familiar', bg: 'bg-emerald-200', label: 'Familiar' },
  { key: 'seen', bg: 'bg-zinc-400', label: 'Seen' },
] as const

function StageBar({ item }: { item: CefrProgressItem }) {
  const total = item.total_concepts
  if (total === 0) return null

  // Build segments with cumulative counts
  const segments: { key: string; bg: string; text: string; label: string; pct: number; cumulative: number }[] = []
  let cumulative = 0
  for (const { key, bg, label } of STAGES) {
    const count = item[key as keyof CefrProgressItem] as number
    if (count === 0) continue
    cumulative += count
    const pct = (count / total) * 100
    // Dark text on light backgrounds, white on darker ones
    const text = key === 'seen' || key === 'familiar' ? 'text-zinc-700' : 'text-white/90'
    segments.push({ key, bg, text, label, pct, cumulative })
  }

  return (
    <div className="flex items-center gap-2">
      <span className="w-7 text-sm font-medium">{item.cefr_level}</span>
      <div className="flex h-5 flex-1 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
        {segments.map(({ key, bg, text, label, pct, cumulative: cum }) => (
          <div
            key={key}
            className={`${bg} flex items-center justify-end overflow-hidden transition-all`}
            style={{ width: `${pct}%` }}
            title={`${label}: ${item[key as keyof CefrProgressItem]}`}
          >
            <span className={`${text} px-1 text-[10px] leading-none`}>{cum}</span>
          </div>
        ))}
      </div>
      <span className="w-7 text-right text-xs text-muted-foreground">{total}</span>
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

interface CourseCardProps {
  course: CourseResponse
  levels: CefrProgressItem[]
}

function CourseCard({ course, levels }: CourseCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between pb-2">
        <div>
          <CardTitle className="text-lg">{course.title}</CardTitle>
          <p className="text-muted-foreground mt-1 text-sm">
            {course.source_language.toUpperCase()} → {course.target_language.toUpperCase()}
          </p>
        </div>
        <Button asChild>
          <Link to={`/learn/${course.id}`}>Study</Link>
        </Button>
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

export function CourseListPage() {
  const [courses, setCourses] = useState<CourseResponse[] | null>(null)
  const [progressMap, setProgressMap] = useState<Record<string, CefrProgressItem[]>>({})
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [courseList, progress] = await Promise.all([
          listCourses(),
          getAllProgress(),
        ])
        if (cancelled) return
        setCourses(courseList)
        setProgressMap(progress)
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err, 'Failed to load courses.'))
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

  if (courses === null) {
    return (
      <p role="status" aria-live="polite" className="text-muted-foreground">
        Loading courses...
      </p>
    )
  }

  if (courses.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Your Courses</h1>
        <p className="text-muted-foreground">No courses yet. Import a course to get started.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Your Courses</h1>
      <StageLegend />
      <div className="space-y-3">
        {courses.map((course) => (
          <CourseCard key={course.id} course={course} levels={progressMap[course.id] ?? []} />
        ))}
      </div>
    </div>
  )
}

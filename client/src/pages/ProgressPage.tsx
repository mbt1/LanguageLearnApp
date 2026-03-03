// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useEffect, useState } from 'react'

import { listCourses } from '@/api/courses'
import { getCourseProgress } from '@/api/study'
import type { CefrProgressItem, CourseResponse } from '@/api/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'

interface CourseLevels {
  course: CourseResponse
  levels: CefrProgressItem[]
}

function LevelRow({ item }: { item: CefrProgressItem }) {
  const pct = Math.round(item.mastery_percentage)
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">{item.cefr_level}</span>
        <span className="text-muted-foreground">
          {item.mastered_concepts}/{item.total_concepts} mastered ({pct}%)
        </span>
      </div>
      <Progress value={pct} />
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
          <LevelRow key={item.cefr_level} item={item} />
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
        const courses = await listCourses()
        if (cancelled) return

        const results = await Promise.allSettled(courses.map((c) => getCourseProgress(c.id)))
        if (cancelled) return

        const combined: CourseLevels[] = []
        courses.forEach((course, i) => {
          const result = results[i]
          if (result?.status === 'fulfilled') {
            combined.push({ course, levels: result.value.levels })
          }
        })
        setData(combined)
      } catch {
        if (!cancelled) setError('Failed to load progress.')
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
    return <p className="text-muted-foreground">Loading progress...</p>
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
      <div className="space-y-4">
        {data.map(({ course, levels }) => (
          <CourseProgressCard key={course.id} course={course} levels={levels} />
        ))}
      </div>
    </div>
  )
}

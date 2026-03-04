// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getErrorMessage } from '@/api/client'
import { listCourses } from '@/api/courses'
import { getAllProgress } from '@/api/study'
import type { CefrProgressItem, CourseResponse } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface CourseCardProps {
  course: CourseResponse
  levels: CefrProgressItem[] | null
}

function CourseCard({ course, levels }: CourseCardProps) {
  const totalConcepts = levels?.reduce((sum, item) => sum + item.total_concepts, 0) ?? 0
  const startedConcepts = levels?.reduce((sum, item) => sum + item.total_concepts - item.not_started, 0) ?? 0

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
      <CardContent>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          {totalConcepts > 0 && (
            <span className="text-muted-foreground">
              {startedConcepts}/{totalConcepts} started
            </span>
          )}
          {levels?.map((item) => (
            <Badge key={item.cefr_level} variant="outline">
              {item.cefr_level}: {item.total_concepts}
            </Badge>
          ))}
        </div>
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
        const [courseList, progressMap] = await Promise.all([
          listCourses(),
          getAllProgress(),
        ])
        if (cancelled) return
        setCourses(courseList)
        setProgressMap(progressMap)
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
      <div className="space-y-3">
        {courses.map((course) => (
          <CourseCard key={course.id} course={course} levels={progressMap[course.id] ?? null} />
        ))}
      </div>
    </div>
  )
}

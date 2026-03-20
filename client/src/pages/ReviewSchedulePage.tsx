// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { getErrorMessage } from '@/api/client'
import { listCourses } from '@/api/courses'
import { getReviewSchedule } from '@/api/study'
import type { ConceptProgressDetail, CourseResponse } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface CourseSchedule {
  course: CourseResponse
  items: ConceptProgressDetail[]
}

type SortKey = 'ref' | 'cefr_level' | 'stage' | 'due' | 'status'

type SortDir = 'asc' | 'desc'
type StatusFilter = 'all' | 'not_started' | 'in_progress' | 'mastered'

const CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] as const

function formatDate(iso: string | null | undefined): string {
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

function getStatus(item: ConceptProgressDetail): StatusFilter {
  if (item.peak_difficulty == null) return 'not_started'
  if (item.is_mastered) return 'mastered'
  return 'in_progress'
}

function DueStatus({ due }: { due: string | null | undefined }) {
  if (!due) return <span className="text-muted-foreground">--</span>
  const isOverdue = new Date(due) <= new Date()
  return (
    <span className={isOverdue ? 'font-medium text-orange-500' : ''}>
      {formatDate(due)}
    </span>
  )
}

function SortHeader({
  label,
  sortKey,
  currentKey,
  currentDir,
  onSort,
}: {
  label: string
  sortKey: SortKey
  currentKey: SortKey
  currentDir: SortDir
  onSort: (key: SortKey) => void
}) {
  const active = currentKey === sortKey
  return (
    <th
      className="cursor-pointer select-none pb-2 pr-3 font-medium"
      onClick={() => onSort(sortKey)}
    >
      {label} {active ? (currentDir === 'asc' ? '\u25B2' : '\u25BC') : ''}
    </th>
  )
}

function compareItems(a: ConceptProgressDetail, b: ConceptProgressDetail, key: SortKey, dir: SortDir): number {
  let cmp = 0
  switch (key) {
    case 'ref':
      cmp = a.ref.localeCompare(b.ref)
      break
    case 'cefr_level':
      cmp = CEFR_LEVELS.indexOf(a.cefr_level as typeof CEFR_LEVELS[number])
           - CEFR_LEVELS.indexOf(b.cefr_level as typeof CEFR_LEVELS[number])
      break
    case 'stage':
      cmp = (a.peak_difficulty ?? -1) - (b.peak_difficulty ?? -1)
      break
    case 'due': {
      const aTime = a.fsrs_due ? new Date(a.fsrs_due).getTime() : Infinity
      const bTime = b.fsrs_due ? new Date(b.fsrs_due).getTime() : Infinity
      cmp = aTime - bTime
      break
    }
    case 'status': {
      const order: Record<StatusFilter, number> = { not_started: 0, in_progress: 1, mastered: 2, all: 3 }
      cmp = order[getStatus(a)] - order[getStatus(b)]
      break
    }
  }
  return dir === 'asc' ? cmp : -cmp
}

function ScheduleTable({ items, courseId }: { items: ConceptProgressDetail[]; courseId: string }) {
  const navigate = useNavigate()
  const [sortKey, setSortKey] = useState<SortKey>('ref')
  const [sortDir, setSortDir] = useState<SortDir>('asc')
  const [cefrFilter, setCefrFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const filtered = useMemo(() => {
    let result = items
    if (cefrFilter !== 'all') {
      result = result.filter((i) => i.cefr_level === cefrFilter)
    }
    if (statusFilter !== 'all') {
      result = result.filter((i) => getStatus(i) === statusFilter)
    }
    return [...result].sort((a, b) => compareItems(a, b, sortKey, sortDir))
  }, [items, cefrFilter, statusFilter, sortKey, sortDir])

  if (items.length === 0) {
    return <p className="text-muted-foreground text-sm">No concepts in this course.</p>
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-3">
        <label className="flex items-center gap-1 text-sm">
          CEFR:
          <select
            value={cefrFilter}
            onChange={(e) => setCefrFilter(e.target.value)}
            className="border-input bg-background rounded border px-2 py-1 text-sm"
          >
            <option value="all">All</option>
            {CEFR_LEVELS.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1 text-sm">
          Status:
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
            className="border-input bg-background rounded border px-2 py-1 text-sm"
          >
            <option value="all">All</option>
            <option value="not_started">Not started</option>
            <option value="in_progress">In progress</option>
            <option value="mastered">Mastered</option>
          </select>
        </label>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-muted-foreground border-b text-left">
              <SortHeader label="Concept" sortKey="ref" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} />
              <SortHeader label="CEFR" sortKey="cefr_level" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} />
              <th className="pb-2 pr-3 font-medium">Type</th>
              <SortHeader label="Level" sortKey="stage" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} />
              <SortHeader label="Status" sortKey="status" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} />
              <SortHeader label="Due" sortKey="due" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} />
              <th className="pb-2 pr-3 font-medium">Stability</th>
              <th className="pb-2 pr-3 font-medium">Difficulty</th>
              <th className="pb-2 pr-3 font-medium">Last Review</th>
              <th className="pb-2 font-medium">Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item) => {
              const isStarted = item.peak_difficulty != null
              return (
                <tr key={item.concept_id} className="border-b last:border-0">
                  <td className="py-2 pr-3 font-medium">{item.ref}</td>
                  <td className="py-2 pr-3">
                    <Badge variant="outline">{item.cefr_level}</Badge>
                  </td>
                  <td className="py-2 pr-3">{item.concept_type}</td>
                  <td className="py-2 pr-3">
                    {isStarted ? item.peak_difficulty : '--'}
                  </td>
                  <td className="py-2 pr-3">
                    {!isStarted ? (
                      <Badge variant="outline">Not started</Badge>
                    ) : item.is_mastered ? (
                      <Badge variant="default">Mastered</Badge>
                    ) : (
                      <Badge variant="secondary">In progress</Badge>
                    )}
                  </td>
                  <td className="whitespace-nowrap py-2 pr-3">
                    <DueStatus due={item.fsrs_due} />
                  </td>
                  <td className="py-2 pr-3">{formatNum(item.fsrs_stability)}</td>
                  <td className="py-2 pr-3">{formatNum(item.fsrs_difficulty)}</td>
                  <td className="whitespace-nowrap py-2 pr-3">{formatDate(item.fsrs_last_review)}</td>
                  <td className="py-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => void navigate(`/learn/${courseId}?conceptId=${item.concept_id}`)}
                    >
                      {isStarted ? 'Review' : 'Start'}
                    </Button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
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
        Browse all concepts and their SRS progress.
      </p>
      {schedules.map(({ course, items }) => {
        const started = items.filter((i) => i.peak_difficulty != null).length
        return (
          <Card key={course.id}>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg">{course.title}</CardTitle>
              <p className="text-muted-foreground text-sm">
                {started} / {items.length} started
              </p>
            </CardHeader>
            <CardContent>
              <ScheduleTable items={items} courseId={course.id} />
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}

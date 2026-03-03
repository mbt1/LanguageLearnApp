// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import DOMPurify from 'dompurify'
import { useState } from 'react'

import { Button } from '@/components/ui/button'

interface ExplanationPanelProps {
  explanation: string | null
  defaultOpen?: boolean
}

export function ExplanationPanel({ explanation, defaultOpen = false }: ExplanationPanelProps) {
  const [open, setOpen] = useState(defaultOpen)

  if (!explanation) return null

  return (
    <div className="mt-4">
      <Button variant="ghost" size="sm" onClick={() => setOpen((o) => !o)}>
        {open ? 'Hide explanation' : 'Show explanation'}
      </Button>
      {open && (
        <div
          className="prose prose-sm mt-2 rounded-md border bg-muted p-4 text-sm"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(explanation) }}
        />
      )}
    </div>
  )
}

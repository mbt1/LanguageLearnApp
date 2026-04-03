// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { test, expect } from '@playwright/test'

const API_BASE = 'http://localhost:8000'

async function setupUserWithCourse() {
  const ts = Date.now()
  const email = `e2e-progress-${ts}@example.com`
  const resp = await fetch(`${API_BASE}/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password: 'strongpassword' }),
  })
  const data = (await resp.json()) as { access_token: string }
  const token = data.access_token

  const title = `E2E Progress Course ${ts}`
  await fetch(`${API_BASE}/v1/courses/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      slug: `e2e-progress-${ts}`,
      title,
      source_language: 'en',
      target_language: 'es',
      concepts: [
        {
          ref: 'hola',
          concept_type: 'vocabulary',
          cefr_level: 'A1',
          sequence: 1,
          exercises: [
            {
              ref: 'hola-t1',
              exercise_type: 'translate',
              data: {
                prompt: ['hello'],
                answers: [['hola']],
                distractors: { semantic: ['adiós', 'gracias', 'por favor'] },
              },
            },
          ],
        },
      ],
    }),
  })

  return { email, title }
}

test.describe('CEFR progress view', () => {
  test('shows progress bars with A1 level on courses page', async ({ page }) => {
    const { email, title } = await setupUserWithCourse()

    // Login
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/password/i).fill('strongpassword')
    await page.getByRole('button', { name: /sign in/i }).click()

    // Courses page (home) shows progress inline
    await expect(page.getByText(title)).toBeVisible()
    await expect(page.getByText('A1').first()).toBeVisible()
  })
})

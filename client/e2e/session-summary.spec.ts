// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { test, expect } from '@playwright/test'

const API_BASE = 'http://localhost:8000'

async function setupSession() {
  const email = `e2e-summary-${Date.now()}@example.com`
  const resp = await fetch(`${API_BASE}/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password: 'strongpassword' }),
  })
  const data = (await resp.json()) as { access_token: string }
  const token = data.access_token

  const courseResp = await fetch(`${API_BASE}/v1/courses/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      slug: `e2e-summary-${Date.now()}`,
      title: 'E2E Summary Course',
      source_language: 'en',
      target_language: 'es',
      concepts: [
        {
          ref: 'hola',
          concept_type: 'vocabulary',
          cefr_level: 'A1',
          sequence: 1,
          prompt: 'hello',
          target: 'hola',
          exercises: [
            {
              exercise_type: 'multiple_choice',
              prompt: "Choose 'hello'",
              correct_answer: 'hola',
              distractors: ['adiós', 'gracias'],
            },
          ],
        },
      ],
    }),
  })
  const courseData = (await courseResp.json()) as { course_id: string }
  return { email, token, courseId: courseData.course_id }
}

test.describe('Session summary', () => {
  test('shows session summary after completing all items', async ({ page }) => {
    const { email, courseId } = await setupSession()

    // Login
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/password/i).fill('strongpassword')
    await page.getByRole('button', { name: /log in/i }).click()

    // Navigate to learn page
    await page.goto(`/learn/${courseId}`)

    // Answer the exercise
    await page.getByRole('button', { name: 'hola' }).click({ timeout: 10000 })

    // Click Next to advance past feedback
    await page.getByRole('button', { name: /next/i }).click()

    // Session summary shown
    await expect(page.getByText(/session complete/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /back to courses/i })).toBeVisible()
  })
})

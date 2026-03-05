// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { test, expect } from '@playwright/test'

const API_BASE = 'http://localhost:8000'

async function setupUserWithCourse() {
  const email = `e2e-progress-${Date.now()}@example.com`
  const resp = await fetch(`${API_BASE}/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password: 'strongpassword' }),
  })
  const data = (await resp.json()) as { access_token: string }
  const token = data.access_token

  await fetch(`${API_BASE}/v1/courses/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      slug: `e2e-progress-${Date.now()}`,
      title: 'E2E Progress Course',
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

  return { email }
}

test.describe('CEFR progress view', () => {
  test('shows progress bars with A1 level on courses page', async ({ page }) => {
    const { email } = await setupUserWithCourse()

    // Login
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/password/i).fill('strongpassword')
    await page.getByRole('button', { name: /log in/i }).click()

    // Courses page (home) shows progress inline
    await expect(page.getByText('E2E Progress Course')).toBeVisible()
    await expect(page.getByText('A1')).toBeVisible()
  })
})

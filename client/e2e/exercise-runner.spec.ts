// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { test, expect } from './fixtures'

const API_BASE = 'http://localhost:8000'

async function setupSession() {
  const ts = Date.now()
  const email = `e2e-runner-${ts}@example.com`
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
      slug: `e2e-runner-${ts}`,
      title: `E2E Runner Course ${ts}`,
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
  const courseData = (await courseResp.json()) as { course_id: string }
  return { email, token, courseId: courseData.course_id }
}

test.describe('Exercise runner', () => {
  test('completes a multiple choice exercise and shows feedback', async ({ page, checkA11y }) => {
    const { email } = await setupSession()

    // Login
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/password/i).fill('strongpassword')
    await page.getByRole('button', { name: /sign in/i }).click()

    // Wait for course list then navigate to learn page
    await expect(page.getByRole('heading', { name: /your courses/i })).toBeVisible()
    await page.getByRole('link', { name: /study/i }).first().click()

    // Wait for exercise to load
    await expect(page.getByText('hello')).toBeVisible({ timeout: 10000 })
    await checkA11y()

    // Click the correct answer
    await page.getByRole('button', { name: 'hola' }).click()

    // Feedback panel shown
    await expect(page.getByText('✓ Correct!')).toBeVisible()
    await expect(page.getByText('Click or press Enter to continue')).toBeVisible()
    await checkA11y()
  })
})

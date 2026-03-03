// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { test, expect } from './fixtures'

const API_BASE = 'http://localhost:8000'

async function registerUser() {
  const email = `e2e-courselist-${Date.now()}@example.com`
  const resp = await fetch(`${API_BASE}/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password: 'strongpassword' }),
  })
  const data = (await resp.json()) as { access_token: string }
  return { email, token: data.access_token }
}

async function importCourse(token: string) {
  const slug = `e2e-course-${Date.now()}`
  const resp = await fetch(`${API_BASE}/v1/courses/import`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      slug,
      title: 'E2E Spanish Course',
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
  const data = (await resp.json()) as { course_id: string }
  return data.course_id
}

test.describe('Course list', () => {
  test('shows imported course with CEFR badge and Study link', async ({ page, checkA11y }) => {
    const { email, token } = await registerUser()
    await importCourse(token)

    // Login via the UI
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/password/i).fill('strongpassword')
    await page.getByRole('button', { name: /log in/i }).click()

    // Should land on course list
    await expect(page.getByRole('heading', { name: /your courses/i })).toBeVisible()
    await expect(page.getByText('E2E Spanish Course')).toBeVisible()
    await checkA11y()

    // CEFR badge shown
    await expect(page.getByText(/A1/)).toBeVisible()

    // Study link navigates to /learn/:courseId
    await page.getByRole('link', { name: /study/i }).click()
    await expect(page).toHaveURL(/\/learn\//)
  })
})

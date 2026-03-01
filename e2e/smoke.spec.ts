// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { test, expect } from '@playwright/test'

test('smoke: app loads with correct title', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/LanguageLearn/)
})

test('smoke: login page is accessible', async ({ page }) => {
  await page.goto('/login')
  await expect(page.getByText('Sign in to your account')).toBeVisible()
})

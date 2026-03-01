// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { test, expect } from '@playwright/test'

function uniqueEmail(): string {
  return `e2e-${Date.now()}@example.com`
}

test.describe('Auth flow', () => {
  test('unauthenticated user is redirected to login', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Sign in to your account')).toBeVisible()
  })

  test('register → login → logout cycle', async ({ page }) => {
    const email = uniqueEmail()

    // Navigate to register
    await page.goto('/register')
    await expect(page.getByText('Create Account', { exact: true })).toBeVisible()

    // Fill in registration form
    await page.getByLabel('Email').fill(email)
    await page.getByLabel('Password', { exact: true }).fill('password123')
    await page.getByLabel('Confirm Password').fill('password123')
    await page.getByRole('button', { name: /create account/i }).click()

    // Should be on dashboard (protected route)
    await expect(page.getByText('LanguageLearn')).toBeVisible()
    await expect(page.getByText(`Welcome, ${email}`)).toBeVisible()
    await expect(page.getByText('Email not verified')).toBeVisible()

    // Logout
    await page.getByRole('button', { name: /logout/i }).click()
    await expect(page.getByText('Sign in to your account')).toBeVisible()

    // Login with the same credentials
    await page.getByLabel('Email').fill(email)
    await page.getByLabel('Password').fill('password123')
    await page.getByRole('button', { name: /sign in/i }).click()

    // Should be on dashboard again
    await expect(page.getByText(`Welcome, ${email}`)).toBeVisible()
  })

  test('shows validation error for mismatched passwords', async ({ page }) => {
    await page.goto('/register')

    await page.getByLabel('Email').fill('test@example.com')
    await page.getByLabel('Password', { exact: true }).fill('password123')
    await page.getByLabel('Confirm Password').fill('differentpassword')
    await page.getByRole('button', { name: /create account/i }).click()

    await expect(page.getByRole('alert')).toContainText('do not match')
  })

  test('shows error on wrong password login', async ({ page }) => {
    await page.goto('/login')

    await page.getByLabel('Email').fill('nobody@example.com')
    await page.getByLabel('Password').fill('wrongpassword')
    await page.getByRole('button', { name: /sign in/i }).click()

    await expect(page.getByRole('alert')).toBeVisible()
  })

  test('navigation between login and register', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('link', { name: /register/i }).click()
    await expect(page.getByText('Create Account', { exact: true })).toBeVisible()

    await page.getByRole('link', { name: /login/i }).click()
    await expect(page.getByText('Sign in to your account')).toBeVisible()
  })
})

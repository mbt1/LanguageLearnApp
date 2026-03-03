// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import AxeBuilder from '@axe-core/playwright'
import { test as base, expect } from '@playwright/test'

type A11yFixtures = {
  checkA11y: () => Promise<void>
}

export const test = base.extend<A11yFixtures>({
  checkA11y: async ({ page }, use) => {
    await use(async () => {
      const results = await new AxeBuilder({ page }).analyze()
      expect(results.violations).toEqual([])
    })
  },
})

export { expect } from '@playwright/test'

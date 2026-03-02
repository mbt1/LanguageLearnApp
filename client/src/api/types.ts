// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors
//
// Re-exports of generated OpenAPI types for convenient use.
// This file is hand-maintained; types.gen.d.ts is auto-generated.

import type { components } from './types.gen'

// Auth types
export type RegisterResponse = components['schemas']['RegisterResponse']
export type LoginResponse = components['schemas']['LoginResponse']
export type RefreshResponse = components['schemas']['RefreshResponse']
export type VerifyEmailResponse = components['schemas']['VerifyEmailResponse']

// Passkey types
export type PasskeyRegistrationOptionsResponse =
  components['schemas']['PasskeyRegistrationOptionsResponse']
export type PasskeyRegistrationVerifyResponse =
  components['schemas']['PasskeyRegistrationVerifyResponse']
export type PasskeyAuthenticationOptionsResponse =
  components['schemas']['PasskeyAuthenticationOptionsResponse']
export type PasskeyAuthenticationVerifyResponse =
  components['schemas']['PasskeyAuthenticationVerifyResponse']
export type PasskeyListItem = components['schemas']['PasskeyListItem']

// Course & content types
export type CourseResponse = components['schemas']['CourseResponse']
export type CourseDetail = components['schemas']['CourseDetail']
export type CourseImportResponse = components['schemas']['CourseImportResponse']
export type ConceptSummary = components['schemas']['ConceptSummary']
export type ConceptDetail = components['schemas']['ConceptDetail']
export type ExerciseResponse = components['schemas']['ExerciseResponse']
export type PrerequisiteInfo = components['schemas']['PrerequisiteInfo']

// Re-export full types for future openapi-fetch usage
export type { paths, components } from './types.gen'

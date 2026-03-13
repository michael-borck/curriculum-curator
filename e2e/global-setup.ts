/**
 * Playwright global setup — runs once before all tests.
 *
 * Registers both test users via the API and auto-verifies the regular
 * user via direct DB access. This ensures tests 02+ can log in
 * without depending on the registration UI tests.
 */

import { ensureUsers } from "./helpers/setup.js";

export default async function globalSetup(): Promise<void> {
  console.log("🔧 Global setup: ensuring test users exist...");
  await ensureUsers();
  console.log("✅ Test users ready");
}

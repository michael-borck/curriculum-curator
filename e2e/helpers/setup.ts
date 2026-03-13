/**
 * Test setup helpers — register users via the API, verify via DB.
 *
 * Call ensureUsers() in global setup or beforeAll to ensure both
 * admin and regular users exist before tests run.
 */

import { API_BASE, ADMIN_USER, REGULAR_USER } from "./constants.js";
import { userExists, autoVerifyUser } from "./db.js";

/**
 * Register a user via the backend API.
 * Returns true if registration succeeded (or user already exists).
 */
async function registerUser(
  name: string,
  email: string,
  password: string,
): Promise<boolean> {
  if (userExists(email)) {
    return true;
  }

  const resp = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });

  if (resp.ok || resp.status === 409) {
    // 409 = already exists, that's fine
    return true;
  }

  const body = await resp.text();
  console.error(`Registration failed for ${email}: ${resp.status} ${body}`);
  return false;
}

/**
 * Ensure both test users exist and are verified.
 * Safe to call multiple times — skips if users already exist.
 */
export async function ensureUsers(): Promise<void> {
  // Register admin (first user — auto-verified by backend)
  const adminOk = await registerUser(
    ADMIN_USER.name,
    ADMIN_USER.email,
    ADMIN_USER.password,
  );
  if (!adminOk) {
    throw new Error("Failed to register admin user");
  }

  // Register regular user
  const userOk = await registerUser(
    REGULAR_USER.name,
    REGULAR_USER.email,
    REGULAR_USER.password,
  );
  if (!userOk) {
    throw new Error("Failed to register regular user");
  }

  // Auto-verify the regular user via DB (skip email verification)
  autoVerifyUser(REGULAR_USER.email);
}

/**
 * Direct SQLite access for test helpers.
 *
 * Used to read verification codes, seed data, and verify DB state
 * without going through the API.
 */

import Database from "better-sqlite3";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = path.resolve(
  __dirname,
  "../../backend/data/test_e2e.db",
);

function dbExists(): boolean {
  return fs.existsSync(DB_PATH);
}

export function getDb(): Database.Database {
  return new Database(DB_PATH);
}

/**
 * Get the latest unused verification code for an email address.
 */
export function getVerificationCode(email: string): string | null {
  if (!dbExists()) return null;
  const db = getDb();
  try {
    const row = db
      .prepare(
        `SELECT ev.code
         FROM email_verifications ev
         JOIN users u ON u.id = ev.user_id
         WHERE u.email = ?
           AND ev.used = 0
         ORDER BY ev.created_at DESC
         LIMIT 1`,
      )
      .get(email) as { code: string } | undefined;
    return row?.code ?? null;
  } catch {
    return null;
  } finally {
    db.close();
  }
}

/**
 * Check if a user exists and is verified.
 */
export function isUserVerified(email: string): boolean {
  if (!dbExists()) return false;
  const db = getDb();
  try {
    const row = db
      .prepare("SELECT is_verified FROM users WHERE email = ?")
      .get(email) as { is_verified: number } | undefined;
    return row?.is_verified === 1;
  } catch {
    return false;
  } finally {
    db.close();
  }
}

/**
 * Auto-verify a user by email (set is_verified=1, mark verification code used).
 * Returns true if the user was found and updated.
 */
export function autoVerifyUser(email: string): boolean {
  if (!dbExists()) return false;
  const db = getDb();
  try {
    const result = db
      .prepare("UPDATE users SET is_verified = 1 WHERE email = ?")
      .run(email);
    // Also mark any verification codes as used
    db.prepare(
      `UPDATE email_verifications SET used = 1
       WHERE user_id = (SELECT id FROM users WHERE email = ?)`,
    ).run(email);
    return result.changes > 0;
  } catch {
    return false;
  } finally {
    db.close();
  }
}

/**
 * Check if a user exists in the database.
 * Returns false if DB or table doesn't exist yet.
 */
export function userExists(email: string): boolean {
  if (!dbExists()) return false;
  const db = getDb();
  try {
    const row = db
      .prepare("SELECT id FROM users WHERE email = ?")
      .get(email) as { id: string } | undefined;
    return !!row;
  } catch {
    return false;
  } finally {
    db.close();
  }
}

/**
 * Delete the test database to start fresh.
 */
export function resetTestDb(): void {
  try {
    fs.unlinkSync(DB_PATH);
  } catch {
    // File doesn't exist — fine
  }
}

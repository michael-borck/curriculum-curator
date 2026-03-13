#!/usr/bin/env node
/**
 * Reset the E2E test database.
 *
 * Deletes the test SQLite DB so the backend creates a fresh one on startup.
 * Run this before starting the test backend.
 *
 * Usage: node scripts/setup-test-db.js
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = path.resolve(__dirname, "../../backend/data/test_e2e.db");

try {
  fs.unlinkSync(DB_PATH);
  console.log(`Deleted ${DB_PATH}`);
} catch {
  console.log("No existing test DB to delete — starting fresh.");
}

console.log("Test database reset. Start the backend with .env.test to create tables.");

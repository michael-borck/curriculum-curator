/**
 * Shared test data — consistent across all test files.
 */

// First registered user becomes admin (auto-verified, no email code needed)
// Passwords must NOT contain parts of name, email, or email domain
export const ADMIN_USER = {
  email: "admin@test.example.com",
  name: "Alice Manager",
  password: "Burgundy#Fox92!",
};

// Second user requires email verification (code read from DB)
export const REGULAR_USER = {
  email: "user@test.example.com",
  name: "Bob Learner",
  password: "Crimson$Wolf47!",
};

export const API_BASE = "http://localhost:8000/api";

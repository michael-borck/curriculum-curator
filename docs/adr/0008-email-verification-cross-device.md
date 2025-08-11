# 8. Email Verification with Cross-Device Support

Date: 2025-01-08

## Status

Accepted

## Context

After implementing basic authentication (ADR-0007), we identified the need for email verification to:
1. Ensure users own the email addresses they register with
2. Reduce admin workload by eliminating manual account verification
3. Enable self-service password reset functionality

During implementation, we discovered a critical use case: users often register on one device (e.g., classroom computer) but check email on another (e.g., personal phone). Traditional link-only verification doesn't support this workflow well.

### The Cross-Device Challenge

Consider this common scenario:
- User registers on a shared classroom/lab computer
- They check email on their personal phone
- Clicking the verification link opens the browser on their phone
- They cannot complete verification on the original computer where they need to work

## Decision

We will implement a dual-method email verification system that sends both:
1. A 6-digit verification code
2. A traditional verification link

This allows users to choose the method that best fits their situation:
- **Same device**: Click the link for instant verification
- **Cross-device**: Enter the 6-digit code on the registration device

### Implementation Details

1. **Verification Email Contents**:
   - Prominently display a 6-digit code with visual formatting
   - Include a clickable verification button/link
   - Clear instructions for both methods
   - 24-hour expiration for security

2. **Database Schema**:
   ```sql
   -- email_tokens table
   verification_code TEXT,  -- 6-digit code for email verification
   ```

3. **User Flow**:
   - After registration, show a code entry form
   - Allow entering the 6-digit code OR clicking the emailed link
   - Both methods verify the account equally

4. **Security Measures**:
   - Codes are cryptographically random (not sequential)
   - Single-use tokens (marked as used after verification)
   - Time-limited validity (24 hours)
   - No information leakage on invalid attempts

## Consequences

### Positive

- **Flexibility**: Users can verify from any device
- **User-friendly**: No need to configure email clients on shared computers
- **Accessibility**: Works well with screen readers (codes are easier to dictate)
- **Fallback**: If one method fails, users have an alternative
- **Mobile-friendly**: Easy to type a code vs. complex URL manipulation

### Negative

- **Complexity**: Two verification paths to maintain and test
- **UI Space**: Need to display both options clearly
- **Support**: Users might be confused by having two options
- **Security**: Slightly increased attack surface (though negligible with proper implementation)

### Neutral

- Code length (6 digits) balances security and usability
- Visual presentation of code aids readability
- Development mode shows codes in console when email is disabled

## Implementation Notes

1. **Email Template Design**:
   - Code displayed in large, spaced font (e.g., "123 456")
   - Clear visual hierarchy: code first, link second
   - Mobile-responsive layout

2. **Error Handling**:
   - Generic "invalid code" message (no hints)
   - Resend option available from login page
   - Admin can manually verify if needed

3. **Future Enhancements**:
   - Could add SMS verification as third option
   - Could implement rate limiting on code attempts
   - Could add QR code for mobile scanning

## Related

- Supersedes the basic authentication approach in ADR-0007
- Complements the no-JavaScript decision (ADR-0006) by keeping verification server-side
- Enables future password reset functionality using same dual-method approach

## References

- NIST Digital Identity Guidelines on verification codes
- Industry best practices for email verification
- User research on cross-device authentication workflows
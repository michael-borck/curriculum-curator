# 9. Self-Service Password Reset

Date: 2025-01-08

## Status

Accepted

## Context

With email verification in place (ADR-0008), we can now implement self-service password reset functionality. This addresses a critical operational need:

1. **Admin Burden**: Password reset requests are the most common support ticket
2. **User Frustration**: Waiting for admin response delays work
3. **Security**: Manual resets via admin create security risks (password sharing)
4. **Availability**: Admins aren't available 24/7 for urgent resets

The Brevo email service integration makes this feasible without additional infrastructure.

## Decision

We will implement a secure, email-based password reset flow:

1. **Initiation**: "Forgot password?" link on login page
2. **Verification**: User enters their registered email address
3. **Token Generation**: System creates time-limited reset token
4. **Email Delivery**: Send reset link to registered email only
5. **Reset Form**: User sets new password (with confirmation)
6. **Session Management**: Invalidate all existing sessions after reset

### Security Design

1. **No Information Leakage**:
   - Same response whether email exists or not
   - Generic "If that email exists, we've sent a reset link" message
   - Prevents email enumeration attacks

2. **Token Security**:
   - Cryptographically secure random tokens
   - Single-use (marked as used after reset)
   - Time-limited (1 hour expiration)
   - Stored hashed in database

3. **Session Invalidation**:
   - All user sessions deleted after password reset
   - Prevents compromised sessions from persisting
   - User must login with new password

4. **Rate Limiting** (future enhancement):
   - Limit reset requests per email per hour
   - Prevent abuse and email bombing

### Database Schema

Uses existing `email_tokens` table:
```sql
-- token_type = 'reset' for password reset tokens
-- expires_at set to 1 hour from creation
-- used flag prevents token reuse
```

## Consequences

### Positive

- **Reduced Admin Workload**: 90%+ reduction in password reset tickets
- **User Autonomy**: Users can reset passwords immediately
- **Better Security**: No password sharing between admin and user
- **Audit Trail**: All resets logged with timestamps
- **24/7 Availability**: Works outside business hours

### Negative

- **Email Dependency**: Requires working email configuration
- **Phishing Risk**: Users might be targeted with fake reset emails
- **Support Complexity**: Some users may still need help with the process
- **Email Delays**: Reset depends on email delivery speed

### Neutral

- **Admin Override**: Admins retain ability to manually reset passwords
- **Mobile Workflow**: Reset link works on any device with email access
- **Notification**: Consider adding email notification after successful reset

## Implementation Notes

1. **Email Template**:
   - Clear subject line: "Reset your Curriculum Curator password"
   - Prominent reset button
   - Plain-text link as fallback
   - Security notice about ignoring if not requested

2. **Reset Form UX**:
   - Password strength indicator (future)
   - Clear password requirements
   - Confirmation field with matching validation
   - Success message with login link

3. **Error Scenarios**:
   - Expired token: Show appropriate message with new reset option
   - Used token: Explain token already used, link to request new one
   - Invalid token: Generic error, redirect to forgot password

4. **Development Mode**:
   - When email disabled, print reset URL to console
   - Allows testing without email configuration

## Future Enhancements

1. **Enhanced Security**:
   - Rate limiting on reset requests
   - IP-based blocking for abuse
   - Optional security questions

2. **User Notifications**:
   - Email confirmation after successful reset
   - Alert on suspicious reset attempts
   - Login notifications from new devices

3. **Password Policy**:
   - Enforce minimum complexity requirements
   - Prevent password reuse
   - Regular password expiration (if required)

## Related

- Builds on email service from ADR-0008
- Maintains no-JavaScript approach (ADR-0006)
- Complements simple authentication (ADR-0007)
- Could integrate with future SSO solution

## References

- OWASP Password Reset Best Practices
- NIST SP 800-63B on Authentication
- Industry standards for secure password reset flows
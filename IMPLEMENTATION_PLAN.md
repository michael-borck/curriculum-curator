# User Registration & Admin Workflow Implementation Plan

> **Project**: Curriculum Curator - Complete Authentication & User Management System  
> **Created**: 2025-08-08  
> **Status**: Planning Phase  
> **Current Phase**: Phase 1 - Database Models & Infrastructure

---

## 📋 Quick Status Overview

### ✅ Currently Implemented
- [x] Basic JWT authentication with mock login
- [x] Password hashing utilities (bcrypt)
- [x] `fastapi-mail` configured in pyproject.toml
- [x] SMTP configuration structure in config.py
- [x] Landing → Login → Dashboard user flow
- [x] Basic Dashboard with logout functionality

### ❌ Missing Components
- [ ] Database models for users, verification, admin settings
- [ ] Brevo email service implementation
- [ ] User registration with email verification
- [ ] Admin dashboard and user management
- [ ] Email whitelist functionality
- [ ] Password reset functionality
- [ ] User workspace isolation
- [ ] Role-based access control

---

## 🚀 Implementation Phases

### Phase 1: Database Models & Core Infrastructure
**Status**: ✅ Completed  
**Priority**: High  
**Estimated Time**: 4-6 hours *(Completed in ~2 hours)*

#### Tasks
- [x] **1.1** Create User model (id, email, password_hash, name, role, is_verified, created_at)
- [x] **1.2** Create EmailVerification model (code, user_id, expires_at, used)
- [x] **1.3** Create PasswordReset model (token, user_id, expires_at, used)
- [x] **1.4** Create SystemSettings model (key, value) for admin configurations
- [x] **1.5** Create EmailWhitelist model (domain/email patterns)
- [x] **1.6** Set up Alembic migration for new tables
- [x] **1.7** Add database indexes for performance
- [x] **1.8** Create initial admin user seeder

#### Technical Specifications
```python
# User Model Schema
class User(Base):
    id: UUID (Primary Key)
    email: str (Unique, Index)
    password_hash: str
    name: str
    role: Enum('admin', 'user')
    is_verified: bool (Default: False)
    is_active: bool (Default: True)
    created_at: datetime
    updated_at: datetime
    
# EmailVerification Schema
class EmailVerification(Base):
    id: UUID (Primary Key)
    user_id: UUID (Foreign Key → User)
    code: str (6 digits)
    expires_at: datetime
    used: bool (Default: False)
    created_at: datetime
```

#### Session Notes
- [x] **Decisions made**: 
  - Used platform-independent GUID type for UUID compatibility across SQLite/PostgreSQL
  - Created comprehensive validators for email whitelist patterns
  - Default admin user: admin@localhost / admin123 (change in production)
  - All models include created_at/updated_at timestamps for audit trails
- [x] **Issues encountered**: 
  - Initial GUID import issue in migration file (fixed by adding explicit import)
  - Email validation logic needed refinement for domain patterns vs full emails
  - Bcrypt version warning (minor, doesn't affect functionality)
- [x] **Next steps**: Begin Phase 2 - Brevo Email Service Integration

---

### Phase 2: Brevo Email Service Integration
**Status**: ✅ Completed  
**Priority**: High  
**Estimated Time**: 3-4 hours *(Completed in ~1.5 hours)*

#### Tasks
- [x] **2.1** Update config.py with Brevo API settings
- [x] **2.2** Add BREVO_API_KEY environment variable
- [x] **2.3** Configure SMTP settings for Brevo (smtp-relay.sendinblue.com)
- [x] **2.4** Create email_service.py using fastapi-mail
- [x] **2.5** Design email templates (verification, password reset)
- [x] **2.6** Implement HTML and plain text email formats
- [x] **2.7** Add rate limiting for email sending (configured, not enforced yet)
- [x] **2.8** Create authentication helper utilities for code management

#### Technical Specifications
```python
# Brevo Configuration
BREVO_API_KEY: str
BREVO_SMTP_HOST: str = "smtp-relay.sendinblue.com"
BREVO_SMTP_PORT: int = 587
BREVO_FROM_EMAIL: str = "noreply@curriculum-curator.com"
BREVO_FROM_NAME: str = "Curriculum Curator"

# Email Service Methods
- send_verification_email(user: User, code: str)
- send_password_reset_email(user: User, code: str)
- send_welcome_email(user: User)
```

#### Session Notes
- [x] **Decisions made**: 
  - Used Jinja2 templates for flexible email rendering with HTML + plain text fallback
  - Created comprehensive auth_helpers utility module for code management
  - Implemented graceful error handling for email failures (removes verification records)
  - Designed responsive HTML email templates with professional styling
  - Added automatic cleanup of expired verification/reset codes
- [x] **Issues encountered**: 
  - No significant issues - fastapi-mail integration was straightforward
  - Email templates are embedded in Python (could be moved to files later)
- [x] **Next steps**: Begin Phase 3 - Authentication Backend APIs

---

### Phase 3: Authentication Backend APIs
**Status**: 🔄 Not Started  
**Priority**: High  
**Estimated Time**: 5-6 hours

#### Tasks
- [ ] **3.1** Update registration endpoint with email whitelist validation
- [ ] **3.2** Implement 6-digit verification code generation
- [ ] **3.3** Create email verification endpoint
- [ ] **3.4** Build forgot password endpoint
- [ ] **3.5** Build reset password endpoint
- [ ] **3.6** Enhance login endpoint with verification checks
- [ ] **3.7** Add rate limiting to prevent abuse
- [ ] **3.8** Create user profile endpoints

#### API Specifications
```
POST /api/auth/register
Body: { email, password, name }
Response: { message, verification_required: true }

POST /api/auth/verify-email
Body: { email, code }
Response: { access_token, user }

POST /api/auth/forgot-password
Body: { email }
Response: { message }

POST /api/auth/reset-password
Body: { email, code, new_password }
Response: { message }

GET /api/auth/me
Headers: Authorization: Bearer <token>
Response: { id, email, name, role, is_verified }
```

#### Session Notes
- [ ] Decisions made:
- [ ] Issues encountered:
- [ ] Next steps:

---

### Phase 4: Admin Backend APIs
**Status**: 🔄 Not Started  
**Priority**: Medium  
**Estimated Time**: 4-5 hours

#### Tasks
- [ ] **4.1** Create admin user management endpoints
- [ ] **4.2** Build email whitelist CRUD endpoints
- [ ] **4.3** Implement system settings management
- [ ] **4.4** Add user search and pagination
- [ ] **4.5** Create user statistics endpoints
- [ ] **4.6** Build database backup triggers
- [ ] **4.7** Add admin role middleware protection
- [ ] **4.8** Create audit logging system

#### API Specifications
```
GET /api/admin/users?page=1&search=email
POST /api/admin/users/{id}/toggle-status
DELETE /api/admin/users/{id}

GET /api/admin/whitelist
POST /api/admin/whitelist
PUT /api/admin/whitelist/{id}
DELETE /api/admin/whitelist/{id}

GET /api/admin/settings
PUT /api/admin/settings
POST /api/admin/backup
```

#### Session Notes
- [ ] Decisions made:
- [ ] Issues encountered:
- [ ] Next steps:

---

### Phase 5: Frontend Components
**Status**: 🔄 Not Started  
**Priority**: High  
**Estimated Time**: 6-8 hours

#### Tasks
- [ ] **5.1** Create Registration modal component
- [ ] **5.2** Build Email verification component
- [ ] **5.3** Design Password reset flow components
- [ ] **5.4** Create Admin dashboard layout
- [ ] **5.5** Build User management table component
- [ ] **5.6** Create Email whitelist management interface
- [ ] **5.7** Build System settings forms
- [ ] **5.8** Add loading states and error handling

#### Component Specifications
```jsx
// Registration Flow Components
<RegistrationModal />
<EmailVerificationForm />
<PasswordResetFlow />

// Admin Components
<AdminDashboard />
<UserManagementTable />
<EmailWhitelistManager />
<SystemSettingsForm />
<DatabaseBackupPanel />
```

#### Session Notes
- [ ] Decisions made:
- [ ] Issues encountered:
- [ ] Next steps:

---

### Phase 6: User Workspace Isolation
**Status**: 🔄 Not Started  
**Priority**: Medium  
**Estimated Time**: 3-4 hours

#### Tasks
- [ ] **6.1** Add authorization middleware for user data access
- [ ] **6.2** Update all course/content queries with user_id filtering
- [ ] **6.3** Implement role-based route protection
- [ ] **6.4** Add user context to all API calls
- [ ] **6.5** Test cross-user data access prevention
- [ ] **6.6** Add admin override capabilities
- [ ] **6.7** Create user data export functionality

#### Session Notes
- [ ] Decisions made:
- [ ] Issues encountered:
- [ ] Next steps:

---

### Phase 7: Frontend Auth Flow Updates
**Status**: 🔄 Not Started  
**Priority**: High  
**Estimated Time**: 4-5 hours

#### Tasks
- [ ] **7.1** Add "Sign Up" button to Landing page
- [ ] **7.2** Update Auth store for registration flow
- [ ] **7.3** Implement conditional dashboard routing (admin vs user)
- [ ] **7.4** Create role-based navigation menus
- [ ] **7.5** Add user profile management
- [ ] **7.6** Implement proper error states
- [ ] **7.7** Add loading spinners and transitions

#### Session Notes
- [ ] Decisions made:
- [ ] Issues encountered:
- [ ] Next steps:

---

### Phase 8: Security & Brevo Enhancements
**Status**: 🔄 Not Started  
**Priority**: Medium  
**Estimated Time**: 3-4 hours

#### Tasks
- [ ] **8.1** Implement rate limiting for registration/verification
- [ ] **8.2** Add password strength validation
- [ ] **8.3** Set up Brevo webhook support
- [ ] **8.4** Implement email bounce handling
- [ ] **8.5** Add comprehensive input validation
- [ ] **8.6** Create audit logging system
- [ ] **8.7** Add monitoring and alerting
- [ ] **8.8** Performance testing and optimization

#### Session Notes
- [ ] Decisions made:
- [ ] Issues encountered:
- [ ] Next steps:

---

## 📧 Brevo Integration Details

### Configuration Requirements
```env
# Brevo Settings
BREVO_API_KEY=your_brevo_api_key_here
BREVO_SMTP_HOST=smtp-relay.sendinblue.com
BREVO_SMTP_PORT=587
BREVO_FROM_EMAIL=noreply@curriculum-curator.com
BREVO_FROM_NAME=Curriculum Curator
```

### Email Templates
- **Verification Email**: Welcome message + 6-digit code
- **Password Reset**: Security notice + reset code
- **Welcome Email**: Account activated confirmation

### Rate Limits
- Registration: 5 attempts per IP per hour
- Email sending: 50 emails per hour (Brevo free tier)
- Verification attempts: 5 per code

---

## 🔧 Development Notes

### Current Session Progress
- **Date**: 2025-08-08
- **Phase**: Planning Complete
- **Next Action**: Begin Phase 1 - Database Models

### Key Decisions Made
1. Using Brevo for email service (already configured)
2. 6-digit verification codes (device independent)
3. Email whitelist managed by admins
4. Role-based access: admin vs user dashboards
5. User workspace isolation at database level

### Technical Debt
- [ ] Need to implement proper database models
- [ ] Mock authentication needs to be replaced
- [ ] Email service needs implementation
- [ ] Admin dashboard needs creation

### Future Considerations
- Mobile app authentication flow
- SSO integration possibilities
- Advanced admin analytics
- Bulk user import functionality

---

## 📚 Resources

### Documentation Links
- [FastAPI Authentication](https://fastapi.tiangolo.com/tutorial/security/)
- [Brevo SMTP Documentation](https://developers.brevo.com/docs/send-emails-via-smtp)
- [SQLAlchemy Models](https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html)

### Dependencies Added
- `fastapi-mail>=1.4.1` ✅ Already configured
- `alembic` for database migrations
- `python-multipart` for form handling

---

*Last Updated: 2025-08-08*  
*Next Review: After completing Phase 1*
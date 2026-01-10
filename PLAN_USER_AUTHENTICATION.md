# User Authentication Implementation Plan

## Current State Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Login UI | Exists but mocked | `frontend/src/app/login/page.tsx` - Not connected to backend |
| User Database | None | No user model, no database tables |
| Password Auth | None | No password hashing, no credential validation |
| OAuth | None | No OAuth providers configured |
| Session Management | Basic | Sessions exist but not tied to authenticated users |
| API Key Auth | Working | `src/api/auth.py` - Header-based validation |

**Critical Issue**: The login page is purely cosmetic. Clicking "Sign In" runs a mock function that creates a fake user object in localStorage.

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
├─────────────────────────────────────────────────────────────────┤
│  Login Page ──► OAuth Buttons (Google, GitHub, Microsoft)        │
│       │                                                          │
│       ▼                                                          │
│  AuthContext ──► JWT Token Storage (httpOnly cookie or memory)   │
│       │                                                          │
│       ▼                                                          │
│  API Client ──► Authorization: Bearer <token>                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
├─────────────────────────────────────────────────────────────────┤
│  /auth/login ────────► Email/Password validation                 │
│  /auth/register ─────► Create new user account                   │
│  /auth/oauth/{provider} ► OAuth callback handling                │
│  /auth/refresh ──────► Refresh JWT tokens                        │
│  /auth/logout ───────► Invalidate session                        │
│  /auth/me ───────────► Get current user profile                  │
├─────────────────────────────────────────────────────────────────┤
│  JWT Middleware ─────► Validate tokens on protected routes       │
│  User Service ───────► CRUD operations for users                 │
│  OAuth Service ──────► Handle OAuth provider callbacks           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Database (SQLite/PostgreSQL)                │
├─────────────────────────────────────────────────────────────────┤
│  users ──────────────► id, email, name, hashed_password, etc.    │
│  oauth_accounts ─────► id, user_id, provider, provider_user_id   │
│  sessions ───────────► Link to existing session management       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Database & User Model Setup
**Estimated Files**: 4-5 new files

#### 1.1 Add Database Dependencies
```
# requirements.txt additions
sqlalchemy>=2.0.0
aiosqlite>=0.19.0      # For SQLite async support
python-jose[cryptography]>=3.3.0  # JWT handling
passlib[bcrypt]>=1.7.4  # Password hashing
```

#### 1.2 Create Database Models
**New File**: `src/database/models.py`
```python
# User model with:
- id (UUID, primary key)
- email (unique, indexed)
- name (optional)
- hashed_password (nullable - for OAuth-only users)
- is_active (boolean)
- is_verified (boolean)
- created_at, updated_at
- avatar_url (optional)

# OAuthAccount model:
- id (UUID, primary key)
- user_id (foreign key to users)
- provider (google, github, microsoft)
- provider_user_id (unique per provider)
- provider_email
- access_token (encrypted)
- refresh_token (encrypted)
- created_at
```

#### 1.3 Create Database Connection
**New File**: `src/database/connection.py`
- SQLAlchemy async engine setup
- Session factory
- Database initialization

#### 1.4 Configuration Updates
**Update**: `src/config.py`
```python
# New settings:
DATABASE_URL: str = "sqlite+aiosqlite:///./data/users.db"
JWT_SECRET_KEY: str  # For signing JWTs
JWT_ALGORITHM: str = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

# OAuth settings (per provider):
GOOGLE_CLIENT_ID: str = ""
GOOGLE_CLIENT_SECRET: str = ""
GITHUB_CLIENT_ID: str = ""
GITHUB_CLIENT_SECRET: str = ""
MICROSOFT_CLIENT_ID: str = ""
MICROSOFT_CLIENT_SECRET: str = ""
```

---

### Phase 2: Authentication Services
**Estimated Files**: 3-4 new files

#### 2.1 Password Service
**New File**: `src/auth/password.py`
- `hash_password(password: str) -> str`
- `verify_password(plain: str, hashed: str) -> bool`
- Uses bcrypt with proper work factor

#### 2.2 JWT Service
**New File**: `src/auth/jwt.py`
- `create_access_token(user_id: str, email: str) -> str`
- `create_refresh_token(user_id: str) -> str`
- `decode_token(token: str) -> TokenPayload`
- `verify_token(token: str) -> bool`

#### 2.3 User Service
**New File**: `src/auth/user_service.py`
- `create_user(email, password, name) -> User`
- `get_user_by_email(email) -> User | None`
- `get_user_by_id(id) -> User | None`
- `authenticate_user(email, password) -> User | None`
- `update_user(id, updates) -> User`
- `link_oauth_account(user_id, provider, oauth_data)`

#### 2.4 OAuth Service
**New File**: `src/auth/oauth.py`
- `get_oauth_login_url(provider) -> str`
- `handle_oauth_callback(provider, code) -> User`
- Provider-specific implementations for Google, GitHub, Microsoft

---

### Phase 3: API Endpoints
**Estimated Changes**: 1 new file, 2 updates

#### 3.1 Auth Router
**New File**: `src/api/auth_router.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Create new account with email/password |
| `/auth/login` | POST | Login with email/password, return JWT |
| `/auth/logout` | POST | Invalidate current session |
| `/auth/refresh` | POST | Refresh access token |
| `/auth/me` | GET | Get current user profile |
| `/auth/oauth/{provider}` | GET | Redirect to OAuth provider |
| `/auth/oauth/{provider}/callback` | GET | Handle OAuth callback |

#### 3.2 Auth Middleware Update
**Update**: `src/api/auth.py`
- Add `get_current_user()` dependency
- Verify JWT from `Authorization: Bearer <token>` header
- Make `verify_api_key()` also accept JWT tokens
- Add optional user injection for routes

#### 3.3 Session Integration
**Update**: `src/api/app.py`
- Link sessions to authenticated user_id
- Filter sessions by current user
- Protect session endpoints with auth

---

### Phase 4: Frontend Integration
**Estimated Changes**: 5-7 file updates

#### 4.1 Update AuthContext
**Update**: `frontend/src/lib/contexts/AuthContext.tsx`
- Real `login(email, password)` API call
- Real `register(email, password, name)` function
- OAuth login flow with popup/redirect
- Token storage and refresh logic
- Automatic token refresh before expiry

#### 4.2 Update Login Page
**Update**: `frontend/src/app/login/page.tsx`
- Add OAuth provider buttons (Google, GitHub, Microsoft)
- Add "Sign Up" link
- Handle OAuth redirects
- Show proper error messages

#### 4.3 Create Registration Page
**New File**: `frontend/src/app/register/page.tsx`
- Email, password, confirm password, name fields
- Password strength indicator
- Terms of service checkbox
- Link to login page

#### 4.4 Update API Client
**Update**: `frontend/src/lib/api/client.ts`
- Add JWT token to Authorization header
- Implement token refresh interceptor
- Handle 401 responses (redirect to login)

#### 4.5 OAuth Callback Page
**New File**: `frontend/src/app/auth/callback/page.tsx`
- Handle OAuth provider callbacks
- Exchange code for tokens
- Redirect to dashboard

#### 4.6 Protected Route Wrapper
**New File**: `frontend/src/components/ProtectedRoute.tsx`
- Check authentication before rendering
- Redirect to login if not authenticated
- Show loading state while checking

---

### Phase 5: Session-User Linking
**Estimated Changes**: 2-3 file updates

#### 5.1 Update Session Manager
**Update**: `src/sessions/session_manager.py`
- Require user_id for authenticated sessions
- Allow anonymous sessions for guests
- Add `get_user_sessions(user_id)` method

#### 5.2 Update Session Endpoints
**Update**: `src/api/app.py`
- Inject current user into session creation
- Filter list by current user's sessions only
- Prevent access to other users' sessions

#### 5.3 Document Ownership (Optional)
- Link uploaded documents to user_id
- Filter document listing by user
- Implement sharing capabilities

---

## New Files Summary

| File | Purpose |
|------|---------|
| `src/database/models.py` | SQLAlchemy User and OAuthAccount models |
| `src/database/connection.py` | Database engine and session factory |
| `src/auth/password.py` | Password hashing with bcrypt |
| `src/auth/jwt.py` | JWT token creation and validation |
| `src/auth/user_service.py` | User CRUD operations |
| `src/auth/oauth.py` | OAuth provider handling |
| `src/api/auth_router.py` | Authentication API endpoints |
| `frontend/src/app/register/page.tsx` | User registration page |
| `frontend/src/app/auth/callback/page.tsx` | OAuth callback handler |
| `frontend/src/components/ProtectedRoute.tsx` | Route protection component |

---

## Files to Update

| File | Changes |
|------|---------|
| `requirements.txt` | Add SQLAlchemy, python-jose, passlib, httpx |
| `src/config.py` | Add database and OAuth configuration |
| `src/api/app.py` | Include auth router, update session endpoints |
| `src/api/auth.py` | Add JWT validation, user dependency |
| `src/sessions/session_manager.py` | Add user ownership |
| `frontend/src/lib/contexts/AuthContext.tsx` | Real API integration |
| `frontend/src/app/login/page.tsx` | Add OAuth buttons, fix API calls |
| `frontend/src/lib/api/client.ts` | Add JWT interceptor |
| `env.example.yaml` | Add OAuth and database config |
| `CLAUDE.md` | Update with auth architecture |

---

## Environment Variables to Add

```yaml
# Database
DATABASE_URL: "sqlite+aiosqlite:///./data/users.db"

# JWT Configuration
JWT_SECRET_KEY: "<generate-secure-random-key>"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS: 7

# OAuth - Google
GOOGLE_CLIENT_ID: "<from-google-console>"
GOOGLE_CLIENT_SECRET: "<from-google-console>"

# OAuth - GitHub
GITHUB_CLIENT_ID: "<from-github-settings>"
GITHUB_CLIENT_SECRET: "<from-github-settings>"

# OAuth - Microsoft
MICROSOFT_CLIENT_ID: "<from-azure-portal>"
MICROSOFT_CLIENT_SECRET: "<from-azure-portal>"
```

---

## OAuth Provider Setup (User Action Required)

### Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Add authorized redirect URI: `https://your-backend.run.app/auth/oauth/google/callback`
4. Copy Client ID and Secret

### GitHub OAuth
1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Create new OAuth App
3. Set callback URL: `https://your-backend.run.app/auth/oauth/github/callback`
4. Copy Client ID and Secret

### Microsoft OAuth
1. Go to [Azure Portal](https://portal.azure.com/)
2. Register new application in Azure AD
3. Add redirect URI: `https://your-backend.run.app/auth/oauth/microsoft/callback`
4. Create client secret and copy values

---

## Security Considerations

| Aspect | Implementation |
|--------|----------------|
| Password Storage | bcrypt with cost factor 12 |
| JWT Signing | HS256 with secure random key |
| Token Storage | httpOnly cookies (preferred) or secure memory |
| CSRF Protection | Double-submit cookie pattern |
| Rate Limiting | 5 login attempts per minute per IP |
| Session Fixation | New session ID after login |
| XSS Prevention | Sanitize all user inputs |
| SQL Injection | Parameterized queries via SQLAlchemy |

---

## Database Choice

### Option A: SQLite (Recommended for Start)
- **Pros**: No additional infrastructure, works with GCS FUSE, simple setup
- **Cons**: Limited concurrent writes, not ideal for high traffic
- **Best for**: MVP, low-medium traffic applications

### Option B: PostgreSQL (Production Scale)
- **Pros**: Full ACID compliance, excellent concurrent access, rich features
- **Cons**: Requires Cloud SQL setup (~$10-30/month), more complex
- **Best for**: High-traffic production applications

**Recommendation**: Start with SQLite stored at `/mnt/chroma_data/users.db` (uses existing GCS FUSE mount), migrate to PostgreSQL when needed.

---

## Migration Path

```
Current State ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5
   (Mock)       (Database)  (Services)   (API)     (Frontend)  (Sessions)
                                                                    │
                                                                    ▼
                                                            Production Ready
```

---

## Testing Strategy

| Test Type | Coverage |
|-----------|----------|
| Unit Tests | Password hashing, JWT creation/validation, user service |
| Integration Tests | Auth endpoints, OAuth flow, database operations |
| E2E Tests | Login flow, registration, OAuth redirect, protected routes |
| Security Tests | Token expiration, invalid tokens, SQL injection, XSS |

---

## Estimated Implementation Scope

| Phase | New Files | Updated Files | Complexity |
|-------|-----------|---------------|------------|
| Phase 1 | 3 | 2 | Medium |
| Phase 2 | 4 | 0 | Medium |
| Phase 3 | 1 | 2 | Medium |
| Phase 4 | 3 | 4 | High |
| Phase 5 | 0 | 3 | Low |
| **Total** | **11** | **11** | **~22 files** |

---

## Questions for Approval

1. **Database Choice**: SQLite (simple) or PostgreSQL (scalable)?
2. **OAuth Providers**: All three (Google, GitHub, Microsoft) or start with subset?
3. **Guest Mode**: Keep guest access for unauthenticated users or require login?
4. **Email Verification**: Implement email verification flow or skip for MVP?
5. **Password Requirements**: Minimum length, complexity rules?

---

## Approval Checklist

- [ ] Database choice confirmed
- [ ] OAuth providers selected
- [ ] Guest mode decision made
- [ ] Ready to proceed with implementation

**Awaiting your approval before starting implementation.**

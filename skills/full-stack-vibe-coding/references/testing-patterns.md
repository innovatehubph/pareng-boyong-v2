# Testing Patterns

## Setup

### Vitest Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['node_modules/', 'tests/'],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
})
```

### Test Setup

```typescript
// tests/setup.ts
import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

// Reset mocks between tests
beforeEach(() => {
  vi.clearAllMocks()
})
```

---

## Unit Testing

### Testing Utilities

```typescript
// lib/utils.test.ts
import { describe, it, expect } from 'vitest'
import { cn, formatCurrency, truncate } from './utils'

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('handles conditional classes', () => {
    expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz')
  })
})

describe('formatCurrency', () => {
  it('formats USD by default', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56')
  })

  it('handles zero', () => {
    expect(formatCurrency(0)).toBe('$0.00')
  })
})
```

### Testing Validation Schemas

```typescript
// lib/validations/user.test.ts
import { describe, it, expect } from 'vitest'
import { createUserSchema } from './user'

describe('createUserSchema', () => {
  it('validates correct input', () => {
    const result = createUserSchema.safeParse({
      name: 'John Doe',
      email: 'john@example.com',
    })
    expect(result.success).toBe(true)
  })

  it('rejects invalid email', () => {
    const result = createUserSchema.safeParse({
      name: 'John Doe',
      email: 'invalid',
    })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].path).toContain('email')
    }
  })

  it('rejects short name', () => {
    const result = createUserSchema.safeParse({
      name: 'J',
      email: 'john@example.com',
    })
    expect(result.success).toBe(false)
  })
})
```

---

## Component Testing

### Testing with React Testing Library

```typescript
// components/user-form.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UserForm } from './user-form'

describe('UserForm', () => {
  it('renders form fields', () => {
    render(<UserForm onSubmit={vi.fn()} />)
    
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument()
  })

  it('shows validation errors', async () => {
    const user = userEvent.setup()
    render(<UserForm onSubmit={vi.fn()} />)
    
    await user.click(screen.getByRole('button', { name: /submit/i }))
    
    expect(await screen.findByText(/name is required/i)).toBeInTheDocument()
  })

  it('calls onSubmit with form data', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<UserForm onSubmit={onSubmit} />)
    
    await user.type(screen.getByLabelText(/name/i), 'John Doe')
    await user.type(screen.getByLabelText(/email/i), 'john@example.com')
    await user.click(screen.getByRole('button', { name: /submit/i }))
    
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        name: 'John Doe',
        email: 'john@example.com',
      })
    })
  })
})
```

### Testing Loading States

```typescript
it('shows loading state during submission', async () => {
  const user = userEvent.setup()
  const onSubmit = vi.fn(() => new Promise((r) => setTimeout(r, 100)))
  render(<UserForm onSubmit={onSubmit} />)
  
  await user.type(screen.getByLabelText(/name/i), 'John')
  await user.type(screen.getByLabelText(/email/i), 'john@example.com')
  await user.click(screen.getByRole('button', { name: /submit/i }))
  
  expect(screen.getByRole('button')).toBeDisabled()
  expect(screen.getByText(/submitting/i)).toBeInTheDocument()
})
```

---

## API Testing

### Testing Server Actions (Mocking Prisma)

```typescript
// lib/actions/users.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createUser } from './users'
import { db } from '@/lib/db'

// Mock Prisma
vi.mock('@/lib/db', () => ({
  db: {
    user: {
      create: vi.fn(),
      findUnique: vi.fn(),
    },
  },
}))

describe('createUser', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('creates a user with valid data', async () => {
    const mockUser = { id: '1', name: 'John', email: 'john@example.com' }
    vi.mocked(db.user.create).mockResolvedValue(mockUser)

    const result = await createUser({
      name: 'John',
      email: 'john@example.com',
    })

    expect(result.success).toBe(true)
    expect(result.data).toEqual(mockUser)
    expect(db.user.create).toHaveBeenCalledWith({
      data: { name: 'John', email: 'john@example.com' },
    })
  })

  it('returns error for invalid data', async () => {
    const result = await createUser({
      name: '',
      email: 'invalid',
    })

    expect(result.success).toBe(false)
    expect(result.error).toBeDefined()
    expect(db.user.create).not.toHaveBeenCalled()
  })
})
```

### Testing API Routes

```typescript
// app/api/users/route.test.ts
import { describe, it, expect, vi } from 'vitest'
import { GET, POST } from './route'
import { db } from '@/lib/db'

vi.mock('@/lib/db')

describe('GET /api/users', () => {
  it('returns paginated users', async () => {
    const mockUsers = [{ id: '1', name: 'John', email: 'john@example.com' }]
    vi.mocked(db.user.findMany).mockResolvedValue(mockUsers)
    vi.mocked(db.user.count).mockResolvedValue(1)

    const request = new Request('http://localhost/api/users?page=1&limit=10')
    const response = await GET(request)
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data.data).toEqual(mockUsers)
    expect(data.pagination.total).toBe(1)
  })
})
```

---

## E2E Testing with Playwright

### Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

### E2E Test Examples

```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test('user can sign up', async ({ page }) => {
    await page.goto('/signup')
    
    await page.fill('[name="name"]', 'Test User')
    await page.fill('[name="email"]', 'test@example.com')
    await page.fill('[name="password"]', 'SecurePass123!')
    await page.click('button[type="submit"]')
    
    await expect(page).toHaveURL('/dashboard')
    await expect(page.getByText('Welcome, Test User')).toBeVisible()
  })

  test('shows error for invalid credentials', async ({ page }) => {
    await page.goto('/login')
    
    await page.fill('[name="email"]', 'wrong@example.com')
    await page.fill('[name="password"]', 'wrongpassword')
    await page.click('button[type="submit"]')
    
    await expect(page.getByText(/invalid credentials/i)).toBeVisible()
  })
})
```

### Page Object Model

```typescript
// e2e/pages/login-page.ts
import { Page, Locator } from '@playwright/test'

export class LoginPage {
  readonly page: Page
  readonly emailInput: Locator
  readonly passwordInput: Locator
  readonly submitButton: Locator
  readonly errorMessage: Locator

  constructor(page: Page) {
    this.page = page
    this.emailInput = page.locator('[name="email"]')
    this.passwordInput = page.locator('[name="password"]')
    this.submitButton = page.locator('button[type="submit"]')
    this.errorMessage = page.locator('[role="alert"]')
  }

  async goto() {
    await this.page.goto('/login')
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email)
    await this.passwordInput.fill(password)
    await this.submitButton.click()
  }
}

// Usage in test
test('user can login', async ({ page }) => {
  const loginPage = new LoginPage(page)
  await loginPage.goto()
  await loginPage.login('user@example.com', 'password123')
  await expect(page).toHaveURL('/dashboard')
})
```

---

## Test Commands

```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific file
npm test -- user.test.ts

# Run in watch mode
npm test -- --watch

# Run E2E tests
npx playwright test

# Run E2E with UI
npx playwright test --ui

# View E2E report
npx playwright show-report
```

---

## Testing Best Practices

1. **Test behavior, not implementation** — Focus on what the user sees/does
2. **One assertion per test** — Clear failure messages
3. **Arrange-Act-Assert** — Clear test structure
4. **Mock at boundaries** — Database, APIs, not internal functions
5. **Use test factories** — Consistent test data creation
6. **Clean up after tests** — Reset state between tests
7. **Test edge cases** — Empty, null, max values
8. **Don't test framework code** — Focus on your logic

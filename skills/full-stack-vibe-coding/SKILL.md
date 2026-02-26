---
name: full-stack-vibe-coding
version: 1.0.0
description: |
  Complete full-stack webapp development skill for vibe coding — PRD-driven development, modern UI/UX with shadcn/ui and Tailwind, 
  React/Next.js frontend, Node.js backend, PostgreSQL/Prisma database, with strict rules to prevent duplicate files and ensure 
  code reuse. Use when: building webapps from scratch, implementing features, designing UI, writing PRDs, creating wireframes, 
  or any full-stack development task. Triggers: webapp, full-stack, vibe coding, build app, create feature, PRD, wireframe, 
  shadcn, tailwind, next.js, react, node, prisma, database schema.
triggers:
  - webapp
  - full-stack
  - vibe coding
  - build app
  - create feature
  - PRD
  - wireframe
  - shadcn
  - tailwind
  - next.js
  - react
  - node
  - prisma
  - new feature
  - implement
role: lead-developer
scope: full-stack
output-format: code
---

# Full-Stack Vibe Coding

> Build modern webapps fast with PRD-driven development, beautiful UI, and clean architecture. No duplicate files. No wasted effort. Pure vibe. 🚀

---

## 🚨 CRITICAL RULES (Read First)

### Rule 1: Check Before Creating

**NEVER create a new file without first checking if similar functionality exists.**

```bash
# Before creating ANY file, run these checks:
find . -name "*.tsx" -o -name "*.ts" | xargs grep -l "ComponentName\|functionName"
grep -r "similar-functionality" src/
```

| Action | Check First |
|--------|-------------|
| New component | Does a similar component exist in `components/`? |
| New API route | Is there an existing endpoint that can be extended? |
| New utility | Check `lib/utils.ts` and `lib/` folder first |
| New hook | Check `hooks/` folder for existing hooks |
| New type | Check `types/` or existing type definitions |

### Rule 2: Single Source of Truth

- **One component per concern** — don't create `Button.tsx` if `ui/button.tsx` exists
- **One API handler per resource** — extend existing routes, don't duplicate
- **One schema per entity** — Prisma schema is the source of truth for types

### Rule 3: File Organization

```
project/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Auth group routes
│   ├── (dashboard)/       # Dashboard group routes
│   ├── api/               # API routes
│   └── layout.tsx
├── components/
│   ├── ui/                # shadcn/ui components (DO NOT DUPLICATE)
│   ├── forms/             # Form components
│   ├── layouts/           # Layout components
│   └── [feature]/         # Feature-specific components
├── lib/
│   ├── db.ts              # Prisma client (SINGLE INSTANCE)
│   ├── utils.ts           # Utility functions (CHECK BEFORE ADDING)
│   ├── validations/       # Zod schemas
│   └── actions/           # Server actions
├── hooks/                 # Custom React hooks
├── types/                 # TypeScript types (extend, don't duplicate)
├── prisma/
│   └── schema.prisma      # Database schema (SINGLE SOURCE)
└── docs/
    ├── PRD.md             # Product Requirements
    ├── WIREFRAMES.md      # UI Wireframes
    └── TODO.md            # Task tracking
```

### Rule 4: Import Existing, Don't Recreate

```typescript
// ✅ CORRECT - Import from existing
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { db } from "@/lib/db"

// ❌ WRONG - Creating duplicate
// Don't create a new Button component
// Don't create a new cn function
// Don't create a new Prisma client instance
```

### Rule 5: Extend, Don't Fork

When you need to modify existing functionality:

```typescript
// ✅ CORRECT - Extend existing component
import { Button, ButtonProps } from "@/components/ui/button"

interface IconButtonProps extends ButtonProps {
  icon: React.ReactNode
}

export function IconButton({ icon, children, ...props }: IconButtonProps) {
  return <Button {...props}>{icon}{children}</Button>
}

// ❌ WRONG - Copying and modifying Button.tsx
```

---

## 🎸 Vibe Coding Philosophy

> Programming where you describe what you want and let AI generate code. You evaluate by results, not by reading every line.

### Core Vibe Rules

| Rule | Why |
|------|-----|
| **Define Intent First** | Vague prompts → vague results |
| **Research-Plan-Implement** | Catch misunderstanding during planning = 10x cheaper |
| **Test After Every Change** | AI code looks flawless but has subtle bugs |
| **Paste Errors, Let AI Fix** | Copy error → paste → usually it fixes it |
| **Constraint Anchoring** | "Under 50 lines", "Only this function", "Follow UserService.ts" |

### When to Intervene vs Let It Flow

| Let AI Flow 🌊 | Intervene 🛑 |
|----------------|--------------|
| Scaffolding, UI components | Auth, payments, security |
| Exploring ideas, prototypes | Database schemas, API permissions |
| Boilerplate, forms | User data handling |

### Research-Plan-Implement Workflow

```
1. RESEARCH: "Read the auth module, explain how sessions work"
2. PLAN: "Write the files you'll modify and changes in each"
3. IMPLEMENT: Only after reviewing the plan
```

---

## 📋 PRD (Product Requirements Document)

Every feature starts with a PRD. Create `agents/prd.json`:

### prd.json Format (Machine-Readable)

```json
{
  "project": "MyApp",
  "branchName": "feature/user-dashboard",
  "description": "User dashboard with stats and recent activity",
  "userStories": [
    {
      "id": "US-001",
      "title": "Add dashboard stats schema",
      "description": "As a developer, I need to store dashboard metrics.",
      "acceptanceCriteria": [
        "Add UserStats model to Prisma schema",
        "Generate and run migration",
        "Typecheck passes"
      ],
      "priority": 1,
      "passes": false,
      "notes": ""
    },
    {
      "id": "US-002",
      "title": "Create stats API endpoint",
      "description": "As a user, I want to fetch my dashboard stats.",
      "acceptanceCriteria": [
        "GET /api/users/[id]/stats returns stats object",
        "Authenticated users only",
        "Typecheck passes"
      ],
      "priority": 2,
      "passes": false,
      "notes": ""
    }
  ]
}
```

### Story Sizing

**Each story should be completable in one AI context window.**

| ✅ Right-sized | ❌ Too large (split these) |
|----------------|---------------------------|
| Add a database column | "Build entire dashboard" |
| Add UI component to existing page | "Add authentication" |
| Update server action with new logic | "Create admin panel" |

### Story Order

1. **Schema/database** (migrations first)
2. **Server actions / backend logic**
3. **UI components** that use backend
4. **Dashboard/summary views**

### PRD Template (Markdown Alternative)

```markdown
# Feature: [Feature Name]

## Overview
[2-3 sentence description]

## User Stories
- As a [user], I want to [action] so that [benefit]

## Acceptance Criteria
- [ ] Criterion 1 (verifiable)
- [ ] Criterion 2 (verifiable)
- [ ] Typecheck passes

## Out of Scope
- [What this does NOT include]
```

---

## 🎨 Wireframes & UI Planning

Create `docs/WIREFRAMES.md` using ASCII art for quick planning:

### Wireframe Notation

```markdown
# Page: Dashboard

┌─────────────────────────────────────────────────────┐
│ [Logo]                    [Search...]    [Avatar ▼] │  <- Header
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│ □ Home   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ □ Users  │  │ Stat 1   │ │ Stat 2   │ │ Stat 3   │ │  <- Stats Grid
│ □ Orders │  │ $12,345  │ │ 1,234    │ │ 98%      │ │
│ □ Prods  │  └──────────┘ └──────────┘ └──────────┘ │
│          │                                          │
│ ───────  │  ┌────────────────────────────────────┐ │
│ □ Config │  │ Recent Activity                    │ │  <- Activity Feed
│ □ Help   │  │ ┌─────────────────────────────────┐│ │
│          │  │ │ • User signed up - 2m ago       ││ │
│          │  │ │ • Order placed - 5m ago         ││ │
│          │  │ │ • Payment received - 10m ago    ││ │
│          │  │ └─────────────────────────────────┘│ │
│          │  └────────────────────────────────────┘ │
└──────────┴──────────────────────────────────────────┘
     ↑ Sidebar                    ↑ Main Content

## Components Needed:
- [ ] Header with search and user menu
- [ ] Sidebar navigation (collapsible)
- [ ] Stats cards (reuse Card component)
- [ ] Activity feed list

## Interactions:
- Sidebar collapses on mobile (Sheet)
- Stats refresh every 30s
- Activity feed infinite scroll
```

### Common Wireframe Symbols

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Button |
| `[...]` | Input field |
| `□` | Checkbox/Nav item |
| `○` | Radio button |
| `▼` | Dropdown |
| `┌─┐` | Card/Container |
| `←→` | Navigation |
| `↑↓` | Scroll direction |

---

## ✅ TODO Tracking

Create `docs/TODO.md`:

```markdown
# Project TODO

## In Progress 🔄
- [ ] Implement user authentication
  - [x] Login form UI
  - [ ] API endpoint
  - [ ] Session management

## Blocked 🚫
- [ ] Payment integration (waiting for Stripe keys)

## Done ✅
- [x] Project setup
- [x] Database schema
- [x] shadcn/ui components installed

## Backlog 📋
- [ ] Email notifications
- [ ] Export to CSV
- [ ] Dark mode toggle
```

---

## 💾 Memory: Project Context

Maintain project context in `docs/CONTEXT.md`:

```markdown
# Project Context

## Tech Stack
- Framework: Next.js 14 (App Router)
- UI: shadcn/ui + Tailwind CSS
- Database: PostgreSQL + Prisma
- Auth: NextAuth.js
- Validation: Zod

## Key Decisions
| Decision | Reason | Date |
|----------|--------|------|
| Use App Router | Server components, streaming | 2024-01-01 |
| Prisma over Drizzle | Better DX, mature ecosystem | 2024-01-01 |

## Environment
- Node: 20.x
- pnpm (not npm/yarn)

## Conventions
- File naming: kebab-case
- Component naming: PascalCase
- API routes: /api/v1/resource

## Known Issues
- Issue 1: [description] - [workaround]
```

---

## 🎨 UI/UX Design Principles

### The 5 Laws of Beautiful UI

1. **Contrast creates hierarchy** — big vs small, dark vs light
2. **Whitespace creates calm** — never fear empty space
3. **Consistency builds trust** — same patterns repeated
4. **Feedback confirms action** — animations, success messages
5. **Accessibility includes everyone** — contrast, keyboard, screen readers

### Design System Hierarchy

```
shadcn/ui (base components)
    ↓
Tailwind CSS (styling)
    ↓
Custom variants (extend, don't replace)
    ↓
Feature components (compose primitives)
```

### Color System

| Type | Usage |
|------|-------|
| **Primary** | Brand color — CTAs, links, active states |
| **Neutrals** | Grays 50-900 — text, backgrounds, borders |
| **Semantic** | Success (green), Error (red), Warning (yellow) |

```typescript
// ✅ Use semantic tokens (works in dark mode)
<div className="bg-background text-foreground">
<Button variant="destructive">Delete</Button>
<span className="text-muted-foreground">Hint</span>

// ❌ Raw colors break dark mode
<div className="bg-white text-black">
```

### Typography Scale (8px baseline)

```
text-xs:   12px  (captions)
text-sm:   14px  (secondary text)
text-base: 16px  (body default)
text-lg:   18px  (emphasized)
text-xl:   20px  (card titles)
text-2xl:  24px  (section headers)
text-3xl:  30px  (page titles)
text-4xl+: 36px+ (hero)
```

### Spacing System (8px grid)

```typescript
// Space in multiples of 8px
// Sections: gap-8 (32px) or space-y-8
// Components: gap-4 (16px) or space-y-4
// Elements: gap-2 (8px) or space-y-2
// Card padding: p-6 (24px)
```

### Responsive Patterns (Mobile-First)

```typescript
// Breakpoints: sm:640px md:768px lg:1024px xl:1280px
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

// Common patterns
// Stack → Grid: flex-col md:flex-row
// Hide mobile: hidden md:block
// Full → Fixed: w-full md:w-auto
```

### Micro-Interactions

```css
/* Hover: scale up slightly */
.btn:hover { transform: scale(1.02); }

/* Click: scale down for tactile feel */
.btn:active { transform: scale(0.98); }

/* Duration: 150-200ms (subtle, fast) */
transition: all 0.15s ease;

/* Only animate transform & opacity (GPU) */
```

### Accessibility (WCAG 2.2)

| Requirement | Target |
|-------------|--------|
| Text contrast | 4.5:1 minimum |
| UI components | 3:1 minimum |
| Focus states | Visible, 3:1 contrast |
| Keyboard nav | Logical tab order |

**Checklist:**
- [ ] All interactive elements keyboard accessible
- [ ] Color contrast ratio ≥ 4.5:1
- [ ] Form inputs have visible labels
- [ ] Images have alt text
- [ ] Focus states visible
- [ ] Tested with screen reader

---

## 🏗️ Architecture Patterns

### Component Architecture

```
Page (Server Component)
  └── Layout
        └── Feature Component (Client if interactive)
              ├── UI Components (shadcn/ui)
              └── Data Display
```

### Data Flow

```
User Action → Server Action/API → Database → Revalidate → UI Update
```

### Server Actions Pattern

```typescript
// lib/actions/users.ts
"use server"

import { z } from "zod"
import { db } from "@/lib/db"
import { revalidatePath } from "next/cache"

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2),
})

export async function createUser(formData: FormData) {
  const data = createUserSchema.parse({
    email: formData.get("email"),
    name: formData.get("name"),
  })

  const user = await db.user.create({ data })
  revalidatePath("/users")
  return { success: true, user }
}
```

---

## ✅ Pre-Build Checklist

Before writing ANY code:

### Design
- [ ] Color palette defined (primary + neutrals + semantic)
- [ ] Typography scale chosen (6-8 sizes)
- [ ] Mobile breakpoints planned (640, 768, 1024px)
- [ ] Accessibility contrast checked (4.5:1 text)

### Architecture
- [ ] PRD/user stories written
- [ ] Wireframes sketched (ASCII or Figma)
- [ ] Database schema designed
- [ ] API endpoints planned

### Codebase
- [ ] Searched for existing similar components
- [ ] Identified files to modify
- [ ] Checked lib/utils.ts for reusable functions
- [ ] Verified no duplicate implementations exist

---

## 🛠️ Quick Start Commands

```bash
# New Next.js project with shadcn/ui
npx create-next-app@latest my-app --typescript --tailwind --eslint --app
cd my-app
npx shadcn@latest init
npx shadcn@latest add button card input form table dialog sheet toast

# Prisma setup
npm install prisma @prisma/client
npx prisma init
npx prisma db push
npx prisma generate
npx prisma studio

# Common dev commands
npm run dev          # Start dev server
npm run build        # Production build
npm run lint         # Lint check
npx prisma migrate dev --name init  # Create migration
```

---

## 📚 References

### Internal References

| Reference | Description |
|-----------|-------------|
| [shadcn-patterns.md](references/shadcn-patterns.md) | shadcn/ui component patterns and recipes |
| [api-patterns.md](references/api-patterns.md) | REST API and Server Action patterns |
| [database-patterns.md](references/database-patterns.md) | Prisma schema and query patterns |
| [testing-patterns.md](references/testing-patterns.md) | Vitest and Playwright testing patterns |

### Related Skills (Installed)

| Skill | Use For |
|-------|---------|
| `ui-ux-design` | Deep-dive UI/UX principles, 2026 trends |
| `prd` | Advanced PRD patterns, agent workflows |
| `vibe-coding` | Prompting techniques, pitfalls, tool selection |
| `shadcn-ui` | Full shadcn/ui component reference |

---

## 🔄 Development Workflow

### Feature Development Checklist

1. **Plan**
   - [ ] Update PRD with requirements
   - [ ] Create wireframes
   - [ ] Add tasks to TODO.md

2. **Check Existing Code**
   - [ ] Search for similar components
   - [ ] Review existing utilities
   - [ ] Check for reusable hooks

3. **Database First**
   - [ ] Update Prisma schema if needed
   - [ ] Run migration
   - [ ] Generate types

4. **API/Actions**
   - [ ] Create Zod validation schema
   - [ ] Implement server action or API route
   - [ ] Add error handling

5. **UI Components**
   - [ ] Use shadcn/ui primitives
   - [ ] Build feature component
   - [ ] Add loading/error states

6. **Test**
   - [ ] Manual testing
   - [ ] Write critical path tests

7. **Document**
   - [ ] Update CONTEXT.md if decisions made
   - [ ] Mark TODO items complete

---

## 🚫 Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Duplicate components | Maintenance nightmare | Search first, extend existing |
| Multiple Prisma clients | Connection pool exhaustion | Single db instance in lib/db.ts |
| Inline styles | Inconsistent UI | Use Tailwind + design tokens |
| fetch in components | No caching | Use Server Components or SWR/React Query |
| Giant components | Untestable | Extract to smaller, focused components |
| No loading states | Poor UX | Always add loading.tsx and Suspense |
| No error handling | Silent failures | try/catch + error.tsx boundaries |
| Magic strings | Typo bugs | Use enums or const objects |
| Prop drilling | Verbose code | Use React Context or Zustand |
| No TypeScript | Runtime errors | Strict mode, no `any` |

---

## ⚡ Performance Checklist

- [ ] Images use `next/image` with proper sizing
- [ ] Heavy components are lazy loaded
- [ ] Database queries are optimized (no N+1)
- [ ] Static pages use ISR or static generation
- [ ] Bundle size checked with `next build`
- [ ] Core Web Vitals measured

---

## 🔐 Security Checklist

- [ ] Environment variables for secrets
- [ ] Input validation with Zod (server-side)
- [ ] CSRF protection (Next.js handles)
- [ ] SQL injection prevented (Prisma parameterizes)
- [ ] XSS prevented (React escapes by default)
- [ ] Auth on all protected routes
- [ ] Rate limiting on API routes

---

> **Remember:** Vibe coding is about flow, not chaos. Structure enables speed. Check before creating. Extend before forking. Ship with confidence. 🚀

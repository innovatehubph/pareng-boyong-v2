# Database & Prisma Patterns

## Prisma Client Setup

```typescript
// lib/db.ts - SINGLE INSTANCE (never duplicate this file)
import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

export const db = globalForPrisma.prisma ?? new PrismaClient({
  log: process.env.NODE_ENV === 'development' 
    ? ['query', 'error', 'warn'] 
    : ['error'],
})

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = db
```

---

## Schema Patterns

### User with Auth

```prisma
// prisma/schema.prisma

model User {
  id            String    @id @default(cuid())
  email         String    @unique
  name          String?
  password      String?   // Null if OAuth only
  emailVerified DateTime?
  image         String?
  role          Role      @default(USER)
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt
  deletedAt     DateTime? // Soft delete

  // Relations
  accounts      Account[]
  sessions      Session[]
  posts         Post[]

  @@index([email])
  @@index([deletedAt])
}

enum Role {
  USER
  ADMIN
  EDITOR
}
```

### One-to-Many Relationship

```prisma
model Post {
  id          String   @id @default(cuid())
  title       String
  content     String?
  published   Boolean  @default(false)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  
  // Foreign key
  authorId    String
  author      User     @relation(fields: [authorId], references: [id], onDelete: Cascade)

  // Self-relations
  parentId    String?
  parent      Post?    @relation("PostReplies", fields: [parentId], references: [id])
  replies     Post[]   @relation("PostReplies")

  // Many-to-many
  tags        Tag[]

  @@index([authorId])
  @@index([published, createdAt])
}
```

### Many-to-Many with Explicit Join Table

```prisma
model Tag {
  id    String @id @default(cuid())
  name  String @unique
  posts Post[]
}

// Explicit join table (for extra fields)
model PostTag {
  post      Post     @relation(fields: [postId], references: [id], onDelete: Cascade)
  postId    String
  tag       Tag      @relation(fields: [tagId], references: [id], onDelete: Cascade)
  tagId     String
  addedAt   DateTime @default(now())
  addedBy   String?

  @@id([postId, tagId])
  @@index([tagId])
}
```

### Audit Log

```prisma
model AuditLog {
  id        String   @id @default(cuid())
  action    String   // CREATE, UPDATE, DELETE
  entity    String   // User, Post, etc.
  entityId  String
  oldData   Json?
  newData   Json?
  userId    String?
  user      User?    @relation(fields: [userId], references: [id])
  createdAt DateTime @default(now())

  @@index([entity, entityId])
  @@index([userId])
  @@index([createdAt])
}
```

---

## Query Patterns

### Basic CRUD

```typescript
// Create
const user = await db.user.create({
  data: {
    email: 'user@example.com',
    name: 'John Doe',
  },
})

// Read
const user = await db.user.findUnique({
  where: { id: userId },
})

// Update
const user = await db.user.update({
  where: { id: userId },
  data: { name: 'Jane Doe' },
})

// Delete
await db.user.delete({
  where: { id: userId },
})

// Soft delete
await db.user.update({
  where: { id: userId },
  data: { deletedAt: new Date() },
})
```

### Pagination

```typescript
async function getUsers(page: number = 1, limit: number = 10) {
  const skip = (page - 1) * limit

  const [users, total] = await Promise.all([
    db.user.findMany({
      where: { deletedAt: null },
      skip,
      take: limit,
      orderBy: { createdAt: 'desc' },
    }),
    db.user.count({
      where: { deletedAt: null },
    }),
  ])

  return {
    data: users,
    pagination: {
      page,
      limit,
      total,
      pages: Math.ceil(total / limit),
      hasMore: page * limit < total,
    },
  }
}
```

### Search with Filters

```typescript
interface UserFilters {
  search?: string
  role?: Role
  createdAfter?: Date
  createdBefore?: Date
}

async function searchUsers(filters: UserFilters, page: number, limit: number) {
  const where: Prisma.UserWhereInput = {
    deletedAt: null,
    ...(filters.search && {
      OR: [
        { name: { contains: filters.search, mode: 'insensitive' } },
        { email: { contains: filters.search, mode: 'insensitive' } },
      ],
    }),
    ...(filters.role && { role: filters.role }),
    ...(filters.createdAfter && { createdAt: { gte: filters.createdAfter } }),
    ...(filters.createdBefore && { createdAt: { lte: filters.createdBefore } }),
  }

  return db.user.findMany({
    where,
    skip: (page - 1) * limit,
    take: limit,
    orderBy: { createdAt: 'desc' },
  })
}
```

### Relations - Include vs Select

```typescript
// Include - adds relation to base model
const user = await db.user.findUnique({
  where: { id: userId },
  include: {
    posts: true,
    _count: { select: { posts: true } },
  },
})

// Select - precise field selection (more efficient)
const user = await db.user.findUnique({
  where: { id: userId },
  select: {
    id: true,
    name: true,
    email: true,
    posts: {
      select: { id: true, title: true },
      take: 5,
      orderBy: { createdAt: 'desc' },
    },
  },
})
```

### Transactions

```typescript
// Sequential transaction
const [post, audit] = await db.$transaction([
  db.post.create({ data: postData }),
  db.auditLog.create({ data: auditData }),
])

// Interactive transaction (for dependent operations)
const result = await db.$transaction(async (tx) => {
  const user = await tx.user.findUnique({
    where: { id: userId },
  })

  if (!user) throw new Error('User not found')

  const post = await tx.post.create({
    data: {
      ...postData,
      authorId: user.id,
    },
  })

  await tx.user.update({
    where: { id: userId },
    data: { postCount: { increment: 1 } },
  })

  return post
})
```

### Upsert

```typescript
const user = await db.user.upsert({
  where: { email: 'user@example.com' },
  update: { name: 'Updated Name' },
  create: { email: 'user@example.com', name: 'New User' },
})
```

### Aggregations

```typescript
// Count
const count = await db.user.count({
  where: { role: 'ADMIN' },
})

// Group by
const postsByAuthor = await db.post.groupBy({
  by: ['authorId'],
  _count: { id: true },
  _sum: { views: true },
  orderBy: { _count: { id: 'desc' } },
  take: 10,
})

// Aggregate
const stats = await db.post.aggregate({
  _count: true,
  _avg: { views: true },
  _max: { views: true },
  _min: { views: true },
})
```

---

## Migration Patterns

### Commands

```bash
# Create migration from schema changes
npx prisma migrate dev --name add_user_role

# Apply pending migrations (production)
npx prisma migrate deploy

# Reset database (development only!)
npx prisma migrate reset

# Generate client after schema changes
npx prisma generate

# View database
npx prisma studio
```

### Safe Migration Checklist

1. **Adding column** - Safe, nullable or with default
2. **Removing column** - Deploy code first, then migrate
3. **Renaming column** - Create new → migrate data → deploy → remove old
4. **Adding index** - Safe (Prisma uses `CREATE CONCURRENTLY`)
5. **Changing type** - Risky, may need custom migration

### Custom Migration

```typescript
// For complex data migrations, create a script
// scripts/migrate-data.ts
import { db } from '@/lib/db'

async function main() {
  // Batch update in chunks to avoid timeout
  const batchSize = 1000
  let processed = 0

  while (true) {
    const users = await db.user.findMany({
      where: { newField: null },
      take: batchSize,
    })

    if (users.length === 0) break

    await db.$transaction(
      users.map((user) =>
        db.user.update({
          where: { id: user.id },
          data: { newField: computeNewField(user) },
        })
      )
    )

    processed += users.length
    console.log(`Processed ${processed} users`)
  }
}

main()
```

---

## Performance Tips

### Avoid N+1 Queries

```typescript
// ❌ BAD - N+1 queries
const posts = await db.post.findMany()
for (const post of posts) {
  const author = await db.user.findUnique({
    where: { id: post.authorId },
  })
}

// ✅ GOOD - Single query with include
const posts = await db.post.findMany({
  include: { author: true },
})
```

### Use Select for Large Tables

```typescript
// ❌ BAD - Fetches all columns
const users = await db.user.findMany()

// ✅ GOOD - Only needed columns
const users = await db.user.findMany({
  select: {
    id: true,
    name: true,
    email: true,
  },
})
```

### Index Foreign Keys

```prisma
model Post {
  authorId String
  author   User   @relation(fields: [authorId], references: [id])

  @@index([authorId])  // Always index FKs
}
```

### Connection Pooling

```
# .env for serverless (Vercel, AWS Lambda)
DATABASE_URL="postgresql://...?pgbouncer=true&connection_limit=1"
DIRECT_URL="postgresql://..."  # For migrations
```

```prisma
datasource db {
  provider  = "postgresql"
  url       = env("DATABASE_URL")
  directUrl = env("DIRECT_URL")
}
```

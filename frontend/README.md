# Curriculum Curator Frontend

React + TypeScript frontend for the Curriculum Curator application.

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Rich Text Editor**: TipTap
- **HTTP Client**: Axios
- **Testing**: Vitest + React Testing Library
- **Linting**: ESLint
- **Formatting**: Prettier

## Quick Start

```bash
# Start the frontend (handles dependencies automatically)
./frontend.sh

# Or manually:
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:5173

## Development

### Code Quality

**IMPORTANT**: All checks must pass with 0 errors before committing.

```bash
# Linting and type checking
npm run lint              # ESLint (must show 0 errors)
npm run lint:fix          # Auto-fix linting issues
npm run type-check        # TypeScript checking (must show 0 errors)

# Formatting
npm run format            # Format with Prettier
npm run format:check      # Check formatting

# Testing
npm test                  # Run tests in watch mode
npm run test:coverage     # Generate coverage report
npm run test:ui           # Run tests with UI
```

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── Editor/      # Rich text editor
│   │   ├── Layout/      # Layout components
│   │   └── Wizard/      # Multi-step wizards
│   ├── features/        # Feature modules
│   │   ├── admin/       # Admin functionality
│   │   ├── auth/        # Authentication
│   │   ├── content/     # Content creation
│   │   ├── courses/     # Course management
│   │   ├── lrd/         # Learning Resource Documents
│   │   └── teaching/    # Teaching styles
│   ├── pages/           # Page components
│   ├── services/        # API services
│   ├── stores/          # Zustand state stores
│   ├── types/           # TypeScript type definitions
│   └── main.tsx         # Application entry point
├── public/              # Static assets
└── package.json         # Dependencies
```

## TypeScript Requirements

**CRITICAL**: This is a TypeScript-only project!

- ✅ **ALWAYS** use `.tsx` for React components
- ✅ **ALWAYS** use `.ts` for utilities
- ❌ **NEVER** create `.jsx` or `.js` files
- ✅ **Type everything**: props, state, functions
- ❌ **No `any` types** without justification

### Example Component

```typescript
// ✅ CORRECT: ComponentName.tsx
interface Props {
  id: string;
  onUpdate: (data: UpdateData) => void;
}

export const ComponentName: React.FC<Props> = ({ id, onUpdate }) => {
  // Component implementation
};
```

## Building for Production

```bash
# Build production bundle
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create a `.env.local` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
VITE_ENABLE_AI_FEATURES=true
```

## Key Features

- **Rich Text Editing** with tables and code blocks
- **Pedagogy-Aware** content creation
- **Real-time AI assistance** with streaming
- **Responsive design** with Tailwind CSS
- **Type-safe** API integration

## Testing

```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage

# Run with UI
npm run test:ui
```

## Component Guidelines

1. **Use functional components** with hooks
2. **Define TypeScript interfaces** for all props
3. **Use Tailwind CSS** for styling
4. **Import icons** from `lucide-react`
5. **Follow existing patterns** in the codebase

## State Management

Using Zustand for minimal state management:
- Authentication state in `stores/authStore.ts`
- Keep components stateless when possible
- Use React Query for server state (if needed)

## API Integration

All API calls go through `services/api.ts`:
- Configured with JWT interceptors
- Base URL from environment variable
- Automatic token refresh handling
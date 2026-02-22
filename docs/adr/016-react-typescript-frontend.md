# 16. React + TypeScript Frontend

Date: 2025-12-01

## Status

Accepted

Supersedes:
- [ADR-002: FastHTML Web Framework](002-fasthtml-web-framework.md)
- [ADR-006: Pure FastHTML Without JavaScript](006-pure-fasthtml-no-javascript.md)
- [ADR-012: Framework Migration FastHTML to NiceGUI](012-framework-migration-fasthtml-to-nicegui.md)

## Context

The Curriculum Curator project has evolved through multiple frontend framework iterations:

1. **FastHTML (ADR-002)**: Initial choice for Python-native server-rendered pages with HTMX
2. **NiceGUI (ADR-012)**: Planned migration for richer UI components (never implemented)
3. **React + TypeScript**: Current production implementation

### Why the Migrations Occurred

**FastHTML limitations discovered:**
- Complex UI interactions required increasingly convoluted HTMX patterns
- Rich text editing (TipTap) requires JavaScript - contradicts "no JS" goal (ADR-006)
- Limited ecosystem for educational UI components (drag-drop, wizards)
- Difficult to find developers familiar with FastHTML/HTMX

**NiceGUI evaluation (ADR-012):**
- Offered Python-native approach with better components
- However, still hit limitations with professional rich text editing
- Community/ecosystem smaller than React
- Decision made to adopt industry-standard React before significant NiceGUI investment

### Requirements Driving the Final Decision

1. **Rich text editing**: Professional WYSIWYG editor for educational content
2. **Complex UI patterns**: Multi-step wizards, drag-and-drop reordering
3. **Type safety**: Catch errors at compile time, not runtime
4. **Ecosystem**: Access to mature libraries (TipTap, dnd-kit, etc.)
5. **Developer availability**: React/TypeScript skills widely available
6. **API boundary**: Clean separation enables future mobile apps, integrations

## Decision

Adopt **React 18 with TypeScript** as the frontend framework, using:

| Category | Choice | Rationale |
|----------|--------|-----------|
| **Framework** | React 18.2 | Industry standard, concurrent features, large ecosystem |
| **Language** | TypeScript (strict) | Type safety, better refactoring, self-documenting |
| **Build Tool** | Vite 6.x | Fast HMR, modern ESM, minimal config |
| **Styling** | Tailwind CSS | Utility-first, consistent design, small bundle |
| **State** | Zustand | Minimal boilerplate, only for auth state |
| **Routing** | React Router 6 | Standard, type-safe routing |
| **Rich Text** | TipTap | Professional editor, extensible, Markdown support |
| **HTTP** | Axios | Interceptors for JWT, familiar API |
| **Icons** | Lucide React | Consistent, tree-shakeable |
| **Testing** | Vitest + Testing Library | Fast, React-focused |

### Architecture

```
frontend/
├── src/
│   ├── components/          # Shared UI components
│   │   ├── Editor/          # TipTap rich text editor
│   │   ├── Layout/          # Page layouts, navigation
│   │   └── Wizard/          # Multi-step flows
│   ├── features/            # Feature-based modules
│   │   ├── auth/            # Login, registration
│   │   ├── units/           # Unit management
│   │   ├── content/         # Content creation/editing
│   │   └── ...
│   ├── hooks/               # Custom React hooks
│   ├── services/            # API client, utilities
│   ├── stores/              # Zustand stores (minimal)
│   ├── types/               # TypeScript interfaces
│   └── App.tsx              # Root component, routing
├── package.json
├── tsconfig.json            # Strict TypeScript config
├── vite.config.js           # Dev server, API proxy
└── tailwind.config.js       # Design system
```

### TypeScript Configuration

Strict mode enabled with additional checks:
- `noUnusedLocals`, `noUnusedParameters`
- `noFallthroughCasesInSwitch`, `noImplicitReturns`
- `exactOptionalPropertyTypes`

**Rule**: All React components must be `.tsx` files. No `.jsx` files permitted.

### API Integration

Frontend communicates with FastAPI backend via REST:
- JWT tokens stored in memory (Zustand)
- Axios interceptors attach Authorization headers
- Vite dev server proxies `/api/*` to backend

## Consequences

### Positive

- **Rich editing**: TipTap provides professional content editing with tables, code blocks, Markdown support
- **Type safety**: TypeScript catches errors early, improves refactoring confidence
- **Ecosystem access**: Vast library of React components available
- **Developer hiring**: React/TypeScript skills are common
- **Performance**: Vite provides sub-second HMR, fast builds
- **Future-proof**: React's stability and Facebook backing
- **Mobile path**: Same API can serve React Native app later

### Negative

- **Two languages**: Python backend + TypeScript frontend requires dual expertise
- **Build complexity**: Additional build step vs. server-rendered
- **Bundle size**: JavaScript bundle must be downloaded (mitigated by code splitting)
- **SEO**: SPA requires additional work for SEO (not critical for this app)

### Neutral

- **Learning curve**: Team must learn React patterns (offset by documentation)
- **State management**: Zustand is minimal; may need more structure as app grows
- **Testing strategy**: Different tools than Python backend

## Alternatives Considered

### Continue with FastHTML + HTMX

- **Why rejected**: Rich text editing requires JavaScript regardless; ecosystem too limited for complex UI

### NiceGUI (ADR-012)

- **Why rejected**: Still hit limitations with professional editing; smaller ecosystem; Python-only locked us in

### Vue.js

- **Why rejected**: Smaller ecosystem than React; less TypeScript maturity at decision time

### Svelte/SvelteKit

- **Why rejected**: Smaller ecosystem; fewer available developers; less mature

### Next.js (React SSR)

- **Why rejected**: Added complexity; SEO not critical for authenticated app; Vite simpler for SPA

## Implementation Notes

### Development Workflow

```bash
# Start frontend dev server (proxies to backend)
cd frontend && npm run dev

# Type checking
npm run type-check

# Linting and formatting
npm run lint
npm run format

# Testing
npm test
npm run test:coverage
```

### Code Quality Gates

All checks must pass before committing:
- `npm run lint` - 0 ESLint errors
- `npm run type-check` - 0 TypeScript errors
- `npm run format:check` - Prettier compliance

### Key Libraries Installed

```json
{
  "@tiptap/react": "^2.1.13",
  "@tiptap/starter-kit": "^2.1.13",
  "@dnd-kit/core": "^6.1.0",
  "zustand": "^4.4.7",
  "react-router-dom": "^6.21.0",
  "axios": "^1.7.7",
  "tailwindcss": "^3.4.0",
  "lucide-react": "^0.309.0"
}
```

## References

- [ADR-002: FastHTML Web Framework](002-fasthtml-web-framework.md) (Superseded)
- [ADR-006: Pure FastHTML Without JavaScript](006-pure-fasthtml-no-javascript.md) (Superseded)
- [ADR-012: Framework Migration FastHTML to NiceGUI](012-framework-migration-fasthtml-to-nicegui.md) (Superseded)
- [ADR-015: Content Format and Export Strategy](015-content-format-and-export-strategy.md)
- [React Documentation](https://react.dev/)
- [TipTap Documentation](https://tiptap.dev/)
- [Vite Documentation](https://vitejs.dev/)

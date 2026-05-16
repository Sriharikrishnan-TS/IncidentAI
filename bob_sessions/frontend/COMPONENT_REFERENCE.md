# IncidentOS Component Reference

## Component Hierarchy

```
App
├── RootLayout
│   ├── Sidebar
│   │   ├── Logo
│   │   ├── NavLinks[]
│   │   │   └── NavLink (icon + label)
│   │   └── RepoSelector
│   ├── Navbar
│   │   ├── SearchBar
│   │   └── UserMenu
│   └── PageContent
│       ├── UploadPage
│       │   └── RepoUploadCard
│       │       ├── DragDropZone
│       │       ├── URLInput
│       │       └── UploadButton
│       ├── DashboardPage
│       │   ├── StatsGrid
│       │   │   └── StatsCard[] (4x)
│       │   ├── FragileServicesSection
│       │   │   └── FragileServiceCard[]
│       │   ├── RecentIncidentsSection
│       │   │   └── IncidentCard[]
│       │   └── DependencyStatsSection
│       │       └── DependencyChart
│       ├── FragilityPage
│       │   ├── FragilityChart
│       │   ├── FilterControls
│       │   └── ServiceScoreCard[]
│       ├── GraphsPage
│       │   ├── DependencyGraph (React Flow)
│       │   ├── GraphControls
│       │   └── NodeDetailsPanel
│       ├── MentorPage
│       │   ├── ChatInterface
│       │   │   ├── MessageList
│       │   │   │   └── MessageBubble[]
│       │   │   ├── TypingIndicator
│       │   │   └── SuggestedQuestions
│       │   └── ChatInput
│       └── InvestigationPage
│           ├── IncidentForm
│           ├── Timeline
│           │   └── TimelineEvent[]
│           ├── RootCauseCard
│           └── RecommendedActions
```

## Component Quick Reference

### Layout Components

#### Sidebar

- **Path**: `components/layout/Sidebar.tsx`
- **Props**: None (uses context for active route)
- **Features**: Navigation, repo selector, collapsible
- **Styling**: Fixed left, dark glass effect, 256px width

#### Navbar

- **Path**: `components/layout/Navbar.tsx`
- **Props**: None
- **Features**: Search, user menu, branding
- **Styling**: Fixed top, glass effect, 64px height

### UI Components (shadcn/ui)

#### Card

- **Usage**: Container for content sections
- **Variants**: Default, glass (with backdrop-blur)
- **Props**: className, children

#### Badge

- **Usage**: Status indicators, tags
- **Variants**: default, secondary, destructive, outline
- **Props**: variant, children

#### Button

- **Usage**: Actions, navigation
- **Variants**: default, destructive, outline, ghost, link
- **Props**: variant, size, children, onClick

#### Skeleton

- **Usage**: Loading placeholders
- **Props**: className (for custom sizing)

### Dashboard Components

#### StatsCard

- **Path**: `components/dashboard/StatsCard.tsx`
- **Props**:
  - `icon`: LucideIcon
  - `label`: string
  - `value`: number | string
  - `change?`: number (percentage)
  - `trend?`: 'up' | 'down'
- **Styling**: Glass card, gradient border on hover

#### FragileServiceCard

- **Path**: `components/dashboard/FragileServiceCard.tsx`
- **Props**:
  - `service`: string
  - `score`: number (0-10)
  - `reason`: string
  - `onClick?`: () => void
- **Features**: Score visualization, color-coded

#### IncidentCard

- **Path**: `components/dashboard/IncidentCard.tsx`
- **Props**:
  - `title`: string
  - `severity`: 'low' | 'medium' | 'high' | 'critical'
  - `affectedServices`: string[]
  - `timestamp`: string
- **Features**: Severity badge, service chips

### Upload Components

#### RepoUploadCard

- **Path**: `components/upload/RepoUploadCard.tsx`
- **Props**:
  - `onUpload`: (repoUrl: string) => Promise<void>
- **Features**: Drag-and-drop, URL input, progress indicator
- **State**: uploading, progress, error

### Fragility Components

#### FragilityChart

- **Path**: `components/fragility/FragilityChart.tsx`
- **Props**:
  - `data`: FragilityScore[]
- **Library**: Recharts (BarChart)
- **Features**: Color-coded bars, tooltips, responsive

#### ServiceScoreCard

- **Path**: `components/fragility/ServiceScoreCard.tsx`
- **Props**:
  - `service`: string
  - `score`: number
  - `reasons`: string[]
  - `metrics?`: object
- **Features**: Expandable details, metric breakdown

### Graph Components

#### DependencyGraph

- **Path**: `components/graphs/DependencyGraph.tsx`
- **Props**:
  - `nodes`: GraphNode[]
  - `edges`: GraphEdge[]
  - `onNodeClick?`: (nodeId: string) => void
- **Library**: React Flow
- **Features**: Custom nodes, zoom, pan, minimap

### Mentor Components

#### ChatInterface

- **Path**: `components/mentor/ChatInterface.tsx`
- **Props**:
  - `repoId`: string
- **State**: messages, loading, input
- **Features**: Auto-scroll, typing indicator

#### MessageBubble

- **Path**: `components/mentor/MessageBubble.tsx`
- **Props**:
  - `message`: string
  - `sender`: 'user' | 'ai'
  - `timestamp`: string
- **Styling**: Right-aligned (user), left-aligned (AI)

#### ChatInput

- **Path**: `components/mentor/ChatInput.tsx`
- **Props**:
  - `onSend`: (message: string) => void
  - `disabled?`: boolean
- **Features**: Textarea, send button, keyboard shortcuts

### Investigation Components

#### Timeline

- **Path**: `components/investigation/Timeline.tsx`
- **Props**:
  - `events`: TimelineEvent[]
- **Features**: Vertical timeline, event cards

#### TimelineEvent

- **Path**: `components/investigation/TimelineEvent.tsx`
- **Props**:
  - `event`: TimelineEvent
- **Features**: Icon, timestamp, expandable details

## Custom Hooks

### useDashboard

```typescript
const { data, loading, error } = useDashboard(repoId);
```

Returns dashboard data for a repository.

### useFragility

```typescript
const { scores, loading, error } = useFragility(repoId);
```

Returns fragility scores for services.

### useGraph

```typescript
const { nodes, edges, loading, error } = useGraph(repoId);
```

Returns dependency graph data.

### useMentor

```typescript
const { messages, sendMessage, loading } = useMentor(repoId);
```

Manages mentor chat state and messages.

### useInvestigation

```typescript
const { investigate, result, loading, error } = useInvestigation(repoId);
```

Handles investigation requests and results.

## Styling Utilities

### Glass Effect

```typescript
className = "bg-slate-800/50 backdrop-blur-md border border-slate-700/50";
```

### Gradient Border

```typescript
className =
  "border-2 border-transparent bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-border";
```

### Score Color

```typescript
function getScoreColor(score: number): string {
  if (score >= 9) return "text-red-500";
  if (score >= 7) return "text-orange-500";
  if (score >= 4) return "text-yellow-500";
  return "text-emerald-500";
}
```

### Severity Color

```typescript
function getSeverityColor(severity: string): string {
  switch (severity) {
    case "critical":
      return "bg-red-500";
    case "high":
      return "bg-orange-500";
    case "medium":
      return "bg-yellow-500";
    case "low":
      return "bg-blue-500";
    default:
      return "bg-gray-500";
  }
}
```

## Animation Patterns

### Page Transition

```typescript
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3 }}
>
  {children}
</motion.div>
```

### Card Hover

```typescript
<motion.div
  whileHover={{ scale: 1.02 }}
  transition={{ duration: 0.2 }}
>
  {children}
</motion.div>
```

### Stagger List

```typescript
<motion.div
  variants={{
    animate: {
      transition: { staggerChildren: 0.1 }
    }
  }}
  initial="initial"
  animate="animate"
>
  {items.map(item => (
    <motion.div
      key={item.id}
      variants={{
        initial: { opacity: 0, x: -20 },
        animate: { opacity: 1, x: 0 }
      }}
    >
      {item.content}
    </motion.div>
  ))}
</motion.div>
```

## Icon Usage (Lucide React)

```typescript
import {
  Upload,
  LayoutDashboard,
  AlertTriangle,
  Network,
  MessageSquare,
  Search,
  TrendingUp,
  TrendingDown,
  GitBranch,
  Database,
  Server,
} from "lucide-react";
```

### Navigation Icons

- Upload: `<Upload className="w-5 h-5" />`
- Dashboard: `<LayoutDashboard className="w-5 h-5" />`
- Fragility: `<AlertTriangle className="w-5 h-5" />`
- Graphs: `<Network className="w-5 h-5" />`
- Mentor: `<MessageSquare className="w-5 h-5" />`
- Investigation: `<Search className="w-5 h-5" />`

### Stats Icons

- Services: `<Server className="w-6 h-6" />`
- Dependencies: `<GitBranch className="w-6 h-6" />`
- Database: `<Database className="w-6 h-6" />`

## Responsive Breakpoints

```typescript
// Mobile: < 640px
className = "flex-col md:flex-row";

// Tablet: 640px - 1024px
className = "hidden md:block lg:hidden";

// Desktop: > 1024px
className = "hidden lg:block";
```

## Common Patterns

### Loading State

```typescript
{loading ? (
  <div className="space-y-4">
    <Skeleton className="h-20 w-full" />
    <Skeleton className="h-20 w-full" />
  </div>
) : (
  <div>{content}</div>
)}
```

### Error State

```typescript
{error && (
  <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-4">
    <p className="text-red-400">{error.message}</p>
  </div>
)}
```

### Empty State

```typescript
{data.length === 0 && (
  <div className="text-center py-12 text-slate-400">
    <p>No data available</p>
  </div>
)}
```

This reference guide provides quick access to all component specifications and common patterns used throughout the IncidentOS frontend.

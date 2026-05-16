# IncidentOS Frontend

AI-Powered Engineering Intelligence Platform - Frontend Application

## 🚀 Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **UI Components**: Custom components with shadcn/ui patterns
- **Icons**: Lucide React
- **State Management**: React hooks + localStorage

## 📁 Project Structure

```
frontend/
├── app/                      # Next.js App Router pages
│   ├── layout.tsx           # Root layout with Sidebar + Navbar
│   ├── page.tsx             # Home page
│   ├── upload/              # Repository upload page
│   ├── dashboard/           # Main dashboard
│   ├── fragility/           # Fragility analysis
│   ├── graphs/              # Dependency graph visualization
│   ├── mentor/              # AI mentor chat
│   └── investigation/       # Investigation timeline
├── components/
│   ├── layout/              # Layout components (Sidebar, Navbar)
│   └── ui/                  # Reusable UI components
├── services/
│   └── mockData.ts          # Mocked API responses
├── types/
│   └── api.ts               # TypeScript type definitions
└── lib/
    ├── utils.ts             # Utility functions
    └── constants.ts         # Helper functions for styling
```

## 🎨 Features Implemented

### ✅ Core Pages

1. **Home Page** (`/`)
   - Hero section with gradient text
   - Feature cards with navigation
   - Stats overview

2. **Upload Page** (`/upload`)
   - Repository URL input
   - Upload button with loading state
   - Example repositories
   - Success navigation to dashboard

3. **Dashboard** (`/dashboard`)
   - Stats cards (Services, Dependencies, Incidents, Avg Fragility)
   - Fragile services list with scores
   - Recent incidents with severity badges
   - Quick action to mentor

4. **Fragility Analysis** (`/fragility`)
   - Overview stats (High/Medium/Low risk)
   - Service cards with fragility scores
   - Metric bars (Commit Churn, Dependency Centrality, Test Coverage)
   - Sort by score or name

5. **Dependency Graph** (`/graphs`)
   - Simplified graph visualization
   - Interactive node selection
   - Node details panel with connections
   - Stats overview

6. **AI Mentor** (`/mentor`)
   - Chat interface with message bubbles
   - Suggested questions
   - Real-time message updates
   - Auto-scroll to latest message

7. **Investigation** (`/investigation`)
   - Incident input form
   - Root cause analysis with confidence score
   - Event timeline with icons
   - Recommended actions checklist

### ✅ Layout Components

- **Sidebar**: Fixed left navigation with active state highlighting
- **Navbar**: Top bar with branding and user menu
- **Responsive**: Works on desktop, tablet, and mobile

### ✅ UI Components

- **Card**: Container with glassmorphism effect
- **Badge**: Status indicators with variants
- **Skeleton**: Loading placeholders
- **Button**: Action buttons with variants

### ✅ Design Features

- **Dark Theme**: Slate color palette with dark backgrounds
- **Glassmorphism**: Backdrop blur effects on cards
- **Gradient Accents**: Blue to purple gradients throughout
- **Color Coding**:
  - Score colors (emerald/yellow/orange/red)
  - Severity colors (blue/yellow/orange/red)
- **Smooth Transitions**: Hover effects and animations
- **Responsive Design**: Mobile-first approach

## 🔧 Setup & Installation

1. **Install dependencies**:

```bash
npm install
```

2. **Install additional packages** (if not already installed):

```bash
npm install framer-motion recharts reactflow lucide-react
```

3. **Run development server**:

```bash
npm run dev
```

4. **Open browser**:
   Navigate to `http://localhost:3000`

## 📊 Mock Data

All pages use mocked API responses from `services/mockData.ts`:

- `mockUploadRepo()` - Repository upload
- `mockDashboardData()` - Dashboard statistics
- `mockFragilityData()` - Fragility scores
- `mockDependencyGraph()` - Dependency graph data
- `mockMentorQuery()` - AI mentor responses
- `mockInvestigation()` - Investigation results

## 🎯 Key Features

### Modern UI/UX

- Clean, minimal design inspired by GitHub, Linear, and Vercel
- Smooth animations and transitions
- Interactive elements with hover states
- Loading states with skeleton components

### Developer-Focused

- Type-safe with TypeScript
- Modular component structure
- Reusable utilities and helpers
- Clean code organization

### AI-Powered Intelligence

- Fragility scoring system
- Root cause analysis
- AI mentor for guidance
- Dependency visualization

## 🚧 Future Enhancements

- [ ] Add React Flow for advanced graph visualization
- [ ] Implement Recharts for data visualization
- [ ] Add Framer Motion for advanced animations
- [ ] Create custom hooks for data fetching
- [ ] Add error boundaries
- [ ] Implement real backend API integration
- [ ] Add user authentication
- [ ] Add real-time updates via WebSocket
- [ ] Add export functionality for reports
- [ ] Add filtering and search capabilities

## 📝 Notes

- Currently uses localStorage for demo repo_id storage
- All API calls are mocked with simulated delays
- Designed for easy backend integration (just replace mock functions)
- Fully responsive and works on all screen sizes

## 🎨 Color Palette

- **Background**: slate-950, slate-900
- **Cards**: slate-800/50 with backdrop-blur
- **Text**: slate-100, slate-300, slate-400
- **Accents**: blue-500, purple-500, emerald-500
- **Borders**: slate-700, slate-800

## 🔗 Navigation

- `/` - Home page
- `/upload` - Upload repository
- `/dashboard` - Main dashboard
- `/fragility` - Fragility analysis
- `/graphs` - Dependency graph
- `/mentor` - AI mentor chat
- `/investigation` - Incident investigation

---

Built with ❤️ for modern engineering teams

# IncidentOS Frontend - Complete Implementation Plan

## 📋 Project Overview

**Goal**: Build a complete, modern frontend for IncidentOS - an AI-powered engineering intelligence platform.

**Tech Stack**:

- Next.js 15 (App Router) + TypeScript
- TailwindCSS + shadcn/ui
- Recharts (charts)
- React Flow (graphs)
- Framer Motion (animations)
- Lucide React (icons)

**Design Inspiration**: GitHub, Linear, Vercel, 21st.dev
**Theme**: Dark, minimal, developer-focused, glassmorphism

## 📁 Current State

The frontend folder exists with:

- ✅ Next.js project initialized
- ✅ TailwindCSS configured
- ✅ Basic folder structure (app/, components/, hooks/, lib/, services/)
- ✅ Placeholder pages created
- ✅ Basic button component
- ⚠️ All pages are empty placeholders
- ⚠️ No UI components implemented
- ⚠️ No data services or types defined

## 🎯 Implementation Plan (27 Tasks)

### Phase 1: Foundation Setup (Tasks 1-6)

**Status**: Partially Complete

1. ✅ Initialize Next.js project with TypeScript
2. ✅ Set up TailwindCSS and shadcn/ui configuration
3. ✅ Create project folder structure
4. ⏳ Install additional dependencies
   - framer-motion
   - recharts
   - reactflow
   - lucide-react
   - shadcn/ui components (card, badge, skeleton, input, etc.)
5. ⏳ Define TypeScript interfaces for API contracts
   - Create `types/api.ts` with all API response/request types
   - Create domain-specific type files
6. ⏳ Create API service layer with mocked data
   - `services/mockData.ts` with all mock functions
   - Individual service files for each domain

### Phase 2: Layout Components (Tasks 7-9)

**Status**: Not Started

7. ⏳ Build Sidebar component
   - Navigation links with icons
   - Active state highlighting
   - Repository selector
   - Collapsible on mobile
8. ⏳ Build Navbar component
   - Logo/branding
   - Search bar (optional)
   - User menu
   - Glassmorphism styling
9. ⏳ Update root layout
   - Integrate Sidebar and Navbar
   - Proper spacing and responsive layout

### Phase 3: Core UI Components (Tasks 10-12)

**Status**: Not Started

10. ⏳ Create reusable Card component
    - Glass effect variant
    - Gradient border on hover
11. ⏳ Create LoadingSkeleton component
    - Multiple size variants
    - Animated shimmer effect
12. ⏳ Create Badge component
    - Severity variants (low, medium, high, critical)
    - Color-coded

### Phase 4: Upload Page (Task 13)

**Status**: Not Started

13. ⏳ Implement repository upload page
    - Drag-and-drop zone
    - URL input field
    - Upload button with loading state
    - Success/error messages
    - Progress indicator

### Phase 5: Dashboard Page (Tasks 14-17)

**Status**: Not Started

14. ⏳ Build dashboard page with overview cards
    - Stats cards (services, dependencies, incidents)
    - Grid layout
15. ⏳ Add fragile services section
    - Service cards with scores
    - Color-coded risk levels
    - Click to view details
16. ⏳ Add recent incidents section
    - Incident cards
    - Severity badges
    - Affected services chips
    - Timestamps
17. ⏳ Add dependency statistics
    - Visual chart (bar/pie)
    - Service distribution

### Phase 6: Fragility Page (Task 18)

**Status**: Not Started

18. ⏳ Build fragility analysis page
    - Bar chart with Recharts
    - Service score cards
    - Detailed metrics breakdown
    - Sorting and filtering controls

### Phase 7: Graphs Page (Task 19)

**Status**: Not Started

19. ⏳ Implement dependency graph page
    - React Flow canvas
    - Custom node styling
    - Interactive nodes
    - Zoom and pan controls
    - Minimap
    - Node details panel

### Phase 8: Mentor Page (Task 20)

**Status**: Not Started

20. ⏳ Create mentor chat page
    - Chat interface with message list
    - User/AI message bubbles
    - Chat input with send button
    - Suggested questions
    - Typing indicator
    - Auto-scroll

### Phase 9: Investigation Page (Task 21)

**Status**: Not Started

21. ⏳ Build investigation timeline page
    - Incident input form
    - Vertical timeline
    - Timeline events with icons
    - Root cause card
    - Confidence score
    - Recommended actions checklist

### Phase 10: Polish & Optimization (Tasks 22-27)

**Status**: Not Started

22. ⏳ Add smooth animations
    - Page transitions
    - Card hover effects
    - Stagger animations for lists
23. ⏳ Implement dark theme styling
    - Glassmorphism effects
    - Gradient highlights
    - Color-coded elements
24. ⏳ Add responsive design
    - Mobile breakpoints
    - Tablet breakpoints
    - Collapsible sidebar
25. ⏳ Create custom hooks
    - useDashboard
    - useFragility
    - useGraph
    - useMentor
    - useInvestigation
26. ⏳ Add error boundaries and error handling
    - Error boundary component
    - Error state UI
    - Toast notifications
27. ⏳ Test all pages and components
    - Functionality testing
    - UX testing
    - Responsive testing

## 📚 Documentation Created

1. **ARCHITECTURE.md** - Complete system architecture
   - Component structure
   - Data flow diagrams
   - Folder organization
   - Design patterns

2. **IMPLEMENTATION_GUIDE.md** - Detailed implementation specs
   - Dependencies to install
   - TypeScript type definitions
   - Mock data services
   - Component specifications
   - Styling guidelines
   - Animation patterns
   - Custom hooks patterns

3. **COMPONENT_REFERENCE.md** - Quick reference guide
   - Component hierarchy
   - Props and usage
   - Styling utilities
   - Common patterns
   - Icon usage

## 🎨 Design System

### Colors

- **Background**: slate-950, slate-900
- **Cards**: slate-800/50 with backdrop-blur
- **Text**: slate-100, slate-300
- **Accents**: blue-500, purple-500, emerald-500
- **Borders**: slate-700, slate-600

### Score Colors

- 0-3: emerald-500 (low risk)
- 4-6: yellow-500 (medium risk)
- 7-8: orange-500 (high risk)
- 9-10: red-500 (critical risk)

### Severity Colors

- Low: blue-500
- Medium: yellow-500
- High: orange-500
- Critical: red-500

## 🔄 Data Flow

```
Component → Custom Hook → Service Layer → Mock Data → Service Layer → Hook → Component
```

## 📦 Key Dependencies to Install

```bash
npm install framer-motion recharts reactflow lucide-react

# shadcn/ui components
npx shadcn-ui@latest add card badge skeleton input textarea avatar dropdown-menu dialog toast progress separator
```

## 🚀 Getting Started

1. **Review Documentation**
   - Read ARCHITECTURE.md for system overview
   - Read IMPLEMENTATION_GUIDE.md for detailed specs
   - Use COMPONENT_REFERENCE.md as quick reference

2. **Install Dependencies**
   - Run npm install commands
   - Add shadcn/ui components

3. **Start with Foundation**
   - Create TypeScript types
   - Set up mock data services
   - Create custom hooks

4. **Build Layout**
   - Implement Sidebar
   - Implement Navbar
   - Update root layout

5. **Implement Pages**
   - Follow the task order
   - Test each page as you build
   - Use mock data for all API calls

6. **Polish**
   - Add animations
   - Ensure responsive design
   - Test thoroughly

## ✅ Success Criteria

- [ ] All 6 pages fully functional
- [ ] Modern, dark-themed UI
- [ ] Smooth animations and transitions
- [ ] Responsive on all devices
- [ ] Type-safe TypeScript code
- [ ] Reusable component library
- [ ] Clean, maintainable code structure
- [ ] Mock data integration working
- [ ] Loading and error states implemented
- [ ] Glassmorphism and gradient effects applied

## 🎯 Next Steps

**Ready to implement?** Switch to Code mode to start building:

1. Install dependencies
2. Create type definitions
3. Build mock data services
4. Implement layout components
5. Build page components
6. Add polish and animations

**Estimated Timeline**: 3-4 days for complete implementation

## 📝 Notes

- Focus on frontend only - no backend logic
- Use mocked data for all API calls
- Prioritize modern, clean UI
- Follow design inspiration from GitHub, Linear, Vercel
- Keep components modular and reusable
- Ensure type safety throughout
- Test on multiple screen sizes

---

**This plan provides a complete roadmap for building the IncidentOS frontend. All specifications, code examples, and guidelines are documented in the accompanying files.**

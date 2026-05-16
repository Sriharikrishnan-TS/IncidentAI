# IncidentOS Frontend - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies

```bash
cd IncidentOS/frontend
npm install
```

### Step 2: Run Development Server

```bash
npm run dev
```

### Step 3: Open Browser

Navigate to `http://localhost:3000`

---

## 📱 Using the Application

### 1. Home Page (`/`)

- Click **"Get Started"** to upload a repository
- Or click **"View Demo"** to see the dashboard with mock data

### 2. Upload Repository (`/upload`)

- Enter a GitHub repository URL (or use an example)
- Click **"Upload Repository"**
- You'll be redirected to the dashboard

### 3. Dashboard (`/dashboard`)

- View service statistics
- See fragile services with scores
- Check recent incidents
- Click **"Ask Mentor"** for AI guidance

### 4. Fragility Analysis (`/fragility`)

- View all services sorted by fragility score
- See detailed metrics for each service
- Sort by score or name

### 5. Dependency Graph (`/graphs`)

- Click on nodes to see details
- View connections and dependencies
- Explore service relationships

### 6. AI Mentor (`/mentor`)

- Type questions about your codebase
- Use suggested questions for quick start
- Get AI-powered guidance

### 7. Investigation (`/investigation`)

- Describe an incident
- Click **"Start Investigation"**
- View root cause analysis and timeline
- See recommended actions

---

## 🎨 Key Features to Try

### Interactive Elements

- **Hover Effects**: Hover over cards and buttons
- **Active States**: Click navigation items to see active highlighting
- **Loading States**: Watch skeleton loaders during data fetch
- **Color Coding**: Notice score colors (green → yellow → orange → red)

### Navigation

- Use the **sidebar** for main navigation
- Click the **IncidentOS logo** to return home
- All pages are interconnected

### Data Flow

1. Upload a repository (stores repo_id in localStorage)
2. View dashboard with that repository's data
3. Explore other pages - all use the same repo_id
4. Data persists across page refreshes

---

## 🛠️ Development Commands

```bash
# Install dependencies
npm install

# Run development server (with hot reload)
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint
```

---

## 📂 Project Structure Overview

```
frontend/
├── app/                    # Pages (Next.js App Router)
│   ├── page.tsx           # Home
│   ├── upload/            # Upload page
│   ├── dashboard/         # Dashboard
│   ├── fragility/         # Fragility analysis
│   ├── graphs/            # Dependency graph
│   ├── mentor/            # AI mentor
│   └── investigation/     # Investigation
├── components/
│   ├── layout/            # Sidebar, Navbar
│   └── ui/                # Card, Badge, Skeleton, Button
├── services/
│   └── mockData.ts        # Mock API responses
├── types/
│   └── api.ts             # TypeScript types
└── lib/
    ├── utils.ts           # Utilities
    └── constants.ts       # Helper functions
```

---

## 🎯 What to Explore

### For Developers

1. Check `types/api.ts` for all TypeScript interfaces
2. Look at `services/mockData.ts` for mock API implementation
3. Explore `components/` for reusable UI components
4. Review `lib/constants.ts` for styling helpers

### For Designers

1. Notice the dark theme with glassmorphism
2. Check gradient accents (blue → purple)
3. See color-coded scores and severity levels
4. Observe smooth transitions and hover effects

### For Product Managers

1. Test the complete user flow (upload → dashboard → analysis)
2. Try the AI mentor chat interface
3. Explore the investigation timeline
4. Check the dependency graph visualization

---

## 💡 Tips & Tricks

### Mock Data

- All data is mocked with realistic delays
- Refresh the page to see loading states
- Data persists in localStorage (repo_id)

### Customization

- Edit `services/mockData.ts` to change mock responses
- Modify `lib/constants.ts` for color schemes
- Update `components/` for UI changes

### Navigation

- Use sidebar for main navigation
- All pages are accessible from any page
- Home page provides overview of all features

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Kill process on port 3000
npx kill-port 3000

# Or use a different port
npm run dev -- -p 3001
```

### Dependencies Not Installing

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Build Errors

```bash
# Check TypeScript errors
npm run build

# Fix linting issues
npm run lint -- --fix
```

---

## 📚 Additional Resources

- **README.md** - Complete project documentation
- **ARCHITECTURE.md** - System architecture overview
- **IMPLEMENTATION_GUIDE.md** - Detailed implementation specs
- **COMPONENT_REFERENCE.md** - Component quick reference
- **IMPLEMENTATION_SUMMARY.md** - What was built

---

## 🎉 You're Ready!

The application is fully functional with mock data. Explore all pages, try different features, and see how everything works together.

**Next Steps:**

1. Explore all 7 pages
2. Try the AI mentor chat
3. Upload a "repository" and see the flow
4. Check the code to understand the implementation

**Happy exploring!** 🚀

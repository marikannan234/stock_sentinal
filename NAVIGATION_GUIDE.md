# 🧭 Premium UI Navigation Guide

## Quick Start

### 1️⃣ Start the Application

```bash
# Development
npm run dev

# Open http://localhost:3000
```

---

## 📍 User Flows

### 🔓 New User Flow
```
localhost:3000 (Home)
    ↓
/auth/premium (Login/Register toggle)
    ├─ Click "Create Account" or tab to register
    ├─ Enter: Full Name, Email, Password
    └─ Submit → Auto-login → /dashboard

/dashboard
    └─ View portfolio, market data, alerts
```

### 👤 Existing User Flow
```
localhost:3000 (Home)
    ↓
/auth/premium (Show login by default)
    ├─ Enter: Email, Password
    └─ Submit → /dashboard

/dashboard
    └─ Full access to all features
```

### 🚪 Logout Flow
```
/dashboard
    ↓
Click logout (sidebar, bottom)
    ↓
/login (or /auth/premium)
```

---

## 🗺️ Route Map

### Public Routes (Auth)
```
/auth/login              (Fallback)
/auth/register           (Fallback)
/auth/premium            ⭐ PRIMARY - Use this
├─ Login tab
├─ Register tab
└─ Animated transition
```

### Protected Routes (Auth Required)
```
/dashboard               ⭐ PRIMARY - Premium dashboard
├─ Sidebar navigation
├─ Portfolio metrics
├─ Market overview
├─ Alerts & news
└─ Auto-redirects to /login if no token
```

### Utility Routes
```
/                        Home page
/_not-found              404 page
```

---

## 🎯 Component Navigation

### From Home (/)
```
Button: "Get Started"
    ↓
/auth/premium (Login)
```

### From /auth/premium
```
📱 Mobile:
  ├─ Tab between "Sign In" and "Register"
  └─ Different content per tab

💻 Desktop:
  ├─ Left: Login form
  ├─ Right: Register form
  ├─ Animated overlay
  └─ Click overlay text to switch
```

### From /dashboard
```
Sidebar (Left):
  ├─ Dashboard (active)
  ├─ Watchlist
  ├─ Portfolio
  ├─ Alerts
  ├─ News
  ├─ Settings
  ├─ Support
  └─ Logout

TopBar (Top):
  ├─ Live ticker ribbon (scrolls)
  ├─ Search bar (center)
  ├─ Notifications
  └─ User profile

Main Content:
  ├─ Portfolio summary (3 cards)
  ├─ Market overview chart
  ├─ Top gainers/losers
  ├─ Alerts feed
  └─ Market intelligence
```

---

## 🔐 Auth State Management

### How It Works
```
User Login
    ↓
POST /auth/login-json
    ↓
Token returned
    ↓
Zustand store updates (useAuthStore)
    ↓
localStorage.setItem('stocksentinel_token', token)
    ↓
Router pushes to /dashboard
    ↓
Dashboard layout checks token
    ↓
If valid → Show dashboard
If invalid → Redirect to /login
```

### Session Persistence
```
Page Reload
    ↓
AuthInitializer.tsx runs
    ↓
Loads token from localStorage
    ↓
useAuthStore.hydrate()
    ↓
Token still valid
    ↓
Stay on /dashboard
```

### Logout
```
Click Logout
    ↓
useAuthStore.logout()
    ↓
localStorage.removeItem('stocksentinel_token')
    ↓
Router.push('/login')
    ↓
New session required
```

---

## 📱 Responsive Design

### Desktop (> 768px)
```
Sidebar (collapsible, hover to expand)
  + TopBar (full width)
  + Main content (full width)
  + Animated transitions
```

### Mobile (< 768px)
```
TopBar (sticky, full width)
  + Main content (full width)
  + Sidebar (hidden until click)
  + Touch-friendly buttons
```

---

## 🎨 Dark Mode

- Dark mode is **always enabled**
- All components use dark color scheme
- Design System colors:
  - Primary: `#adc6ff` (blue)
  - Secondary: `#4edea3` (green)
  - Tertiary: `#ffb3ad` (red/pink)
  - Surface: `#131315` (dark)

---

## 🔄 Common Tasks

### Change Default Auth Page
Currently: `/auth/premium`

To use `/auth/login` instead:
1. Update links in home page
2. Or create redirect in middleware

### Add New Dashboard Page
```tsx
// Create: app/dashboard/watchlist/page.tsx
import { Sidebar } from '@/components/dashboard/Sidebar';
import { TopBar } from '@/components/dashboard/TopBar';

export default function WatchlistPage() {
  return (
    <div>
      <TopBar />
      <Sidebar currentPage="watchlist" />
      {/* Your content */}
    </div>
  );
}
```

### Update Portfolio Data
```tsx
// In app/dashboard/page.tsx
const portfolioData = await fetch('/api/portfolio').then(r => r.json());
```

---

## 🐛 Troubleshooting Navigation

### Dashboard shows loading spinner forever
- Check if token exists: DevTools → Application → localStorage
- Verify backend `/auth/login-json` is working
- Check AuthInitializer in root layout

### Can't see sidebar on mobile
- Sidebar is hidden by default
- It expands on hover on desktop
- May need to check responsive classes

### Auth page not appearing
- Check if route exists: `/app/(auth)/premium/page.tsx`
- Verify file wasn't accidentally deleted
- Clear `.next` folder and rebuild

### Can't login
- Verify backend is running
- Check if `/auth/login-json` endpoint works
- Check CORS configuration
- Check browser console for errors

---

## 📊 Navigation Statistics

```
Total Routes:      6
Public Routes:     4
Protected Routes:  1
Utility Routes:    1

Total Components:  5
UI Components:     5
Dashboard Comp:    2
Shared Comp:       1

Build Size:        113 KB (home)
Dashboard Size:    135 KB (with data)
```

---

## 🚀 Production Deployment

### Before Deploy
1. ✅ Run build: `npm run build`
2. ✅ Test routes in browser
3. ✅ Verify auth flow works
4. ✅ Check backend connectivity
5. ✅ Test on both mobile and desktop

### Deploy Commands
```bash
# Build static export
npm run build

# Start production server
npm start

# Or use Docker (if configured)
docker-compose up
```

### Environment Variables
```
NEXT_PUBLIC_API_URL=https://your-backend.com
```

---

## 📞 Support

See:
- [PREMIUM_UI_INTEGRATION.md](PREMIUM_UI_INTEGRATION.md) - Integration details
- [PROJECT_CLEANUP_COMPLETE.md](PROJECT_CLEANUP_COMPLETE.md) - Cleanup summary
- Next.js Docs: https://nextjs.org/docs

---

**Last Updated:** April 5, 2026
**Version:** 1.0 - Premium UI Edition

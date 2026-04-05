# Stock Sentinel Frontend - Complete Documentation

## 🎯 Overview

A **professional, production-grade trading platform frontend** built with Next.js, React, Tailwind CSS, and Recharts. Designed to look and feel like TradingView, Zerodha Kite, and Groww.

---

## 🏗️ Architecture

### Project Structure

```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx          # Login page
│   │   └── register/page.tsx       # Registration page
│   ├── (dashboard)/
│   │   ├── dashboard/page.tsx      # Main dashboard
│   │   ├── watchlist/page.tsx      # Watchlist management
│   │   ├── portfolio/page.tsx      # Portfolio & P&L
│   │   ├── charts/page.tsx         # Advanced charts
│   │   ├── alerts/page.tsx         # Alert management
│   │   └── news/page.tsx           # Market news
│   ├── layout.tsx                  # Root layout
│   ├── globals.css                 # Global styles
│   └── page.tsx                    # Home page
├── components/
│   ├── Navbar.tsx                  # Navigation bar
│   ├── Sidebar.tsx                 # Sidebar navigation
│   ├── SpecializedCards.tsx        # Trading cards
│   ├── ui/
│   │   ├── Button.tsx              # Enhanced buttons
│   │   ├── Card.tsx                # Card components
│   │   ├── Badge.tsx               # Status badges
│   │   ├── Input.tsx               # Form inputs
│   │   └── Modal.tsx               # Modals & alerts
│   ├── ProfileModal.tsx            # (existing)
│   ├── SearchBar.tsx               # (existing)
│   └── StockTickerRibbon.tsx       # (existing)
├── lib/
│   ├── stores.ts                   # Zustand stores
│   ├── api.ts                      # API integration
│   ├── hooks.ts                    # Custom React hooks
│   ├── api-client.ts               # (existing)
│   ├── auth.ts                     # (existing)
│   └── useInterval.ts              # (existing)
├── tailwind.config.ts              # Tailwind config
├── next.config.mjs                 # (existing)
├── tsconfig.json                   # (existing)
└── package.json                    # (existing)
```

---

## 📦 Tech Stack

- **Framework**: Next.js 14.2+ (App Router)
- **UI Framework**: React 18.3+
- **Styling**: Tailwind CSS 3.4+
- **State Management**: Zustand 4.5+
- **Charts**: Recharts 2.13+
- **HTTP Client**: Axios 1.7+
- **TypeScript**: 5.6+

---

## 🎨 Design System

### Color Palette

- **Background**: `#020617` (slate-950)
- **Card Background**: `#0f172a` (slate-900)
- **Border**: `#334155` (slate-700)
- **Text Primary**: `#f1f5f9` (slate-100)
- **Text Secondary**: `#cbd5e1` (slate-400)
- **Accent**: `#22c55e` (emerald-500)
- **Success**: `#10b981` (emerald-500)
- **Danger**: `#ef4444` (red-500)
- **Warning**: `#f59e0b` (amber-500)

### Components

#### Button Variants
```tsx
<Button variant="primary">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="danger">Delete</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
```

#### Cards
```tsx
<Card>Basic Card</Card>
<Card hover>Hoverable Card</Card>
<GradientCard gradient="emerald">Gradient Card</GradientCard>
```

#### Badge
```tsx
<Badge variant="success" size="sm">Success</Badge>
<StatusBadge status="active" />
```

---

## 🎯 Pages & Features

### Auth Pages
- **Login**: Email/password authentication with "Remember me"
- **Register**: Sign-up with password strength indicator

### Dashboard
- Welcome header with market snapshot
- Key metrics (Portfolio Value, Holdings, Watchlist, Alerts)
- Top Gainers/Losers
- Recent Alerts
- Quick Holdings preview

### Watchlist
- Add/remove stocks
- Grid and list views
- Live price updates
- Quick access to charts

### Portfolio
- Holdings management
- P&L calculations
- Allocation pie chart
- Add/edit holdings

### Charts
- Interactive price chart
- SMA, EMA, RSI indicators
- Timeframe selector (1D, 1W, 1M, 1Y)
- Toggleable indicators
- Tooltip on hover

### Alerts
- Create price alerts
- Filter by type (PRICE, SMA, EMA, RSI, COMBINED)
- Toggle active/inactive
- Delete alerts
- Status tracking

### News
- Market news feed
- Article cards with images
- Modal for full articles
- External link support

---

## 🔌 State Management (Zustand)

### Stores

```typescript
// Auth Store
useAuthStore - user, token, login, register, logout

// Watchlist Store
useWatchlistStore - stocks, addStock, removeStock, fetchWatchlist

// Alerts Store
useAlertsStore - alerts, createAlert, deleteAlert, toggleAlert

// Portfolio Store
usePortfolioStore - holdings, addHolding, fetchPortfolio

// UI Store
useUIStore - sidebarOpen, theme, toggleSidebar
```

---

## 🪝 Custom Hooks

```typescript
// Authentication
useAuth() - { user, token, isAuthenticated, login, register, logout }
useRequireAuth() - { isAuthenticated, isReady }

// Data Fetching
useWatchlist() - Fetch and manage watchlist
useAlerts() - Fetch and manage alerts
usePortfolio() - Fetch and manage portfolio

// Real-time
useRealtimePrice(symbol) - Live price updates
useWebSocket(symbol) - WebSocket connection
useInterval(callback, delay) - Interval execution
```

---

## 📡 API Integration

### Configuration

```typescript
// Base API client with auth interceptor
import apiClient from '@/lib/api';

// Automatic token injection
// 404 on 401 redirects to login
```

### API Endpoints

```typescript
// Stock API
stockApi.search(query)
stockApi.getPrice(symbol)
stockApi.getNews(symbol)

// Indicators API
indicatorsApi.sma(symbol, period)
indicatorsApi.ema(symbol, period)
indicatorsApi.rsi(symbol, period)
indicatorsApi.combined(symbol)

// Sentiment API
sentimentApi.get(symbol)
sentimentApi.getNews(symbol)

// Historical Data
historicalApi.get(symbol, days)
```

---

## 🎨 Styling Guidelines

### Tailwind Best Practices

1. **Dark theme first** - All components built for dark mode
2. **Responsive design** - Mobile-first approach
3. **Accessibility** - ARIA labels, semantic HTML
4. **Performance** - Smooth transitions (0.2s-0.3s)
5. **Consistency** - Reusable component variants

### Custom Animations

```css
/* Fade in animation */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Available utilities */
.animate-in
.animate-out
.animate-pulse
.animate-spin
```

### Glassmorphism

```tsx
<div className="backdrop-blur-xl bg-slate-900/80 border border-slate-700">
  {/* Glass effect */}
</div>
```

---

## 🚀 Performance Optimizations

1. **Code Splitting** - Automatic route-based splitting with App Router
2. **Image Optimization** - Next.js Image component
3. **Lazy Loading** - Dynamic imports for modals/heavy components
4. **Memoization** - React.memo for expensive components
5. **State Optimization** - Zustand for lightweight state
6. **CSS-in-JS** - Tailwind for minimal CSS output

---

## 🔐 Security

1. **Authentication** - JWT tokens stored in Zustand + localStorage
2. **API Security** - Authorization header injection
3. **XSS Protection** - React's built-in XSS protection
4. **CSRF** - Backend should implement CSRF tokens
5. **Password Security** - Strength indicator on registration

---

## 📱 Responsive Design

### Breakpoints
- **Mobile**: `< 640px`
- **Tablet**: `640px - 1024px`
- **Desktop**: `> 1024px`

### Key Features
- Collapsible sidebar on mobile
- Responsive grid layouts
- Touch-optimized buttons
- Mobile-first CSS

---

## 🔧 Development Workflow

### Installation

```bash
cd frontend
npm install
```

### Running Locally

```bash
npm run dev
# http://localhost:3000
```

### Building for Production

```bash
npm run build
npm run start
```

### ESLint & Formatting

```bash
npm run lint
```

---

## 📊 Component Examples

### Price Card

```tsx
<PriceCard
  symbol="AAPL"
  price={150.25}
  change={2.50}
  changePercent={1.70}
  onClick={() => navigate('/charts?symbol=AAPL')}
/>
```

### Stock Row

```tsx
<StockRow
  symbol="GOOGL"
  name="Alphabet Inc"
  price={140.30}
  change={-1.20}
  changePercent={-0.85}
  volume={45000000}
/>
```

### Alert Card

```tsx
<AlertCard
  symbol="MSFT"
  type="PRICE"
  target={380}
  condition=">"
  status="active"
  onToggle={handleToggle}
  onDelete={handleDelete}
/>
```

### Portfolio Holding Row

```tsx
<PortfolioHoldingRow
  symbol="TSLA"
  quantity={10}
  buyPrice={215.50}
  currentPrice={245.30}
  invested={2155}
  currentValue={2453}
  gainLoss={298}
  gainLossPercent={13.82}
/>
```

---

## 🎯 Key Features Implemented

✅ Responsive design (mobile, tablet, desktop)
✅ Dark theme with glassmorphism
✅ Real-time price updates
✅ Advanced technical indicators (SMA, EMA, RSI)
✅ Interactive charts with Recharts
✅ Alert system with multiple types
✅ Portfolio management with P&L
✅ Watchlist with live updates
✅ Market news feed
✅ Authentication (login/register)
✅ Password strength indicator
✅ State management with Zustand
✅ API integration with Axios
✅ Error handling
✅ Loading states
✅ Toast notifications
✅ Modal dialogs
✅ Form validation
✅ Smooth animations & transitions
✅ Professional trading platform UX

---

## 🐛 Troubleshooting

### Issue: Sidebar not showing on mobile
**Solution**: Check `useUIStore` is properly initialized and CSS media queries are working

### Issue: Charts not rendering
**Solution**: Ensure Recharts is installed and responsive container height is set

### Issue: API calls failing
**Solution**: Verify backend is running on `http://localhost:8000` and CORS is enabled

### Issue: State not persisting
**Solution**: Check localStorage isn't disabled and Zustand persist middleware is configured

---

## 📝 Future Enhancements

- [ ] Dark/Light theme toggle
- [ ] Advanced charting (TradingView LightCharts API)
- [ ] Real-time WebSocket updates
- [ ] Advanced filtering and search
- [ ] User preferences/settings
- [ ] Export reports (PDF/CSV)
- [ ] Mobile app (React Native)
- [ ] Social features (share strategies)
- [ ] Backtesting simulator
- [ ] AI-powered sentiment analysis

---

## 📄 License

Stock Sentinel © 2024. All rights reserved.

---

## 🤝 Support

For issues or questions, please open an issue on GitHub or contact the development team.

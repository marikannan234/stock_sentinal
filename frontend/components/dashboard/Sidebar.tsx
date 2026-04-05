'use client';

import Link from 'next/link';
import { useAuthStore } from '@/lib/auth';
import { useRouter } from 'next/navigation';

interface NavItem {
  label: string;
  icon: string;
  href: string;
  active?: boolean;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', icon: 'dashboard', href: '/dashboard' },
  { label: 'Watchlist', icon: 'list_alt', href: '/watchlist' },
  { label: 'Portfolio', icon: 'pie_chart', href: '/portfolio' },
  { label: 'Trade History', icon: 'receipt_long', href: '/trade-history' },
  { label: 'Alerts', icon: 'notifications_active', href: '/alerts' },
  { label: 'News', icon: 'article', href: '/news' },
];

const bottomNavItems: NavItem[] = [
  { label: 'Profile', icon: 'person', href: '/profile' },
  { label: 'Settings', icon: 'settings', href: '/settings' },
  { label: 'Support', icon: 'help_outline', href: '/support' },
];

export function Sidebar({ currentPage = 'dashboard' }: { currentPage?: string }) {
  const { logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <aside
      className="h-screen w-16 hover:w-64 transition-all duration-300 fixed left-0 top-0 z-[55] bg-[#1c1b1d] group flex flex-col pt-28 pb-8 overflow-hidden"
    >
      <div className="flex flex-col flex-1 gap-2">
        {navItems.map((item) => {
          const isActive = currentPage === item.label.toLowerCase();
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center h-12 px-5 gap-4 transition-all duration-300 ${
                isActive
                  ? 'text-white font-bold bg-[#39393b] border-r-2 border-[#adc6ff]'
                  : 'text-[#c2c6d6] hover:bg-[#2a2a2c] hover:text-white hover:translate-x-1'
              }`}
            >
              <span className="material-symbols-outlined shrink-0">
                {item.icon}
              </span>
              <span className="text-sm font-['Inter'] opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>

      <div className="px-3 group-hover:block hidden mb-6">
        <Link
          href="/dashboard?quickTrade=1"
          className="block w-full rounded-xl bg-gradient-to-br from-[#adc6ff] to-[#4d8eff] py-3 text-center text-sm font-bold text-[#001a42] shadow-lg shadow-[#adc6ff]/20 transition-transform active:scale-95"
        >
          Quick Trade
        </Link>
      </div>

      <div className="flex flex-col gap-2 mt-auto">
        {bottomNavItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center h-12 px-5 gap-4 transition-all duration-300 ${
              currentPage === item.label.toLowerCase()
                ? 'text-white font-bold bg-[#39393b] border-r-2 border-[#adc6ff]'
                : 'text-[#c2c6d6] hover:bg-[#2a2a2c]'
            }`}
          >
            <span className="material-symbols-outlined shrink-0">
              {item.icon}
            </span>
            <span className="text-sm font-['Inter'] opacity-0 group-hover:opacity-100 transition-opacity">
              {item.label}
            </span>
          </Link>
        ))}
        <button
          onClick={handleLogout}
          className="flex items-center h-12 px-5 gap-4 text-[#c2c6d6] hover:bg-red-500/10 hover:text-red-400 transition-all duration-300"
        >
          <span className="material-symbols-outlined shrink-0">logout</span>
          <span className="text-sm font-['Inter'] opacity-0 group-hover:opacity-100 transition-opacity">
            Logout
          </span>
        </button>
      </div>
    </aside>
  );
}

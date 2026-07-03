import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, Sun, Moon, LogOut, UserCircle, ChevronDown } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { useThemeStore } from '../store/themeStore';

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const { resolvedTheme, setTheme } = useThemeStore();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const initials = user?.full_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2) ?? '?';

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card px-6 flex-shrink-0">
      <div />

      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <button
          onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
          className="rounded-lg p-2 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
          aria-label="Toggle theme"
        >
          {resolvedTheme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>

        {/* Notifications */}
        <button className="relative rounded-lg p-2 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-destructive" />
        </button>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-accent transition-colors"
          >
            {user?.avatar_url ? (
              <img
                src={user.avatar_url}
                alt={user.full_name}
                className="h-7 w-7 rounded-full object-cover"
              />
            ) : (
              <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-xs font-semibold text-primary">{initials}</span>
              </div>
            )}
            <span className="hidden sm:block text-sm font-medium text-foreground max-w-[120px] truncate">
              {user?.full_name}
            </span>
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
          </button>

          {menuOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setMenuOpen(false)}
              />
              <div className="absolute right-0 top-full mt-1 z-20 w-52 rounded-xl border border-border bg-card shadow-dialog py-1 animate-slide-up">
                <div className="px-3 py-2 border-b border-border">
                  <p className="text-xs font-medium text-foreground truncate">{user?.full_name}</p>
                  <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                </div>
                <Link
                  to="/profile"
                  onClick={() => setMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-accent transition-colors"
                >
                  <UserCircle className="h-4 w-4 text-muted-foreground" />
                  Profile
                </Link>
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-destructive hover:bg-destructive/10 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

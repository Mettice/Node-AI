/**
 * User Profile Dropdown - Top-right user menu with profile and logout
 */

import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { User, LogOut, Settings, ChevronDown } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useUIStore } from '@/store/uiStore';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/utils/cn';

export function UserProfileDropdown() {
  const { user, signOut } = useAuth();
  const { setActiveUtility } = useUIStore();
  const navigate = useNavigate();
  const [showMenu, setShowMenu] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ top: 0, right: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Calculate dropdown position when it opens
  const handleMenuToggle = () => {
    if (!showMenu && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setMenuPosition({
        top: rect.bottom + 4,
        right: window.innerWidth - rect.right,
      });
    }
    setShowMenu(!showMenu);
  };

  // Close menu when clicking outside
  useEffect(() => {
    if (!showMenu) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (buttonRef.current && !buttonRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showMenu]);

  const handleLogout = async () => {
    await signOut();
    navigate('/login');
    setShowMenu(false);
  };

  const handleOpenSettings = () => {
    setActiveUtility('settings');
    setShowMenu(false);
  };

  // Get user display name or email
  const displayName = user?.user_metadata?.name || user?.email?.split('@')[0] || 'User';
  const userEmail = user?.email || '';

  if (!user) return null;

  return (
    <>
      <button
        ref={buttonRef}
        onClick={handleMenuToggle}
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-lg',
          'text-sm font-medium text-slate-300 hover:text-white',
          'hover:bg-white/5 transition-colors',
          showMenu && 'bg-white/5'
        )}
      >
        <div className="w-7 h-7 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center">
          <User className="w-4 h-4 text-purple-400" />
        </div>
        <span className="hidden sm:block max-w-[120px] truncate">{displayName}</span>
        <ChevronDown className={cn('w-4 h-4 transition-transform', showMenu && 'rotate-180')} />
      </button>

      {showMenu && createPortal(
        <>
          <div
            className="fixed inset-0 z-[9999]"
            onClick={() => setShowMenu(false)}
            style={{ pointerEvents: 'auto' }}
          />
          <div
            className="fixed bg-slate-800 border border-white/10 rounded-md shadow-xl z-[10000] py-1 min-w-[200px]"
            style={{
              top: `${menuPosition.top}px`,
              right: `${menuPosition.right}px`,
              pointerEvents: 'auto',
            }}
          >
            {/* User Info */}
            <div className="px-3 py-2 border-b border-white/10">
              <div className="text-sm font-medium text-white truncate">{displayName}</div>
              <div className="text-xs text-slate-400 truncate">{userEmail}</div>
            </div>

            {/* Menu Items */}
            <button
              onClick={handleOpenSettings}
              className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5 transition-colors"
            >
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </button>

            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm text-red-400 hover:bg-red-500/10 transition-colors border-t border-white/10"
            >
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </button>
          </div>
        </>,
        document.body
      )}
    </>
  );
}


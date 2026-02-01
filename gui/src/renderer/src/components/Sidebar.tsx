/**
 * Sidebar Navigation Component
 * 
 * Provides stacked menu navigation for the application.
 * Shows main pages and settings subsections.
 */

import { useLocation, Link } from 'react-router-dom'
import { useAppStore } from '../store'

// Define navigation items with icons
const navItems = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    path: '/',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    )
  },
  {
    id: 'batch',
    label: 'Batch Transcription',
    path: '/batch',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    )
  },
  {
    id: 'stats',
    label: 'Statistics',
    path: '/stats',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    )
  }
]

// Settings subsections
const settingsItems = [
  {
    id: 'model',
    label: 'Model',
    path: '/settings/model',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    )
  },
  {
    id: 'audio',
    label: 'Audio',
    path: '/settings/audio',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    )
  },
  {
    id: 'hotkey',
    label: 'Hotkey',
    path: '/settings/hotkey',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
      </svg>
    )
  },
  {
    id: 'behavior',
    label: 'Behavior',
    path: '/settings/behavior',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    )
  },
  {
    id: 'appearance',
    label: 'Appearance',
    path: '/settings/appearance',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
      </svg>
    )
  },
  {
    id: 'data',
    label: 'Data',
    path: '/settings/data',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
      </svg>
    )
  },
  {
    id: 'about',
    label: 'About',
    path: '/settings/about',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    )
  }
]

interface NavItemProps {
  item: typeof navItems[0]
  isActive: boolean
}

function NavItem({ item, isActive }: NavItemProps): JSX.Element {
  return (
    <Link
      to={item.path}
      className={`
        flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
        transition-all duration-150 ease-out
        ${isActive 
          ? 'bg-[var(--color-sidebar-active)] text-[var(--color-text-primary)]' 
          : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-sidebar-hover)] hover:text-[var(--color-text-primary)]'
        }
      `}
    >
      <span className={isActive ? 'text-[var(--color-accent)]' : ''}>{item.icon}</span>
      <span>{item.label}</span>
    </Link>
  )
}

export default function Sidebar(): JSX.Element {
  const location = useLocation()
  const { backendConnected, isReconnecting } = useAppStore()
  
  const isSettingsPage = location.pathname.startsWith('/settings')
  
  return (
    <aside className="w-56 bg-[var(--color-sidebar-bg)] border-r border-[var(--color-sidebar-border)] flex flex-col h-full">
      {/* Logo / App Title */}
      <div className="px-4 py-4 border-b border-[var(--color-sidebar-border)]">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-[var(--color-accent)] flex items-center justify-center">
            <svg className="w-5 h-5 text-[var(--color-text-on-accent)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </div>
          <span className="font-semibold text-[var(--color-text-primary)]">SpeakEasy</span>
        </div>
      </div>
      
      {/* Main Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(item => (
          <NavItem 
            key={item.id} 
            item={item} 
            isActive={location.pathname === item.path} 
          />
        ))}
        
        {/* Settings Section */}
        <div className="pt-4 mt-4 border-t border-[var(--color-sidebar-border)]">
          <div className="px-3 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-[var(--color-text-muted)]">
              Settings
            </span>
          </div>
          <div className="space-y-1">
            {settingsItems.map(item => (
              <NavItem 
                key={item.id} 
                item={item} 
                isActive={location.pathname === item.path || (location.pathname === '/settings' && item.id === 'model')} 
              />
            ))}
          </div>
        </div>
      </nav>
      
      {/* Connection Status Footer */}
      <div className="px-4 py-3 border-t border-[var(--color-sidebar-border)]">
        <div className="flex items-center gap-2">
          <div 
            className={`rounded-full transition-all duration-300 ${
              backendConnected 
                ? 'w-2 h-2 bg-[var(--color-success)]' 
                : isReconnecting
                  ? 'w-2.5 h-2.5 bg-[var(--color-warning)] animate-pulse'
                  : 'w-2.5 h-2.5 bg-[var(--color-error)]'
            }`} 
          />
          <span className="text-xs text-[var(--color-text-muted)]">
            {backendConnected 
              ? 'Connected' 
              : isReconnecting 
                ? 'Reconnecting...' 
                : 'Disconnected'
            }
          </span>
        </div>
      </div>
    </aside>
  )
}

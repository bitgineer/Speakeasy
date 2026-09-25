/**
 * Sidebar Navigation Component
 *
 * Compact rows grouped under an uppercase Settings label, with the current
 * destination marked by aria-current and a connection status footer.
 */

import { Fragment } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Mic } from 'lucide-react'
import { NAV_GROUPS, type NavItem } from '../utils/navigation'
import { useAppStore } from '../store'

function isCurrentRoute(pathname: string, item: NavItem): boolean {
  return (
    pathname === item.path ||
    (pathname === '/settings' && item.id === 'model')
  )
}

function NavLink({ item, current }: { item: NavItem; current: boolean }): JSX.Element {
  const Glyph = item.icon
  return (
    <Link to={item.path} className="nav-link" aria-current={current ? 'page' : undefined}>
      <Glyph className="nav-glyph" size={15} strokeWidth={1.75} aria-hidden="true" />
      <span>{item.label}</span>
    </Link>
  )
}

export default function Sidebar(): JSX.Element {
  const { pathname } = useLocation()
  const { backendConnected, isReconnecting } = useAppStore()

  const connection = backendConnected
    ? { tone: 'success', label: 'Backend connected' }
    : isReconnecting
      ? { tone: 'warning', label: 'Reconnecting...' }
      : { tone: 'danger', label: 'Backend unreachable' }

  return (
    <aside className="sidebar" aria-label="Application navigation">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          <Mic size={15} strokeWidth={2.25} />
        </span>
        SpeakEasy
      </div>
      <nav className="nav" aria-label="Main navigation">
        {NAV_GROUPS.map((group) => (
          <Fragment key={group.id}>
            {group.label && <div className="nav-group">{group.label}</div>}
            {group.items.map((item) => (
              <NavLink key={item.id} item={item} current={isCurrentRoute(pathname, item)} />
            ))}
          </Fragment>
        ))}
      </nav>
      <div className="connection" role="status">
        <span className="status-dot" data-tone={connection.tone} aria-hidden="true" />
        {connection.label}
      </div>
    </aside>
  )
}

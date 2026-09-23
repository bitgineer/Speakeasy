import {
  BarChart3,
  Cpu,
  Database,
  Info,
  Keyboard,
  LayoutDashboard,
  Layers,
  Mic,
  Palette,
  Settings2,
  SlidersHorizontal,
  type LucideIcon
} from 'lucide-react'

export interface NavItem {
  id: string
  label: string
  path: string
  icon: LucideIcon
}

export interface NavGroup {
  id: 'workspace' | 'settings'
  label: string | null
  items: NavItem[]
}

export const NAV_GROUPS: NavGroup[] = [
  {
    id: 'workspace',
    label: null,
    items: [
      { id: 'dashboard', label: 'Dashboard', path: '/', icon: LayoutDashboard },
      { id: 'batch', label: 'Batch transcription', path: '/batch', icon: Layers },
      { id: 'stats', label: 'Statistics', path: '/stats', icon: BarChart3 }
    ]
  },
  {
    id: 'settings',
    label: 'Settings',
    items: [
      { id: 'model', label: 'Model', path: '/settings/model', icon: Cpu },
      { id: 'audio', label: 'Audio', path: '/settings/audio', icon: Mic },
      { id: 'hotkey', label: 'Hotkey', path: '/settings/hotkey', icon: Keyboard },
      { id: 'processing', label: 'Processing', path: '/settings/processing', icon: SlidersHorizontal },
      { id: 'behavior', label: 'Behavior', path: '/settings/behavior', icon: Settings2 },
      { id: 'appearance', label: 'Appearance', path: '/settings/appearance', icon: Palette },
      { id: 'data', label: 'Data', path: '/settings/data', icon: Database },
      { id: 'about', label: 'About', path: '/settings/about', icon: Info }
    ]
  }
]

const GROUP_TITLES: Record<NavGroup['id'], string> = {
  workspace: 'Workspace',
  settings: 'Settings'
}

export interface RouteLocation {
  group: string
  title: string
}

export function resolveRoute(pathname: string): RouteLocation {
  for (const group of NAV_GROUPS) {
    const item = group.items.find((candidate) => candidate.path === pathname)
    if (item) {
      return { group: GROUP_TITLES[group.id], title: item.label }
    }
  }
  if (pathname.startsWith('/settings')) {
    return { group: GROUP_TITLES.settings, title: 'Model' }
  }
  return { group: GROUP_TITLES.workspace, title: 'Dashboard' }
}

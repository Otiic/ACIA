import { Upload, FolderOpen, Search, Clock, MessageSquare, Settings } from 'lucide-react'
import './Sidebar.css'

const navItems = [
  { id: 'upload', label: 'Subir contrato', icon: Upload, enabled: true },
  { id: 'contracts', label: 'Mis contratos', icon: FolderOpen, enabled: true },
  { id: 'history', label: 'Historial', icon: Clock, enabled: true },
  { id: 'search', label: 'Búsqueda semántica', icon: Search, enabled: false },
  { id: 'chat', label: 'Consultar a la IA', icon: MessageSquare, enabled: false },
]

export default function Sidebar({ activeView, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <div className="sidebar__mark">A</div>
        <div className="sidebar__brand-text">
          <span className="sidebar__brand-name">ACIA</span>
          <span className="sidebar__brand-sub">Análisis de Contratos</span>
        </div>
      </div>

      <nav className="sidebar__nav">
        <div className="sidebar__section-label">Estudio</div>
        <ul>
          {navItems.map((item) => {
            const Icon = item.icon
            const active = activeView === item.id
            return (
              <li key={item.id}>
                <button
                  className={`sidebar__item ${active ? 'is-active' : ''} ${!item.enabled ? 'is-disabled' : ''}`}
                  onClick={() => item.enabled && onNavigate(item.id)}
                  disabled={!item.enabled}
                >
                  <Icon size={16} strokeWidth={1.5} />
                  <span>{item.label}</span>
                  {!item.enabled && <span className="sidebar__soon">pronto</span>}
                </button>
              </li>
            )
          })}
        </ul>
      </nav>

      <div className="sidebar__footer">
        <button className="sidebar__item sidebar__item--ghost" disabled>
          <Settings size={16} strokeWidth={1.5} />
          <span>Ajustes</span>
        </button>
        <p className="sidebar__version">v0.2</p>
      </div>
    </aside>
  )
}

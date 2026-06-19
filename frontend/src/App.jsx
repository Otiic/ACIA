import { useState } from 'react'
import Sidebar from './components/Sidebar'
import UploadView from './components/UploadView'
import SavedView from './components/SavedView'
import './App.css'

function App() {
  const [view, setView] = useState('upload')

  return (
    <div className="app-shell">
      <Sidebar activeView={view} onNavigate={setView} />
      <main className="app-main">
        {view === 'upload' && <UploadView />}
        {view === 'contracts' && <SavedView key="contracts" mode="contracts" />}
        {view === 'history' && <SavedView key="history" mode="history" />}
      </main>
    </div>
  )
}

export default App

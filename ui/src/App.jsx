import React, {useState} from 'react'
import Chat from './components/Chat'
import Admin from './components/Admin'
import SourceBrowser from './components/SourceBrowser'

export default function App(){
  const [view, setView] = useState('chat')
  return (
    <div className="h-screen flex">
      <aside className="w-60 bg-gray-800 p-4">
        <h1 className="text-xl font-bold mb-4">PIVOT</h1>
        <nav className="flex flex-col gap-2">
          <button onClick={()=>setView('chat')} className="p-2 rounded bg-gray-700">Chat</button>
          <button onClick={()=>setView('sources')} className="p-2 rounded bg-gray-700">Sources</button>
          <button onClick={()=>setView('admin')} className="p-2 rounded bg-gray-700">Admin</button>
        </nav>
      </aside>
      <main className="flex-1 bg-gray-900 p-6">
        {view==='chat' && <Chat />}
        {view==='sources' && <SourceBrowser />}
        {view==='admin' && <Admin />}
      </main>
    </div>
  )
}


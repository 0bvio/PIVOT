import React, {useState, useEffect, useRef} from 'react'

export default function Chat(){
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [q, setQ] = useState('')
  const listRef = useRef(null)

  useEffect(()=>{
    // start a session
    fetch('/api/session/start', {method:'POST'})
      .then(r=>r.json())
      .then(j=> setSessionId(j.session_id))
  },[])

  function send(){
    if(!q) return
    const userMsg = {role:'user', content:q}
    setMessages(prev=>[...prev, userMsg])
    setQ('')
    // call backend /query
    fetch('/api/query', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({project:'default', query:q, top_k:5})
    }).then(r=>r.json()).then(j=>{
      setMessages(prev=>[...prev, {role:'assistant', content: j.answer || 'no answer', metadata: {results: j.results}}])
      // auto-append sources or do further handling
    })
  }

  useEffect(()=>{
    if(listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight
  },[messages])

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-auto p-4" ref={listRef}>
        {messages.map((m,i)=> (
          <div key={i} className={`mb-3 ${m.role==='user'?'text-right':''}`}>
            <div className={`inline-block px-3 py-2 rounded ${m.role==='user'? 'bg-indigo-600':'bg-gray-700'}`}>
              {m.content}
            </div>
            {m.metadata && m.metadata.results && (
              <div className="mt-2 text-xs text-gray-400">Sources: {m.metadata.results.length}</div>
            )}
          </div>
        ))}
      </div>
      <div className="p-4 bg-gray-800 flex gap-2">
        <input value={q} onChange={e=>setQ(e.target.value)} className="flex-1 p-2 rounded bg-gray-700" />
        <button onClick={send} className="px-4 py-2 rounded bg-indigo-600">Send</button>
      </div>
    </div>
  )
}


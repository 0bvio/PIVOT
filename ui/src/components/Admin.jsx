import React, {useState} from 'react'

export default function Admin(){
  const [files, setFiles] = useState(null)

  function onFile(e){
    const f = e.target.files[0]
    if(!f) return
    const fd = new FormData()
    fd.append('file', f)
    fd.append('project','default')
    fetch('/api/upload', {method:'POST', body: fd}).then(r=>r.json()).then(j=> alert('upload: '+JSON.stringify(j)))
  }

  return (
    <div>
      <h2 className="text-lg font-bold mb-2">Admin</h2>
      <div className="bg-gray-800 p-4 rounded space-y-4">
        <div>
          <label className="block text-sm text-gray-300">Upload file to ingest</label>
          <input type="file" onChange={onFile} className="mt-2" />
        </div>
        <div>
          <button className="px-3 py-2 rounded bg-red-600">Clear Index (TODO)</button>
        </div>
      </div>
    </div>
  )
}


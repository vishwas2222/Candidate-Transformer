import { useRef, useState } from 'react';

// ── File type validation ───────────────────────────────────────────────────────
function getFileExt(filename) {
  return filename.slice(filename.lastIndexOf('.')).toLowerCase();
}
function validateFile(file, accept) {
  const allowed = accept.split(',').map(s => s.trim().toLowerCase());
  return allowed.includes(getFileExt(file.name));
}

// ── Icons ─────────────────────────────────────────────────────────────────────
const PdfIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);
const CsvIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
      d="M3 10h18M3 14h18M10 3v18M14 3v18M5 3h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2z" />
  </svg>
);
const TrashIcon = () => (
  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
);

// ── Multi-file Resume Drop Zone ───────────────────────────────────────────────
function MultiResumeZone({ files, onChange }) {
  const inputRef  = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [typeErr,  setTypeErr]  = useState('');

  const addFiles = (incoming) => {
    if (!incoming || incoming.length === 0) return;
    const valid   = [];
    const invalid = [];
    Array.from(incoming).forEach(f => {
      if (validateFile(f, '.pdf')) valid.push(f);
      else invalid.push(f.name);
    });
    if (invalid.length) {
      setTypeErr(`Not a PDF: ${invalid.join(', ')}. Only .pdf files accepted.`);
    } else {
      setTypeErr('');
    }
    if (valid.length) {
      // Deduplicate by name
      const existing = new Set(files.map(f => f.name));
      const newFiles = valid.filter(f => !existing.has(f.name));
      onChange([...files, ...newFiles]);
    }
  };

  const removeFile = (idx) => {
    const updated = files.filter((_, i) => i !== idx);
    onChange(updated);
    setTypeErr('');
  };

  const zoneClass = [
    'upload-zone',
    files.length > 0 ? 'has-file' : '',
    dragging          ? 'drag-over' : '',
    typeErr           ? 'border-red-400 bg-red-50' : '',
  ].filter(Boolean).join(' ');

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="label">Resume PDFs</span>
        {files.length > 0 && (
          <span className="text-xs text-brand-600 font-semibold">
            {files.length} file{files.length > 1 ? 's' : ''} selected
          </span>
        )}
      </div>

      {/* Drop zone */}
      <div
        className={zoneClass}
        onClick={() => { setTypeErr(''); inputRef.current?.click(); }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={(e) => { addFiles(e.target.files); e.target.value = ''; }}
        />

        {typeErr ? (
          <>
            <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="text-center">
              <p className="text-sm font-semibold text-red-700">Wrong file type</p>
              <p className="text-xs text-red-600 mt-0.5 max-w-xs">{typeErr}</p>
              <button type="button" onClick={(e) => { e.stopPropagation(); setTypeErr(''); }}
                className="mt-2 text-xs font-medium text-red-500 hover:text-red-700 underline">
                Dismiss
              </button>
            </div>
          </>
        ) : files.length === 0 ? (
          <>
            <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
              <PdfIcon />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-600">
                Drop PDF files here or <span className="text-brand-600">browse</span>
              </p>
              <p className="text-xs text-slate-400 mt-0.5">
                Select <span className="font-semibold">multiple PDFs</span> for batch processing
              </p>
            </div>
          </>
        ) : (
          <>
            <div className="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center text-brand-600 shrink-0">
              <PdfIcon />
            </div>
            <div>
              <p className="text-sm font-semibold text-brand-700">
                {files.length} resume{files.length > 1 ? 's' : ''} ready
              </p>
              <p className="text-xs text-slate-500 mt-0.5">Click to add more files</p>
            </div>
          </>
        )}
      </div>

      {/* File list */}
      {files.length > 0 && (
        <ul className="mt-2 space-y-1.5">
          {files.map((f, idx) => (
            <li key={idx}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 text-sm">
              <div className="text-brand-500 shrink-0"><PdfIcon /></div>
              <span className="flex-1 truncate text-slate-700 font-medium">{f.name}</span>
              <span className="text-xs text-slate-400 shrink-0">{(f.size / 1024).toFixed(0)} KB</span>
              <button
                type="button"
                onClick={() => removeFile(idx)}
                className="text-red-400 hover:text-red-600 transition-colors shrink-0"
                title="Remove"
              >
                <TrashIcon />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ── Single-file CSV Drop Zone (unchanged) ─────────────────────────────────────
function CsvDropZone({ file, onChange }) {
  const inputRef  = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [typeErr,  setTypeErr]  = useState('');

  const handleFile = (incoming) => {
    if (!incoming) { onChange(null); setTypeErr(''); return; }
    if (!validateFile(incoming, '.csv')) {
      setTypeErr(`"${incoming.name}" is not a CSV file.`);
      return;
    }
    setTypeErr('');
    onChange(incoming);
  };

  const zoneClass = [
    'upload-zone',
    file    ? 'has-file'  : '',
    dragging ? 'drag-over' : '',
    typeErr  ? 'border-red-400 bg-red-50' : '',
  ].filter(Boolean).join(' ');

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="label">Recruiter CSV</span>
        <span className="text-xs text-slate-400 font-medium">Optional</span>
      </div>

      <div
        className={zoneClass}
        onClick={() => { setTypeErr(''); inputRef.current?.click(); }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0] ?? null); }}
      >
        <input ref={inputRef} type="file" accept=".csv" className="hidden"
          onChange={(e) => handleFile(e.target.files[0] ?? null)}
          onClick={(e) => { e.target.value = ''; }} />

        {typeErr ? (
          <>
            <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="text-center">
              <p className="text-sm font-semibold text-red-700">Wrong file type</p>
              <p className="text-xs text-red-600 mt-0.5">{typeErr}</p>
              <button type="button" onClick={(e) => { e.stopPropagation(); setTypeErr(''); }}
                className="mt-2 text-xs font-medium text-red-500 hover:text-red-700 underline">Try again</button>
            </div>
          </>
        ) : file ? (
          <>
            <div className="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center"><CsvIcon /></div>
            <div>
              <p className="text-sm font-semibold text-brand-700 truncate max-w-xs">{file.name}</p>
              <p className="text-xs text-slate-500 mt-0.5">{(file.size / 1024).toFixed(1)} KB · Click to replace</p>
            </div>
            <button type="button" onClick={(e) => { e.stopPropagation(); handleFile(null); }}
              className="text-xs text-red-500 hover:text-red-700 font-medium mt-1">Remove</button>
          </>
        ) : (
          <>
            <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-400"><CsvIcon /></div>
            <div>
              <p className="text-sm font-medium text-slate-600">Drop file here or <span className="text-brand-600">browse</span></p>
              <p className="text-xs text-slate-400 mt-0.5">Accepted: <span className="font-semibold">CSV</span></p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Public component ──────────────────────────────────────────────────────────
export default function UploadCard({ resumeFiles, csvFile, onResumeChange, onCsvChange }) {
  return (
    <div className="card">
      <div className="card-header">
        <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        <h2 className="section-title">Upload Files</h2>
        {resumeFiles.length > 1 && (
          <span className="ml-auto text-xs font-semibold text-brand-700 bg-brand-50
                           border border-brand-200 rounded-full px-2.5 py-1">
            Batch Mode · {resumeFiles.length} resumes
          </span>
        )}
      </div>

      <div className="card-body grid grid-cols-1 md:grid-cols-2 gap-5">
        <MultiResumeZone files={resumeFiles} onChange={onResumeChange} />
        <CsvDropZone     file={csvFile}      onChange={onCsvChange} />
      </div>
    </div>
  );
}

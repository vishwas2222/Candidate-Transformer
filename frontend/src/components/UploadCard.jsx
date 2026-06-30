import { useRef, useState } from 'react';

// ── File type validation ───────────────────────────────────────────────────────
function getFileExt(filename) {
  return filename.slice(filename.lastIndexOf('.')).toLowerCase();
}

function validateFile(file, accept) {
  const allowed = accept.split(',').map(s => s.trim().toLowerCase());
  const ext = getFileExt(file.name);
  return allowed.includes(ext);
}

// ── Drop zone component ────────────────────────────────────────────────────────
function FileDropZone({ label, accept, acceptLabel, icon, file, onChange, optional = false }) {
  const inputRef = useRef(null);
  const [dragging, setDragging]   = useState(false);
  const [typeError, setTypeError] = useState('');

  const handleFile = (incoming) => {
    if (!incoming) { onChange(null); setTypeError(''); return; }
    if (!validateFile(incoming, accept)) {
      setTypeError(
        `"${incoming.name}" is not a valid ${acceptLabel} file. ` +
        `Please upload a ${accept.toUpperCase().replace(/\./g, '')} file.`
      );
      return;
    }
    setTypeError('');
    onChange(incoming);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0] ?? null);
  };

  const zoneClass = [
    'upload-zone',
    file     ? 'has-file'   : '',
    dragging ? 'drag-over'  : '',
    typeError ? 'border-red-400 bg-red-50' : '',
  ].filter(Boolean).join(' ');

  return (
    <div>
      {/* Label row */}
      <div className="flex items-center justify-between mb-1.5">
        <span className="label">{label}</span>
        {optional && (
          <span className="text-xs text-slate-400 font-medium">Optional</span>
        )}
      </div>

      {/* Drop zone */}
      <div
        className={zoneClass}
        onClick={() => { setTypeError(''); inputRef.current?.click(); }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          className="hidden"
          onChange={(e) => handleFile(e.target.files[0] ?? null)}
          /* reset value so re-uploading the same filename fires onChange */
          onClick={(e) => { e.target.value = ''; }}
        />

        {/* Error state */}
        {typeError ? (
          <>
            <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="text-center">
              <p className="text-sm font-semibold text-red-700">Wrong file type</p>
              <p className="text-xs text-red-600 mt-0.5 max-w-xs">{typeError}</p>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); setTypeError(''); }}
                className="mt-2 text-xs font-medium text-red-500 hover:text-red-700 underline"
              >
                Try again
              </button>
            </div>
          </>
        ) : file ? (
          /* File selected state */
          <>
            <div className="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center">
              {icon}
            </div>
            <div>
              <p className="text-sm font-semibold text-brand-700 truncate max-w-xs">
                {file.name}
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                {(file.size / 1024).toFixed(1)} KB · Click to replace
              </p>
            </div>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); handleFile(null); }}
              className="text-xs text-red-500 hover:text-red-700 font-medium mt-1"
            >
              Remove
            </button>
          </>
        ) : (
          /* Empty state */
          <>
            <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
              {icon}
            </div>
            <div>
              <p className="text-sm font-medium text-slate-600">
                Drop file here or <span className="text-brand-600">browse</span>
              </p>
              <p className="text-xs text-slate-400 mt-0.5">
                Accepted: <span className="font-semibold">{accept.toUpperCase().replace(/\./g, '')}</span>
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Icons ──────────────────────────────────────────────────────────────────────
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

// ── Public component ───────────────────────────────────────────────────────────
export default function UploadCard({ resumeFile, csvFile, onResumeChange, onCsvChange }) {
  return (
    <div className="card">
      <div className="card-header">
        <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        <h2 className="section-title">Upload Files</h2>
      </div>

      <div className="card-body grid grid-cols-1 md:grid-cols-2 gap-5">
        <FileDropZone
          label="Resume PDF"
          accept=".pdf"
          acceptLabel="PDF"
          icon={<PdfIcon />}
          file={resumeFile}
          onChange={onResumeChange}
        />
        <FileDropZone
          label="Recruiter CSV"
          accept=".csv"
          acceptLabel="CSV"
          icon={<CsvIcon />}
          file={csvFile}
          onChange={onCsvChange}
          optional
        />
      </div>
    </div>
  );
}

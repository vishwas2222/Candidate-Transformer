function downloadJson(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url  = URL.createObjectURL(blob);
  const a    = Object.assign(document.createElement('a'), { href: url, download: filename });
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function DownloadBtn({ onClick, icon, label, sublabel, id }) {
  return (
    <button
      type="button"
      id={id}
      onClick={onClick}
      className="flex items-center gap-3 px-4 py-3 rounded-lg border border-slate-200
                 hover:border-brand-400 hover:bg-brand-50 transition-colors duration-150
                 text-left w-full"
    >
      <div className="w-9 h-9 rounded-lg bg-brand-100 flex items-center justify-center shrink-0 text-brand-600">
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-sm font-semibold text-slate-800">{label}</p>
        <p className="text-xs text-slate-500 truncate">{sublabel}</p>
      </div>
      <svg className="w-4 h-4 text-slate-400 ml-auto shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
    </button>
  );
}

const JsonIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const ReportIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
  </svg>
);

export default function DownloadButtons({ candidate, validationReport }) {
  if (!candidate && !validationReport) return null;

  return (
    <div className="card">
      <div className="card-header">
        <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        <h2 className="section-title">Downloads</h2>
      </div>

      <div className="card-body grid grid-cols-1 sm:grid-cols-2 gap-3">
        {candidate && (
          <DownloadBtn
            id="download-candidate-json"
            icon={<JsonIcon />}
            label="candidate.json"
            sublabel="Full candidate document"
            onClick={() => downloadJson(candidate, 'candidate.json')}
          />
        )}
        {validationReport && (
          <DownloadBtn
            id="download-validation-report"
            icon={<ReportIcon />}
            label="validation_report.json"
            sublabel="Schema validation results"
            onClick={() => downloadJson(validationReport, 'validation_report.json')}
          />
        )}
      </div>

      {/* Validation summary */}
      {validationReport && (
        <div className="px-6 pb-5">
          <div className={[
            'rounded-lg px-4 py-3 flex items-center gap-3 text-sm',
            validationReport.is_valid
              ? 'bg-emerald-50 border border-emerald-200'
              : 'bg-red-50 border border-red-200',
          ].join(' ')}>
            {validationReport.is_valid ? (
              <>
                <svg className="w-4 h-4 text-emerald-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-emerald-800 font-medium">Schema validation passed</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4 text-red-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                <span className="text-red-800 font-medium">
                  {validationReport.errors?.length ?? 0} validation error(s) — download report for details
                </span>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

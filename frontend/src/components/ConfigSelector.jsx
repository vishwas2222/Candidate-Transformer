const CONFIGS = [
  {
    id: 'default',
    label: 'Default',
    description: 'Balanced output with all fields',
  },
  {
    id: 'minimal',
    label: 'Minimal',
    description: 'Name, email, and skills only',
  },
  {
    id: 'recruiter',
    label: 'Recruiter',
    description: 'ATS-optimised view with confidence',
  },
  {
    id: 'analytics',
    label: 'Analytics',
    description: 'Full provenance and source data',
  },
];

export default function ConfigSelector({ value, onChange }) {
  return (
    <div className="card">
      <div className="card-header">
        <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <h2 className="section-title">Output Profile</h2>
      </div>

      <div className="card-body grid grid-cols-2 md:grid-cols-4 gap-3">
        {CONFIGS.map((cfg) => {
          const active = value === cfg.id;
          return (
            <button
              key={cfg.id}
              type="button"
              id={`config-${cfg.id}`}
              onClick={() => onChange(cfg.id)}
              className={[
                'text-left rounded-lg border p-3 transition-colors duration-150',
                active
                  ? 'border-brand-500 bg-brand-50 ring-1 ring-brand-500'
                  : 'border-slate-200 hover:border-brand-300 hover:bg-slate-50',
              ].join(' ')}
            >
              <p className={`text-sm font-semibold ${active ? 'text-brand-700' : 'text-slate-700'}`}>
                {cfg.label}
              </p>
              <p className="text-xs text-slate-500 mt-0.5 leading-snug">
                {cfg.description}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}

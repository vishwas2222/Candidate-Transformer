function ExperienceEntry({ entry, index }) {
  const title     = entry.title     || entry.header || 'Role';
  const company   = entry.company   || '';
  const location  = entry.location  || '';
  const startDate = entry.start_date || '';
  const endDate   = entry.end_date   || '';
  const desc      = Array.isArray(entry.description) ? entry.description : [];

  const period = [startDate, endDate].filter(Boolean).join(' – ');

  return (
    <div className={index > 0 ? 'pt-5 border-t border-slate-100' : ''}>
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-1">
        <div>
          <h3 className="text-sm font-bold text-slate-800">{title}</h3>
          <p className="text-sm text-slate-600">
            {[company, location].filter(Boolean).join(' · ')}
          </p>
        </div>
        {period && (
          <span className="shrink-0 text-xs font-medium text-slate-500 bg-slate-100
                           rounded-full px-3 py-1 self-start">
            {period}
          </span>
        )}
      </div>

      {desc.length > 0 && (
        <ul className="mt-3 space-y-1.5">
          {desc.map((bullet, i) => (
            <li key={i} className="flex gap-2 text-sm text-slate-600">
              <span className="text-brand-400 mt-1 shrink-0">›</span>
              <span>{bullet}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function ExperienceCard({ candidate }) {
  const c = candidate?.candidate || candidate || {};
  const rawExp = c.experience?.value ?? c.experience ?? [];
  const experience = Array.isArray(rawExp) ? rawExp : [];

  if (experience.length === 0) return null;

  return (
    <div className="card">
      <div className="card-header">
        <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <h2 className="section-title">Experience</h2>
        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs
                         font-semibold bg-slate-100 text-slate-600">
          {experience.length} {experience.length === 1 ? 'role' : 'roles'}
        </span>
      </div>

      <div className="card-body space-y-5">
        {experience.map((entry, i) => (
          <ExperienceEntry key={i} entry={entry} index={i} />
        ))}
      </div>
    </div>
  );
}

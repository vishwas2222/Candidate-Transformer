function EducationEntry({ entry, index }) {
  const degree         = entry.degree         || '';
  const specialization = entry.specialization  || '';
  const institution    = entry.institution    || entry.school || '';
  const startDate      = entry.start_date     || '';
  const endDate        = entry.end_date       || '';
  const cgpa           = entry.cgpa           || null;
  const percentage     = entry.percentage     || null;
  const grade          = entry.grade          || null;
  const desc           = Array.isArray(entry.description) ? entry.description : [];

  const period = [startDate, endDate].filter(Boolean).join(' – ');

  const degreeLabel = [degree, specialization].filter(Boolean).join(', ');

  return (
    <div className={index > 0 ? 'pt-5 border-t border-slate-100' : ''}>
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-1">
        <div>
          <h3 className="text-sm font-bold text-slate-800">{degreeLabel || 'Degree'}</h3>
          <p className="text-sm text-slate-600">{institution}</p>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {period && (
            <span className="text-xs font-medium text-slate-500 bg-slate-100 rounded-full px-3 py-1">
              {period}
            </span>
          )}
          <div className="flex gap-1.5">
            {cgpa && (
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-700
                               bg-amber-50 border border-amber-200 rounded-full px-2.5 py-0.5">
                CGPA {cgpa}
              </span>
            )}
            {percentage && (
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700
                               bg-emerald-50 border border-emerald-200 rounded-full px-2.5 py-0.5">
                {percentage}%
              </span>
            )}
            {grade && !cgpa && !percentage && (
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-purple-700
                               bg-purple-50 border border-purple-200 rounded-full px-2.5 py-0.5">
                {grade}
              </span>
            )}
          </div>
        </div>
      </div>

      {desc.length > 0 && (
        <ul className="mt-3 space-y-1 text-sm text-slate-600">
          {desc.map((d, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-brand-400 mt-0.5 shrink-0">›</span>
              <span>{d}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function EducationCard({ candidate }) {
  const c = candidate?.candidate || candidate || {};
  const rawEdu = c.education?.value ?? c.education ?? [];
  const education = Array.isArray(rawEdu) ? rawEdu : [];

  if (education.length === 0) return null;

  return (
    <div className="card">
      <div className="card-header">
        <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path d="M12 14l9-5-9-5-9 5 9 5z" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
          <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z"
            strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
        </svg>
        <h2 className="section-title">Education</h2>
        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs
                         font-semibold bg-slate-100 text-slate-600">
          {education.length}
        </span>
      </div>

      <div className="card-body space-y-5">
        {education.map((entry, i) => (
          <EducationEntry key={i} entry={entry} index={i} />
        ))}
      </div>
    </div>
  );
}

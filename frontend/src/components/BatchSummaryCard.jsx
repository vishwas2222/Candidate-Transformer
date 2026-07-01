// ── Helpers ───────────────────────────────────────────────────────────────────
function unwrap(v) {
  return v && typeof v === 'object' && 'value' in v ? v.value : v;
}

function getScore(c) {
  if (!c) return 0;
  const name     = unwrap(c.full_name)   || '';
  const emails   = unwrap(c.emails)      || [];
  const phones   = unwrap(c.phones)      || [];
  const edu      = unwrap(c.education)   || [];
  const skills   = unwrap(c.skills)      || [];
  const exp      = unwrap(c.experience)  || [];
  const projects = unwrap(c.projects)    || [];
  const links    = unwrap(c.links)       || {};
  const location = unwrap(c.location)   || {};

  const checks = {
    full_name:  name.trim().length > 1,
    email:      emails.length > 0,
    phone:      phones.length > 0,
    education:  edu.length > 0,
    skills:     skills.length >= 3,
    experience: exp.length > 0,
    projects:   projects.length > 0,
    linkedin:   !!links.linkedin,
    github:     !!links.github,
    location:   !!(location.city || location.region),
  };
  const WEIGHTS = { full_name: 12, email: 12, phone: 10, education: 15,
                    skills: 15, experience: 12, projects: 8, linkedin: 6, github: 6, location: 4 };
  const earned = Object.entries(checks).reduce((s, [k, v]) => s + (v ? WEIGHTS[k] : 0), 0);
  return earned; // out of 100
}

function scoreColor(pct) {
  if (pct >= 80) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
  if (pct >= 60) return 'text-blue-700 bg-blue-50 border-blue-200';
  if (pct >= 40) return 'text-amber-700 bg-amber-50 border-amber-200';
  return 'text-red-700 bg-red-50 border-red-200';
}

function Check({ ok }) {
  if (ok) return (
    <svg className="w-4 h-4 text-emerald-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
    </svg>
  );
  return (
    <svg className="w-4 h-4 text-red-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function BatchSummaryCard({ results, onSelect, selectedIndex }) {
  if (!results || results.length === 0) return null;

  const successResults = results.filter(r => r.status === 'success');
  const errorResults   = results.filter(r => r.status === 'error');

  return (
    <div className="card">
      {/* Header */}
      <div className="card-header">
        <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <h2 className="section-title">Batch Results</h2>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2.5 py-1">
            {successResults.length} processed
          </span>
          {errorResults.length > 0 && (
            <span className="text-xs font-semibold text-red-700 bg-red-50 border border-red-200 rounded-full px-2.5 py-1">
              {errorResults.length} failed
            </span>
          )}
        </div>
      </div>

      <div className="card-body space-y-4">

        {/* Errors */}
        {errorResults.map((r, i) => (
          <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-red-50 border border-red-200 text-sm">
            <svg className="w-4 h-4 text-red-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="font-semibold text-red-800">{r.filename}</p>
              <p className="text-red-600 text-xs mt-0.5">{r.error}</p>
            </div>
          </div>
        ))}

        {/* Comparison table */}
        {successResults.length > 0 && (
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="text-left px-4 py-3 font-semibold text-slate-600 whitespace-nowrap">#</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600 whitespace-nowrap">Name</th>
                  <th className="text-center px-3 py-3 font-semibold text-slate-600 whitespace-nowrap">Score</th>
                  <th className="text-center px-3 py-3 font-semibold text-slate-600 whitespace-nowrap">Email</th>
                  <th className="text-center px-3 py-3 font-semibold text-slate-600 whitespace-nowrap">Phone</th>
                  <th className="text-center px-3 py-3 font-semibold text-slate-600 whitespace-nowrap">Education</th>
                  <th className="text-center px-3 py-3 font-semibold text-slate-600 whitespace-nowrap">Experience</th>
                  <th className="text-center px-3 py-3 font-semibold text-slate-600 whitespace-nowrap">Skills</th>
                  <th className="text-center px-3 py-3 font-semibold text-slate-600 whitespace-nowrap">Projects</th>
                  <th className="text-center px-3 py-3 font-semibold text-slate-600 whitespace-nowrap">LinkedIn</th>
                  <th className="text-center px-3 py-3 font-semibold text-slate-600 whitespace-nowrap">GitHub</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {successResults.map((r, idx) => {
                  const c       = r.candidate?.candidate || r.candidate || {};
                  const name    = unwrap(c.full_name)   || r.filename;
                  const emails  = unwrap(c.emails)      || [];
                  const phones  = unwrap(c.phones)      || [];
                  const edu     = unwrap(c.education)   || [];
                  const skills  = unwrap(c.skills)      || [];
                  const exp     = unwrap(c.experience)  || [];
                  const proj    = unwrap(c.projects)    || [];
                  const links   = unwrap(c.links)       || {};
                  const score   = getScore(c);
                  const isSelected = selectedIndex === results.indexOf(r);

                  return (
                    <tr
                      key={idx}
                      onClick={() => onSelect(results.indexOf(r))}
                      className={`border-b border-slate-100 cursor-pointer transition-colors
                                  ${isSelected
                                    ? 'bg-brand-50 border-brand-200'
                                    : 'hover:bg-slate-50'}`}
                    >
                      <td className="px-4 py-3 text-slate-400 text-xs tabular-nums">{idx + 1}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center
                                          text-white text-xs font-bold shrink-0">
                            {name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-semibold text-slate-800 whitespace-nowrap">{name}</p>
                            <p className="text-xs text-slate-400 truncate max-w-[140px]">{r.filename}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-3 text-center">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${scoreColor(score)}`}>
                          {score}%
                        </span>
                      </td>
                      <td className="px-3 py-3"><Check ok={emails.length > 0} /></td>
                      <td className="px-3 py-3"><Check ok={phones.length > 0} /></td>
                      <td className="px-3 py-3"><Check ok={edu.length > 0} /></td>
                      <td className="px-3 py-3"><Check ok={exp.length > 0} /></td>
                      <td className="px-3 py-3 text-center">
                        <span className={`text-xs font-semibold ${skills.length > 0 ? 'text-emerald-600' : 'text-slate-400'}`}>
                          {skills.length > 0 ? skills.length : '—'}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-center">
                        <span className={`text-xs font-semibold ${proj.length > 0 ? 'text-emerald-600' : 'text-slate-400'}`}>
                          {proj.length > 0 ? proj.length : '—'}
                        </span>
                      </td>
                      <td className="px-3 py-3"><Check ok={!!links.linkedin} /></td>
                      <td className="px-3 py-3"><Check ok={!!links.github} /></td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          className={`text-xs font-semibold px-3 py-1.5 rounded-lg border transition-colors
                                      ${isSelected
                                        ? 'bg-brand-600 text-white border-brand-600'
                                        : 'text-brand-600 border-brand-200 hover:bg-brand-50'}`}
                        >
                          {isSelected ? 'Viewing' : 'View'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <p className="text-xs text-slate-400 text-center">
          Click any row to view that candidate's full profile below ↓
        </p>
      </div>
    </div>
  );
}

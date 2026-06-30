// ── Scoring weights (total = 100 points) ─────────────────────────────────────
const SCORE_ITEMS = [
  { key: 'full_name',   label: 'Full Name',          pts: 12, icon: 'person'   },
  { key: 'email',       label: 'Email Address',       pts: 12, icon: 'email'    },
  { key: 'phone',       label: 'Phone Number',        pts: 10, icon: 'phone'    },
  { key: 'education',   label: 'Education',           pts: 15, icon: 'edu'      },
  { key: 'skills',      label: 'Technical Skills',    pts: 15, icon: 'skills'   },
  { key: 'experience',  label: 'Work Experience',     pts: 12, icon: 'work'     },
  { key: 'projects',    label: 'Projects',            pts: 8,  icon: 'project'  },
  { key: 'linkedin',    label: 'LinkedIn Profile',    pts: 6,  icon: 'linkedin' },
  { key: 'github',      label: 'GitHub Profile',      pts: 6,  icon: 'github'   },
  { key: 'location',    label: 'Location',            pts: 4,  icon: 'location' },
];

// ── Evaluate which items pass ─────────────────────────────────────────────────
function evaluateCandidate(c) {
  const unwrap = (v) => (v && typeof v === 'object' && 'value' in v ? v.value : v);

  const name     = unwrap(c.full_name)   || '';
  const emails   = unwrap(c.emails)      || [];
  const phones   = unwrap(c.phones)      || [];
  const edu      = unwrap(c.education)   || [];
  const skills   = unwrap(c.skills)      || [];
  const exp      = unwrap(c.experience)  || [];
  const projects = unwrap(c.projects)    || [];
  const links    = unwrap(c.links)       || {};
  const location = unwrap(c.location)   || {};

  return {
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
}

// ── Derive strengths and missing from evaluated results ───────────────────────
function deriveInsights(c, evaluated) {
  const unwrap = (v) => (v && typeof v === 'object' && 'value' in v ? v.value : v);
  const edu    = unwrap(c.education)  || [];
  const skills = unwrap(c.skills)    || [];
  const exp    = unwrap(c.experience)|| [];
  const proj   = unwrap(c.projects)  || [];

  const strengths = [];
  const missing   = [];

  // Strengths
  if (edu.length >= 2)    strengths.push('Strong Academic Background');
  if (skills.length >= 15) strengths.push('Rich Technical Skill Set');
  else if (skills.length >= 5) strengths.push('Good Technical Skills');
  if (exp.length > 0)     strengths.push('Work Experience Present');
  if (proj.length >= 3)   strengths.push('Strong Project Portfolio');
  else if (proj.length > 0) strengths.push('Projects Included');
  if (evaluated.email && evaluated.phone) strengths.push('Complete Contact Information');
  if (evaluated.linkedin) strengths.push('LinkedIn Profile Linked');
  if (evaluated.github)   strengths.push('GitHub Portfolio Linked');

  // Missing
  if (!evaluated.experience) missing.push('No Work Experience Found');
  if (!evaluated.linkedin)   missing.push('No LinkedIn Profile');
  if (!evaluated.github)     missing.push('No GitHub Profile');
  if (!evaluated.location)   missing.push('No Location Detected');
  if (skills.length < 3)     missing.push('Too Few Skills Listed');
  if (!evaluated.projects)   missing.push('No Projects Found');

  return { strengths, missing };
}

// ── Score colour ──────────────────────────────────────────────────────────────
function scoreColor(pct) {
  if (pct >= 80) return { bar: 'from-emerald-500 to-green-400',  text: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200',  label: 'Excellent' };
  if (pct >= 60) return { bar: 'from-brand-500 to-brand-400',    text: 'text-brand-700',   bg: 'bg-brand-50 border-brand-200',      label: 'Good'      };
  if (pct >= 40) return { bar: 'from-amber-500 to-yellow-400',   text: 'text-amber-700',   bg: 'bg-amber-50 border-amber-200',      label: 'Fair'      };
  return           { bar: 'from-red-500 to-rose-400',            text: 'text-red-700',     bg: 'bg-red-50 border-red-200',          label: 'Weak'      };
}

// ── Icons ─────────────────────────────────────────────────────────────────────
function ItemIcon({ type, pass }) {
  const cls = `w-4 h-4 shrink-0 ${pass ? 'text-emerald-500' : 'text-red-400'}`;
  if (pass) return (
    <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
    </svg>
  );
  return (
    <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function QualityScoreCard({ candidate }) {
  const c = candidate?.candidate || candidate || {};
  const evaluated = evaluateCandidate(c);

  // Compute score
  const earned = SCORE_ITEMS.reduce((sum, item) => sum + (evaluated[item.key] ? item.pts : 0), 0);
  const total  = SCORE_ITEMS.reduce((sum, item) => sum + item.pts, 0);
  const pct    = Math.round((earned / total) * 100);
  const color  = scoreColor(pct);

  const { strengths, missing } = deriveInsights(c, evaluated);

  // Animate bar width via inline style
  const barWidth = `${pct}%`;

  return (
    <div className="card">
      {/* Header */}
      <div className="card-header">
        <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <h2 className="section-title">Candidate Quality Score</h2>
        <span className={`ml-auto text-xs font-bold px-3 py-1 rounded-full border ${color.bg} ${color.text}`}>
          {color.label}
        </span>
      </div>

      <div className="card-body space-y-6">

        {/* ── Score bar ── */}
        <div className="space-y-2">
          <div className="flex items-end justify-between">
            <span className="text-sm font-medium text-slate-600">Profile Completeness</span>
            <span className={`text-3xl font-extrabold tabular-nums ${color.text}`}>
              {pct}<span className="text-lg font-bold">%</span>
            </span>
          </div>

          {/* Track */}
          <div className="relative h-4 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full bg-gradient-to-r ${color.bar} transition-all duration-700 ease-out`}
              style={{ width: barWidth }}
            />
          </div>

          <div className="flex justify-between text-xs text-slate-400">
            <span>{earned} / {total} points</span>
            <span>{SCORE_ITEMS.filter(i => evaluated[i.key]).length} of {SCORE_ITEMS.length} fields present</span>
          </div>
        </div>

        {/* ── Checklist + Insights (two-column on md+) ── */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* Checklist */}
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
              Field Checklist
            </h3>
            <ul className="space-y-2">
              {SCORE_ITEMS.map((item) => {
                const pass = evaluated[item.key];
                return (
                  <li key={item.key}
                      className={`flex items-center justify-between gap-3 px-3 py-2 rounded-lg text-sm
                                  ${pass
                                    ? 'bg-emerald-50 text-emerald-800'
                                    : 'bg-red-50 text-red-700'}`}>
                    <div className="flex items-center gap-2">
                      <ItemIcon pass={pass} />
                      <span className="font-medium">{item.label}</span>
                    </div>
                    <span className={`text-xs font-semibold tabular-nums
                                      ${pass ? 'text-emerald-600' : 'text-red-400'}`}>
                      {pass ? `+${item.pts}` : `0/${item.pts}`}
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>

          {/* Insights */}
          <div className="space-y-5">

            {/* Strengths */}
            {strengths.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  Strengths
                </h3>
                <ul className="space-y-2">
                  {strengths.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <svg className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-slate-700">{s}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Missing */}
            {missing.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  Missing / Weak Areas
                </h3>
                <ul className="space-y-2">
                  {missing.map((m, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <svg className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                      </svg>
                      <span className="text-slate-600">{m}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Perfect score message */}
            {missing.length === 0 && (
              <div className="flex items-center gap-3 p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
                <svg className="w-8 h-8 text-emerald-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
                <div>
                  <p className="text-sm font-bold text-emerald-800">Complete Profile!</p>
                  <p className="text-xs text-emerald-600">All key information is present.</p>
                </div>
              </div>
            )}

          </div>
        </div>

      </div>
    </div>
  );
}

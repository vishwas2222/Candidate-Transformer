export default function SkillsCard({ candidate }) {
  const c = candidate?.candidate || candidate || {};
  const rawSkills = c.skills?.value ?? c.skills ?? [];
  const skills = Array.isArray(rawSkills) ? rawSkills : [];

  if (skills.length === 0) return null;

  // Skills may be plain strings OR {name, confidence, sources} objects
  const getName = (s) => (typeof s === 'string' ? s : s?.name ?? String(s));
  const getConf = (s) => (typeof s === 'object' && s?.confidence != null ? s.confidence : null);

  return (
    <div className="card">
      <div className="card-header">
        <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
        </svg>
        <h2 className="section-title">Skills</h2>
        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs
                         font-semibold bg-brand-100 text-brand-700">
          {skills.length}
        </span>
      </div>

      <div className="card-body">
        <div className="flex flex-wrap gap-2">
          {skills.map((skill, i) => {
            const name = getName(skill);
            const conf = getConf(skill);
            return (
              <span key={i} className="skill-chip" title={conf != null ? `Confidence: ${(conf*100).toFixed(0)}%` : undefined}>
                {name}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}

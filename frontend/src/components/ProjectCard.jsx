function ProjectEntry({ project, index }) {
  const name   = project.project_name || project.name || `Project ${index + 1}`;
  const start  = project.start_date || '';
  const end    = project.end_date   || '';
  const tech   = Array.isArray(project.technology_stack) ? project.technology_stack : [];
  const desc   = Array.isArray(project.description)     ? project.description      : [];

  const period = [start, end].filter(Boolean).join(' – ');

  return (
    <div className={index > 0 ? 'pt-5 border-t border-slate-100' : ''}>
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-1">
        <h3 className="text-sm font-bold text-slate-800">{name}</h3>
        {period && (
          <span className="shrink-0 text-xs font-medium text-slate-500 bg-slate-100
                           rounded-full px-3 py-1 self-start">
            {period}
          </span>
        )}
      </div>

      {tech.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {tech.map((t, i) => (
            <span key={i}
              className="text-xs font-medium px-2 py-0.5 rounded-full
                         bg-violet-50 text-violet-700 border border-violet-200">
              {t}
            </span>
          ))}
        </div>
      )}

      {desc.length > 0 && (
        <ul className="mt-3 space-y-1.5">
          {desc.map((bullet, i) => (
            <li key={i} className="flex gap-2 text-sm text-slate-600">
              <span className="text-brand-400 mt-0.5 shrink-0">›</span>
              <span>{bullet}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function ProjectCard({ candidate }) {
  const c = candidate?.candidate || candidate || {};
  const rawProj = c.projects?.value ?? c.projects ?? [];
  const projects = Array.isArray(rawProj) ? rawProj : [];

  if (projects.length === 0) return null;

  return (
    <div className="card">
      <div className="card-header">
        <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <h2 className="section-title">Projects</h2>
        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs
                         font-semibold bg-slate-100 text-slate-600">
          {projects.length}
        </span>
      </div>

      <div className="card-body space-y-5">
        {projects.map((proj, i) => (
          <ProjectEntry key={i} project={proj} index={i} />
        ))}
      </div>
    </div>
  );
}

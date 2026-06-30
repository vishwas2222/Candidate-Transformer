function MetaBadge({ label, value }) {
  if (!value && value !== 0) return null;
  return (
    <span className="meta-badge">
      <span className="text-slate-400">{label}:</span>
      <span className="text-slate-600 font-semibold">{value}</span>
    </span>
  );
}

function InfoRow({ label, value, href }) {
  if (!value) return null;
  return (
    <div className="flex flex-col gap-0.5">
      <span className="label">{label}</span>
      {href ? (
        <a href={href} className="value text-brand-600 hover:underline break-all">{value}</a>
      ) : (
        <span className="value">{value}</span>
      )}
    </div>
  );
}

export default function CandidateCard({ candidate }) {
  const c = candidate?.candidate || candidate || {};

  const fullName      = c.full_name?.value      ?? c.full_name      ?? '—';
  const emails        = c.emails?.value         ?? c.emails         ?? [];
  const phones        = c.phones?.value         ?? c.phones         ?? [];
  const headline      = c.headline?.value       ?? c.headline       ?? '';
  const currentCompany= c.current_company?.value?? c.current_company?? '';
  const title         = c.title?.value          ?? c.title          ?? '';

  const nameConf    = c.full_name?.confidence;
  const emailConf   = c.emails?.confidence;
  const sources     = c.full_name?.sources;

  const email = Array.isArray(emails) ? emails[0] : emails;
  const phone = Array.isArray(phones) ? phones[0] : phones;

  return (
    <div className="card">
      <div className="card-header">
        <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        <h2 className="section-title">Candidate Profile</h2>

        <div className="ml-auto flex flex-wrap gap-1.5">
          {nameConf !== undefined && (
            <MetaBadge label="confidence" value={`${(nameConf * 100).toFixed(0)}%`} />
          )}
          {sources?.length > 0 && (
            <MetaBadge label="sources" value={sources.join(', ')} />
          )}
        </div>
      </div>

      <div className="card-body">
        {/* Avatar + name row */}
        <div className="flex items-center gap-4 mb-6">
          <div className="w-14 h-14 rounded-full bg-brand-600 flex items-center justify-center text-white
                          text-xl font-bold shrink-0 select-none">
            {fullName !== '—' ? fullName.charAt(0).toUpperCase() : '?'}
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-900">{fullName}</h3>
            {(title || currentCompany) && (
              <p className="text-sm text-slate-500 mt-0.5">
                {[title, currentCompany].filter(Boolean).join(' · ')}
              </p>
            )}
            {headline && (
              <p className="text-sm text-slate-600 mt-1 italic">{headline}</p>
            )}
          </div>
        </div>

        {/* Info grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <InfoRow label="Email" value={email} href={email ? `mailto:${email}` : undefined} />
          <InfoRow label="Phone" value={phone} />
          <InfoRow label="Current Company" value={currentCompany} />
          <InfoRow label="Title" value={title} />
          <InfoRow label="Headline" value={headline} />
          {emails.length > 1 && (
            <div className="flex flex-col gap-0.5">
              <span className="label">All Emails</span>
              {emails.map((e, i) => (
                <a key={i} href={`mailto:${e}`} className="value text-brand-600 hover:underline text-xs">
                  {e}
                </a>
              ))}
            </div>
          )}
        </div>

        {/* Confidence hint */}
        {emailConf !== undefined && (
          <div className="mt-4 pt-4 border-t border-slate-100">
            <div className="flex items-center gap-2">
              <span className="label">Email confidence</span>
              <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-brand-500 rounded-full"
                  style={{ width: `${(emailConf * 100).toFixed(0)}%` }}
                />
              </div>
              <span className="text-xs font-semibold text-slate-600">
                {(emailConf * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

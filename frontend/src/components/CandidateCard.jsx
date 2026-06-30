// ── Helpers ───────────────────────────────────────────────────────────────────
function MetaBadge({ label, value }) {
  if (!value && value !== 0) return null;
  return (
    <span className="meta-badge">
      <span className="text-slate-400">{label}:</span>
      <span className="text-slate-600 font-semibold">{value}</span>
    </span>
  );
}

function InfoRow({ label, value, href, mono = false }) {
  if (!value) return null;
  return (
    <div className="flex flex-col gap-0.5">
      <span className="label">{label}</span>
      {href ? (
        <a href={href} className="value text-brand-600 hover:underline break-all" target="_blank" rel="noreferrer">{value}</a>
      ) : (
        <span className={`value ${mono ? 'font-mono text-xs' : ''}`}>{value}</span>
      )}
    </div>
  );
}

function LinkRow({ icon, label, url }) {
  if (!url) return null;
  const display = url.replace(/^https?:\/\//, '').replace(/\/$/, '');
  return (
    <a href={url} target="_blank" rel="noreferrer"
       className="flex items-center gap-2 text-sm text-brand-600 hover:text-brand-800 hover:underline transition-colors">
      {icon}
      <span className="truncate">{display}</span>
    </a>
  );
}

// ── Icons ─────────────────────────────────────────────────────────────────────
const GitHubIcon = () => (
  <svg className="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
  </svg>
);

const LinkedInIcon = () => (
  <svg className="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 24 24">
    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
  </svg>
);

const GlobeIcon = () => (
  <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
  </svg>
);

const LocationIcon = () => (
  <svg className="w-4 h-4 shrink-0 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

// ── Main component ────────────────────────────────────────────────────────────
export default function CandidateCard({ candidate }) {
  const c = candidate?.candidate || candidate || {};

  // Unwrap CandidateField wrappers (when include_confidence/sources is on)
  const unwrap = (v) => (v && typeof v === 'object' && 'value' in v ? v.value : v);

  const fullName       = unwrap(c.full_name)       ?? '—';
  const emails         = unwrap(c.emails)          ?? [];
  const phones         = unwrap(c.phones)          ?? [];
  const headline       = unwrap(c.headline)        ?? '';
  const currentCompany = unwrap(c.current_company) ?? '';
  const title          = unwrap(c.title)           ?? '';
  const location       = unwrap(c.location)        ?? {};
  const links          = unwrap(c.links)           ?? {};
  const yearsExp       = unwrap(c.years_experience);
  const candidateId    = unwrap(c.candidate_id)    ?? '';
  const overallConf    = c.overall_confidence;

  // Provenance badges (shown in analytics mode)
  const nameConf  = c.full_name?.confidence;
  const emailConf = c.emails?.confidence;
  const sources   = c.full_name?.sources;

  const email = Array.isArray(emails) ? emails[0] : emails;
  const phone = Array.isArray(phones) ? phones[0] : phones;

  // Format location string
  const locationStr = [location.city, location.region, location.country]
    .filter(Boolean).join(', ');

  const hasLinks = links.github || links.linkedin || links.portfolio;

  return (
    <div className="card">
      <div className="card-header">
        <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        <h2 className="section-title">Candidate Profile</h2>

        <div className="ml-auto flex flex-wrap gap-1.5">
          {overallConf !== undefined && overallConf !== null && (
            <MetaBadge label="overall confidence" value={`${(overallConf * 100).toFixed(0)}%`} />
          )}
          {nameConf !== undefined && (
            <MetaBadge label="name confidence" value={`${(nameConf * 100).toFixed(0)}%`} />
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
          <div className="flex-1 min-w-0">
            <h3 className="text-xl font-bold text-slate-900">{fullName}</h3>
            {(title || currentCompany) && (
              <p className="text-sm text-slate-500 mt-0.5">
                {[title, currentCompany].filter(Boolean).join(' · ')}
              </p>
            )}
            {headline && (
              <p className="text-sm text-slate-600 mt-1 italic">{headline}</p>
            )}
            {locationStr && (
              <div className="flex items-center gap-1 mt-1.5">
                <LocationIcon />
                <span className="text-xs text-slate-500">{locationStr}</span>
              </div>
            )}
          </div>
        </div>

        {/* Info grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <InfoRow label="Email"           value={email}           href={email ? `mailto:${email}` : undefined} />
          <InfoRow label="Phone"           value={phone} />
          <InfoRow label="Current Company" value={currentCompany} />
          <InfoRow label="Title"           value={title} />
          <InfoRow label="Headline"        value={headline} />
          {yearsExp !== null && yearsExp !== undefined && (
            <InfoRow label="Years of Experience" value={`${yearsExp} yr${yearsExp !== 1 ? 's' : ''}`} />
          )}
          {emails.length > 1 && (
            <div className="flex flex-col gap-0.5">
              <span className="label">All Emails</span>
              {emails.map((e, i) => (
                <a key={i} href={`mailto:${e}`} className="value text-brand-600 hover:underline text-xs">{e}</a>
              ))}
            </div>
          )}
        </div>

        {/* Links row */}
        {hasLinks && (
          <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap gap-4">
            <LinkRow icon={<GitHubIcon />}   label="GitHub"    url={links.github} />
            <LinkRow icon={<LinkedInIcon />} label="LinkedIn"  url={links.linkedin} />
            <LinkRow icon={<GlobeIcon />}    label="Portfolio" url={links.portfolio} />
            {(links.other || []).map((u, i) => (
              <LinkRow key={i} icon={<GlobeIcon />} label="Link" url={u} />
            ))}
          </div>
        )}

        {/* Candidate ID + confidence footer */}
        {(candidateId || emailConf !== undefined) && (
          <div className="mt-4 pt-4 border-t border-slate-100 space-y-2">
            {candidateId && (
              <InfoRow label="Candidate ID" value={candidateId} mono />
            )}
            {emailConf !== undefined && (
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
            )}
          </div>
        )}
      </div>
    </div>
  );
}

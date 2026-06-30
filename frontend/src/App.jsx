import { useState } from 'react';
import { transformCandidate } from './services/api';

import Header         from './components/Header';
import UploadCard     from './components/UploadCard';
import ConfigSelector from './components/ConfigSelector';
import CandidateCard  from './components/CandidateCard';
import SkillsCard     from './components/SkillsCard';
import ExperienceCard from './components/ExperienceCard';
import EducationCard  from './components/EducationCard';
import ProjectCard    from './components/ProjectCard';
import DownloadButtons from './components/DownloadButtons';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorCard      from './components/ErrorCard';

export default function App() {
  // ── Input state ────────────────────────────────────────────────────────────
  const [resumeFile, setResumeFile] = useState(null);
  const [csvFile,    setCsvFile]    = useState(null);
  const [config,     setConfig]     = useState('default');

  // ── Processing state ───────────────────────────────────────────────────────
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);
  const [result,   setResult]   = useState(null);  // { candidate, validation_report }

  // ── Transform ──────────────────────────────────────────────────────────────
  const handleTransform = async () => {
    if (!resumeFile) {
      setError('Please upload a resume PDF before transforming.');
      return;
    }
    setError(null);
    setLoading(true);
    setResult(null);

    try {
      const data = await transformCandidate(resumeFile, csvFile, config);
      setResult(data);
    } catch (err) {
      const msg =
        err?.response?.data?.error ||
        err?.message ||
        'An unexpected error occurred. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const hasResult = !!result;

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 sm:px-6 py-8 space-y-6">

        {/* ── Hero ─────────────────────────────────────────────────────────── */}
        {!hasResult && !loading && (
          <div className="text-center py-4">
            <h2 className="text-2xl font-bold text-slate-900">
              Multi-Source Candidate Data Transformer
            </h2>
            <p className="text-slate-500 mt-2 text-sm max-w-xl mx-auto">
              Upload a resume PDF and an optional recruiter CSV to extract, normalise,
              merge, and project structured candidate data.
            </p>
          </div>
        )}

        {/* ── Input panel ──────────────────────────────────────────────────── */}
        {!hasResult && (
          <div className="space-y-4">
            <UploadCard
              resumeFile={resumeFile}
              csvFile={csvFile}
              onResumeChange={setResumeFile}
              onCsvChange={setCsvFile}
            />
            <ConfigSelector value={config} onChange={setConfig} />

            {/* Error */}
            {error && (
              <ErrorCard error={error} onDismiss={() => setError(null)} />
            )}

            {/* Transform CTA */}
            <div className="flex justify-end">
              <button
                id="btn-transform"
                type="button"
                onClick={handleTransform}
                disabled={loading || !resumeFile}
                className="btn-primary flex items-center gap-2 px-8 py-3 text-base"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Transform
              </button>
            </div>
          </div>
        )}

        {/* ── Loading ───────────────────────────────────────────────────────── */}
        {loading && (
          <div className="card">
            <div className="card-body">
              <LoadingSpinner message="Transforming candidate data…" />
            </div>
          </div>
        )}

        {/* ── Results ──────────────────────────────────────────────────────── */}
        {hasResult && !loading && (
          <>
            {/* Result toolbar */}
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700
                                 bg-emerald-50 border border-emerald-200 rounded-full px-3 py-1.5">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Transformation complete
                </span>
                <span className="text-xs text-slate-500">
                  Config: <strong>{config}</strong>
                  {csvFile ? ' · Resume + CSV' : ' · Resume only'}
                </span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setResult(null);
                  setError(null);
                  setResumeFile(null);
                  setCsvFile(null);
                  setConfig('default');
                }}
                className="btn-secondary flex items-center gap-2 text-xs"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                New Transform
              </button>
            </div>

            {error && (
              <ErrorCard error={error} onDismiss={() => setError(null)} />
            )}

            {/* Cards */}
            <CandidateCard  candidate={result.candidate} />
            <SkillsCard     candidate={result.candidate} />
            <ExperienceCard candidate={result.candidate} />
            <EducationCard  candidate={result.candidate} />
            <ProjectCard    candidate={result.candidate} />
            <DownloadButtons
              candidate={result.candidate}
              validationReport={result.validation_report}
            />
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white mt-8">
        <div className="max-w-6xl mx-auto px-6 h-12 flex items-center justify-between">
          <span className="text-xs text-slate-400">
            Candidate Transformer · Eightfold AI Internship Assignment
          </span>
          <span className="text-xs text-slate-400">
            Flask API · React · Tailwind CSS
          </span>
        </div>
      </footer>
    </div>
  );
}

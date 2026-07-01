import { useState } from 'react';
import { transformCandidate, transformBatch } from './services/api';

import Header           from './components/Header';
import UploadCard       from './components/UploadCard';
import ConfigSelector   from './components/ConfigSelector';
import BatchSummaryCard from './components/BatchSummaryCard';
import QualityScoreCard from './components/QualityScoreCard';
import CandidateCard    from './components/CandidateCard';
import SkillsCard       from './components/SkillsCard';
import ExperienceCard   from './components/ExperienceCard';
import EducationCard    from './components/EducationCard';
import ProjectCard      from './components/ProjectCard';
import DownloadButtons  from './components/DownloadButtons';
import LoadingSpinner   from './components/LoadingSpinner';
import ErrorCard        from './components/ErrorCard';

export default function App() {
  // ── Input state ────────────────────────────────────────────────────────────
  const [resumeFiles, setResumeFiles] = useState([]);   // always an array now
  const [csvFile,     setCsvFile]     = useState(null);
  const [config,      setConfig]      = useState('default');

  // ── Processing state ───────────────────────────────────────────────────────
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);

  // Batch: results[] — each has { filename, status, candidate, validation_report }
  // Single treated as batch of 1 for simplicity
  const [batchResults,    setBatchResults]    = useState(null);   // full array
  const [selectedIndex,   setSelectedIndex]   = useState(0);      // which candidate to display

  const isBatch    = resumeFiles.length > 1;
  const hasResults = !!batchResults;

  // Active candidate result (the one whose cards are shown below the table)
  const activeResult = batchResults?.[selectedIndex];
  const activeCandidate = activeResult?.candidate;
  const activeValidation = activeResult?.validation_report;

  // ── Transform ──────────────────────────────────────────────────────────────
  const handleTransform = async () => {
    if (resumeFiles.length === 0 && !csvFile) {
      setError('Please upload at least one Resume PDF or a Recruiter CSV.');
      return;
    }
    setError(null);
    setLoading(true);
    setBatchResults(null);
    setSelectedIndex(0);

    try {
      if (resumeFiles.length <= 1) {
        // Single mode — use original endpoint
        const data = await transformCandidate(resumeFiles[0] ?? null, csvFile, config);
        setBatchResults([{ ...data, filename: resumeFiles[0]?.name ?? 'upload', status: 'success' }]);
      } else {
        // Batch mode
        const data = await transformBatch(resumeFiles, csvFile, config);
        setBatchResults(data.results);
      }
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

  const handleReset = () => {
    setBatchResults(null);
    setError(null);
    setResumeFiles([]);
    setCsvFile(null);
    setConfig('default');
    setSelectedIndex(0);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 sm:px-6 py-8 space-y-6">

        {/* ── Hero ─────────────────────────────────────────────────────────── */}
        {!hasResults && !loading && (
          <div className="text-center py-4">
            <h2 className="text-2xl font-bold text-slate-900">
              Multi-Source Candidate Data Transformer
            </h2>
            <p className="text-slate-500 mt-2 text-sm max-w-xl mx-auto">
              Upload one or multiple resume PDFs with an optional recruiter CSV to extract,
              normalise, merge, and project structured candidate data.
            </p>
          </div>
        )}

        {/* ── Input panel ──────────────────────────────────────────────────── */}
        {!hasResults && (
          <div className="space-y-4">
            <UploadCard
              resumeFiles={resumeFiles}
              csvFile={csvFile}
              onResumeChange={setResumeFiles}
              onCsvChange={setCsvFile}
            />
            <ConfigSelector value={config} onChange={setConfig} />

            {error && <ErrorCard error={error} onDismiss={() => setError(null)} />}

            <div className="flex justify-end">
              <button
                id="btn-transform"
                type="button"
                onClick={handleTransform}
                disabled={loading || (resumeFiles.length === 0 && !csvFile)}
                className="btn-primary flex items-center gap-2 px-8 py-3 text-base"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                {isBatch ? `Transform ${resumeFiles.length} Resumes` : 'Transform'}
              </button>
            </div>
          </div>
        )}

        {/* ── Loading ───────────────────────────────────────────────────────── */}
        {loading && (
          <div className="card">
            <div className="card-body">
              <LoadingSpinner
                message={
                  resumeFiles.length > 1
                    ? `Processing ${resumeFiles.length} resumes…`
                    : 'Transforming candidate data…'
                }
              />
            </div>
          </div>
        )}

        {/* ── Results ──────────────────────────────────────────────────────── */}
        {hasResults && !loading && (
          <>
            {/* Result toolbar */}
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700
                                 bg-emerald-50 border border-emerald-200 rounded-full px-3 py-1.5">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {batchResults.length > 1
                    ? `${batchResults.filter(r => r.status === 'success').length} of ${batchResults.length} processed`
                    : 'Transformation complete'}
                </span>
                <span className="text-xs text-slate-500">
                  Config: <strong>{config}</strong>
                  {csvFile ? ' · Resume + CSV' : ' · Resume only'}
                </span>
              </div>
              <button type="button" onClick={handleReset}
                className="btn-secondary flex items-center gap-2 text-xs">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                New Transform
              </button>
            </div>

            {error && <ErrorCard error={error} onDismiss={() => setError(null)} />}

            {/* Batch table (always shown when >1 result) */}
            {batchResults.length > 1 && (
              <BatchSummaryCard
                results={batchResults}
                onSelect={setSelectedIndex}
                selectedIndex={selectedIndex}
              />
            )}

            {/* Individual candidate cards */}
            {activeCandidate && (
              <>
                <QualityScoreCard  candidate={activeCandidate} />
                <CandidateCard     candidate={activeCandidate} />
                <SkillsCard        candidate={activeCandidate} />
                <ExperienceCard    candidate={activeCandidate} />
                <EducationCard     candidate={activeCandidate} />
                <ProjectCard       candidate={activeCandidate} />
                <DownloadButtons
                  candidate={activeCandidate}
                  validationReport={activeValidation}
                />
              </>
            )}

            {/* Error result selected */}
            {activeResult?.status === 'error' && (
              <div className="card">
                <div className="card-body">
                  <ErrorCard
                    error={`Could not process "${activeResult.filename}": ${activeResult.error}`}
                    onDismiss={null}
                  />
                </div>
              </div>
            )}
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

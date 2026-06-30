import axios from 'axios';

// During development Vite proxies /api/* → http://localhost:5000
// In production, serve the Flask API and built React from the same host.
const BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000, // 2 min — PDF parsing can take a moment
});


/**
 * Transforms a resume (+ optional CSV) using the backend pipeline.
 *
 * @param {File}   resumeFile   Required PDF resume
 * @param {File|null} csvFile   Optional recruiter CSV
 * @param {string} config       Profile name: default | minimal | recruiter | analytics
 * @returns {Promise<{candidate: object, validation_report: object}>}
 */
export async function transformCandidate(resumeFile, csvFile, config = 'default') {
  const form = new FormData();
  form.append('resume', resumeFile);
  if (csvFile) form.append('csv', csvFile);
  form.append('config', config);

  const { data } = await api.post('/api/transform', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export default api;

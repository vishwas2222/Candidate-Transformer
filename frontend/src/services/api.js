import axios from 'axios';

// During development Vite proxies /api/* → http://localhost:5000
// In production, serve the Flask API and built React from the same host.
const BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 300_000, // 5 min — batch of PDFs may take longer
});


/**
 * Transforms a single resume (+ optional CSV) using the backend pipeline.
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


/**
 * Transforms multiple resumes in one request.
 * @param {File[]}    resumeFiles  Array of PDF files
 * @param {File|null} csvFile      Optional shared recruiter CSV
 * @param {string}    config       Profile name
 * @returns {Promise<{results: Array, total: number}>}
 */
export async function transformBatch(resumeFiles, csvFile, config = 'default') {
  const form = new FormData();
  resumeFiles.forEach((f) => form.append('resumes', f));
  if (csvFile) form.append('csv', csvFile);
  form.append('config', config);

  const { data } = await api.post('/api/transform/batch', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export default api;

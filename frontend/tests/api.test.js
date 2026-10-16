import test from 'node:test';
import assert from 'node:assert/strict';
import { request } from '../src/api.js';

test('request returns JSON and sends the API prefix', async () => {
  const original = global.fetch;
  global.fetch = async (url, options) => {
    assert.equal(url, '/api/tickets');
    assert.equal(options.headers['Content-Type'], 'application/json');
    return { ok: true, status: 200, json: async () => [{ id: 1 }] };
  };
  try { assert.deepEqual(await request('/tickets'), [{ id: 1 }]); }
  finally { global.fetch = original; }
});

test('request accepts empty delete responses', async () => {
  const original = global.fetch;
  global.fetch = async () => ({ ok: true, status: 204 });
  try { assert.equal(await request('/tickets/1', { method: 'DELETE' }), null); }
  finally { global.fetch = original; }
});

test('request surfaces server failures instead of reporting success', async () => {
  const original = global.fetch;
  global.fetch = async () => ({ ok: false, json: async () => ({ detail: 'Ticket not found' }) });
  try { await assert.rejects(request('/tickets/99'), /Ticket not found/); }
  finally { global.fetch = original; }
});

test('request handles unavailable servers with non-JSON responses', async () => {
  const original = global.fetch;
  global.fetch = async () => ({ ok: false, json: async () => { throw new Error('Invalid JSON'); } });
  try { await assert.rejects(request('/tickets'), /Unable to save/); }
  finally { global.fetch = original; }
});

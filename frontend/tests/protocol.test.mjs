import test from 'node:test';
import assert from 'node:assert/strict';
import { addressOK, hashOK, loadJournal, parseRelease, stageOf, uint, verifyReleaseReadback } from '../src/protocol.mjs';

const address = '0x' + '1'.repeat(40);
const hash = 'a'.repeat(64);

test('configuration guards reject zero or malformed identities', () => {
  assert.equal(addressOK(address), true);
  assert.equal(addressOK('0x' + '0'.repeat(40)), false);
  assert.equal(hashOK('0x' + '2'.repeat(64)), true);
  assert.throws(() => uint('-1'));
});

test('release readback parser enforces exact shape', () => {
  const raw = ['REVIEWED', address, 'signal-kit', '1.4.2', '1.5.0', 'MINOR', hash, hash, 'NON_BREAKING', 'COMPLIANT', 'COMPATIBLE_CHANGE', '{"surface_change":"ADDITIVE"}'].join('|');
  const record = parseRelease(raw);
  assert.equal(record.compliance, 'COMPLIANT');
  assert.equal(record.observations.surface_change, 'ADDITIVE');
  assert.throws(() => parseRelease('REVIEWED|broken'));
});

test('journal rejects corrupt records', () => {
  assert.deepEqual(loadJournal(null), []);
  assert.throws(() => loadJournal('[{"hash":"bad"}]'));
  const row = { hash: '0x' + '2'.repeat(64), sender: address, contract: address, args: ['0'], method: 'seal_release', chainId: 61999, stage: 'PENDING', detail: '', createdAt: '' };
  assert.equal(loadJournal(JSON.stringify([row])).length, 1);
});

test('finality alone is insufficient without successful execution and consensus', () => {
  assert.equal(stageOf({ statusName: 'PROPOSING' }).stage, 'PENDING');
  assert.equal(stageOf({ statusName: 'FINALIZED' }).stage, 'FAILED');
  const tx = { statusName: 'FINALIZED', resultName: 'MAJORITY_AGREE', consensus_data: { leader_receipt: { execution_result: 'SUCCESS', result: { status: 'return' } } } };
  assert.equal(stageOf(tx).stage, 'READBACK_REQUIRED');
});

test('method-specific authoritative readback is mandatory', () => {
  const base = { hash: '0x' + '2'.repeat(64), sender: address, contract: address, args: ['signal-kit', '1.4.2', '1.5.0'], method: 'create_release', chainId: 61999, stage: 'PENDING', detail: '', createdAt: '' };
  const current = { publisher: address, package: 'signal-kit', oldVersion: '1.4.2', newVersion: '1.5.0', status: 'DRAFT', compliance: 'UNEVALUATED' };
  assert.equal(verifyReleaseReadback(base, '0', current), true);
  assert.throws(() => verifyReleaseReadback(base, '0', { ...current, package: 'other' }));
  assert.equal(verifyReleaseReadback({ ...base, method: 'assess_release', args: ['0'] }, 'ASSESSMENT_RETRYABLE', { ...current, status: 'SEALED' }), true);
  assert.throws(() => verifyReleaseReadback({ ...base, method: 'assess_release', args: ['0'] }, 'COMPLIANT', { ...current, status: 'SEALED' }));
});

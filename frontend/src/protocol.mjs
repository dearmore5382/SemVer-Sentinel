export const ZERO = '0x' + '0'.repeat(40);
export const addressOK = (value) =>
  typeof value === 'string' && /^0x[0-9a-fA-F]{40}$/.test(value) && value.toLowerCase() !== ZERO;
export const hashOK = (value) => typeof value === 'string' && /^0x[0-9a-fA-F]{64}$/.test(value);
export function uint(value) {
  const text = String(value);
  if (!/^(0|[1-9]\d*)$/.test(text) || BigInt(text) >= 2n ** 256n) throw new Error('Enter an unsigned release ID.');
  return BigInt(text);
}
export function parseRelease(raw) {
  if (typeof raw !== 'string' || raw === 'RELEASE_NOT_FOUND') throw new Error('Release record not found.');
  const p = raw.split('|');
  if (p.length !== 10 || !addressOK(p[1]) || !p[2]) {
    throw new Error('Malformed contract readback.');
  }
  return {
    status: p[0], publisher: p[1], package: p[2], oldVersion: p[3], newVersion: p[4],
    bump: p[5], category: p[6], compliance: p[7], reason: p[8], observations: p[9] ? JSON.parse(p[9]) : null,
  };
}
export function loadJournal(text) {
  if (!text) return [];
  const rows = JSON.parse(text);
  if (!Array.isArray(rows) || rows.length > 200 || rows.some((row) =>
    !hashOK(row.hash) || !addressOK(row.sender) || !addressOK(row.contract) ||
    !Array.isArray(row.args) || typeof row.method !== 'string' || !Number.isInteger(row.chainId))) {
    throw new Error('Transaction journal is damaged. Export it before clearing browser storage.');
  }
  return rows;
}
export function stageOf(tx) {
  const status = String(tx?.statusName ?? tx?.status ?? 'UNKNOWN');
  if (status !== 'FINALIZED') return { stage: 'PENDING', detail: status };
  const receipts = tx?.consensus_data?.leader_receipt;
  const leader = Array.isArray(receipts) ? receipts.at(-1) : receipts;
  if (!leader || leader.execution_result !== 'SUCCESS' || leader.result?.status !== 'return') {
    return { stage: 'FAILED', detail: 'Finalized without successful contract execution.' };
  }
  const votes = Object.values(tx?.consensus_data?.votes ?? {});
  const agreed = tx?.resultName === 'MAJORITY_AGREE' || (votes.length >= 3 && votes.filter((v) => v === 'agree').length > votes.length / 2);
  if (!agreed) return { stage: 'FAILED', detail: 'Consensus agreement was not established.' };
  return { stage: 'READBACK_REQUIRED', detail: 'Finalized with successful execution and consensus.' };
}
export function verifyReleaseReadback(record, returned, current) {
  const allowed = {
    seal_release: ['RELEASE_SEALED'], cancel_draft: ['RELEASE_CANCELLED'],
    assess_release: ['COMPLIANT', 'VERSION_VIOLATION', 'REVIEW_REQUIRED', 'ARTIFACT_REJECTED', 'ASSESSMENT_RETRYABLE'],
  };
  if (record.method !== 'create_release' && !allowed[record.method]?.includes(returned)) {
    throw new Error(`Contract rejected the requested transition: ${returned}`);
  }
  if (record.method === 'create_release') {
    const args = record.args;
    if (current.publisher.toLowerCase() !== record.sender.toLowerCase() || current.package !== args[0].toLowerCase() || current.oldVersion !== args[1] || current.newVersion !== args[2] || current.status !== 'DRAFT') {
      throw new Error('Created record does not match sealed inputs.');
    }
  } else if (record.method === 'seal_release' && current.status !== 'SEALED') {
    throw new Error('Seal readback mismatch.');
  } else if (record.method === 'cancel_draft' && current.status !== 'CANCELLED') {
    throw new Error('Cancellation readback mismatch.');
  } else if (record.method === 'assess_release' && returned === 'ASSESSMENT_RETRYABLE' && current.status !== 'SEALED') {
    throw new Error('Retry-safe assessment mutated state.');
  } else if (record.method === 'assess_release' && returned === 'ARTIFACT_REJECTED' && (current.status !== 'REJECTED' || current.compliance !== returned)) {
    throw new Error('Artifact rejection readback mismatch.');
  } else if (record.method === 'assess_release' && !['ASSESSMENT_RETRYABLE', 'ARTIFACT_REJECTED'].includes(returned) && (current.status !== 'REVIEWED' || current.compliance !== returned)) {
    throw new Error('Assessment readback mismatch.');
  }
  return true;
}

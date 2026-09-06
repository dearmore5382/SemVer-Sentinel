export const ZERO: string;
export function addressOK(value: unknown): value is string;
export function hashOK(value: unknown): value is string;
export function uint(value: unknown): bigint;
export type ReleaseRecord = {
  status: string; publisher: string; package: string; oldVersion: string; newVersion: string;
  bump: string; category: string; compliance: string;
  reason: string; observations: Record<string, string> | null;
};
export function parseRelease(raw: unknown): ReleaseRecord;
export type JournalEntry = { hash: string; sender: string; contract: string; args: string[]; method: string; chainId: number; stage: string; detail: string; createdAt: string };
export function loadJournal(text: string | null): JournalEntry[];
export function stageOf(tx: unknown): { stage: string; detail: string };
export function verifyReleaseReadback(record: JournalEntry, returned: string, current: ReleaseRecord): true;

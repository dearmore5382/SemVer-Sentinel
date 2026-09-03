import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { abi, createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { TransactionHashVariant } from 'genlayer-js/types';
import { ArrowRight, Braces, Check, CircleAlert, GitCompareArrows, History, LockKeyhole, Radar, RefreshCw, ShieldCheck, Terminal, Wallet } from 'lucide-react';
import deployment from './deployment.json';
import { addressOK, hashOK, loadJournal, parseRelease, stageOf, uint, verifyReleaseReadback } from './protocol.mjs';

type Provider = NonNullable<Parameters<typeof createClient>[0]>['provider'];
type ReleaseRecord = {
  status: string; publisher: string; package: string; oldVersion: string; newVersion: string;
  bump: string; oldHash: string; newHash: string; category: string; compliance: string;
  reason: string; observations: Record<string, string> | null;
};
type JournalEntry = {
  hash: string; sender: string; contract: string; args: string[]; method: string;
  chainId: number; stage: string; detail: string; createdAt: string;
};
const address = deployment.contractAddress as `0x${string}`;
const configured = addressOK(address) && /^[a-f0-9]{64}$/.test(deployment.sourceSha256);
const writesEnabled = configured && deployment.liveAuditVerified;
const reader = createClient({ chain: studionet });
const journalKey = 'semver-sentinel:journal:v1';
const intentKey = 'semver-sentinel:intent:v1';
const initialOld = 'GET /signals/{id} -> 200 { id: string, state: string }';
const initialNew = initialOld + '\nGET /signals/{id}/history -> 200 [{ state: string }]';

const short = (value: string) => value.length > 13 ? `${value.slice(0, 7)}…${value.slice(-5)}` : value;
const errorText = (error: unknown) => error instanceof Error ? error.message : 'The operation could not be completed.';
const same = (left: unknown, right: unknown) => typeof left === 'string' && typeof right === 'string' && left.toLowerCase() === right.toLowerCase();
const decode = (value: unknown) => {
  if (!value || typeof value !== 'object' || !('raw' in value) || !Array.isArray(value.raw)) {
    throw new Error('Receipt calldata is unavailable.');
  }
  return abi.calldata.decode(new Uint8Array(value.raw));
};

export default function App() {
  const [wallet, setWallet] = useState('');
  const [notice, setNotice] = useState(configured ? 'Read access is ready.' : 'Deployment pending — preview mode is active.');
  const [busy, setBusy] = useState(false);
  const [releaseId, setReleaseId] = useState('0');
  const [record, setRecord] = useState<ReleaseRecord | null>(null);
  const [journal, setJournal] = useState<JournalEntry[]>([]);
  const [oldApi, setOldApi] = useState(initialOld);
  const [newApi, setNewApi] = useState(initialNew);
  const lines = useMemo(() => ({ old: oldApi.split('\n'), next: newApi.split('\n') }), [oldApi, newApi]);

  useEffect(() => {
    try { setJournal(loadJournal(localStorage.getItem(journalKey))); }
    catch (error) { setNotice(errorText(error)); }
  }, []);

  const saveJournal = (rows: JournalEntry[]) => {
    localStorage.setItem(journalKey, JSON.stringify(rows));
    setJournal(rows);
  };

  async function connect() {
    setBusy(true);
    try {
      if (!writesEnabled) throw new Error('Writes unlock only after contract deployment and live verification.');
      const provider = (window as unknown as { ethereum?: Provider }).ethereum;
      if (!provider) throw new Error('Install an EIP-1193 browser wallet.');
      const accounts = await provider.request({ method: 'eth_requestAccounts' }) as string[];
      if (!addressOK(accounts[0])) throw new Error('No valid account selected.');
      await provider.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: '0x' + studionet.id.toString(16) }] });
      setWallet(accounts[0]);
      setNotice('Wallet connected on Studionet.');
    } catch (error) { setNotice(errorText(error)); }
    finally { setBusy(false); }
  }

  async function loadRelease() {
    setBusy(true);
    try {
      if (!configured) throw new Error('Deploy and configure the reviewed contract before reading live state.');
      const raw = await reader.readContract({ address, functionName: 'get_release', args: [uint(releaseId)], transactionHashVariant: TransactionHashVariant.LATEST_FINAL });
      setRecord(parseRelease(raw));
      setNotice(`Loaded finalized release ${releaseId}.`);
    } catch (error) { setNotice(errorText(error)); }
    finally { setBusy(false); }
  }

  async function send(method: string, args: (string | bigint)[]) {
    setBusy(true);
    try {
      if (!writesEnabled || !wallet) throw new Error('Connect a verified Studionet wallet before writing.');
      if (localStorage.getItem(intentKey) || journal.some((row) => !['VERIFIED', 'FAILED'].includes(row.stage))) {
        throw new Error('Reconcile the existing transaction before sending another.');
      }
      const provider = (window as unknown as { ethereum?: Provider }).ethereum;
      if (!provider) throw new Error('Wallet disconnected.');
      const intent = { method, args: args.map(String), sender: wallet, contract: address, chainId: studionet.id, createdAt: new Date().toISOString() };
      localStorage.setItem(intentKey, JSON.stringify(intent));
      const writer = createClient({ chain: studionet, account: wallet as `0x${string}`, provider });
      let hash: unknown;
      try { hash = await writer.writeContract({ address, functionName: method, args, value: 0n, leaderOnly: false }); }
      catch (error) {
        if (typeof error === 'object' && error !== null && 'code' in error && error.code === 4001) localStorage.removeItem(intentKey);
        throw error;
      }
      if (!hashOK(hash)) throw new Error('Wallet returned an invalid transaction hash. Preserve the intent and do not resubmit.');
      const transactionHash = String(hash);
      const row: JournalEntry = { ...intent, hash: transactionHash, stage: 'PENDING', detail: 'Submitted once; awaiting finality.' };
      saveJournal([...journal, row]);
      localStorage.removeItem(intentKey);
      setNotice(`Submitted ${short(transactionHash)}. Recheck this hash; do not submit again.`);
    } catch (error) { setNotice(errorText(error)); }
    finally { setBusy(false); }
  }

  async function reconcile(row: JournalEntry) {
    setBusy(true);
    try {
      const tx = await reader.getTransaction({ hash: row.hash as Parameters<typeof reader.getTransaction>[0]['hash'] });
      const stage = stageOf(tx);
      let updated = { ...row, ...stage };
      if (stage.stage === 'READBACK_REQUIRED') {
        const transaction = tx as unknown as {
          hash?: string; txId?: string; from_address?: string; sender?: string; to_address?: string; recipient?: string;
          data?: { calldata?: unknown }; consensus_data?: { leader_receipt?: unknown | unknown[] };
        };
        if (!same(transaction.hash ?? transaction.txId, row.hash) || !same(transaction.from_address ?? transaction.sender, row.sender) || !same(transaction.to_address ?? transaction.recipient, row.contract)) {
          throw new Error('Finalized receipt identity does not match the journal.');
        }
        const receipts = transaction.consensus_data?.leader_receipt;
        const leader = (Array.isArray(receipts) ? receipts.at(-1) : receipts) as { calldata?: unknown; result?: { payload?: unknown } } | undefined;
        const call = decode(transaction.data?.calldata ?? leader?.calldata);
        const returned = decode(leader?.result?.payload);
        if (!(call instanceof Map) || call.get('method') !== row.method || JSON.stringify((call.get('args') as unknown[]).map(String)) !== JSON.stringify(row.args)) {
          throw new Error('Finalized receipt method or arguments do not match the journal.');
        }
        if (!['string', 'number', 'bigint'].includes(typeof returned)) throw new Error('Unexpected contract return type.');
        const result = String(returned);
        const id = row.method === 'create_release' ? result : row.args[0];
        uint(id);
        const raw = await reader.readContract({ address, functionName: 'get_release', args: [uint(id)], transactionHashVariant: TransactionHashVariant.LATEST_FINAL });
        const current = parseRelease(raw);
        verifyReleaseReadback(row, result, current);
        setRecord(current); setReleaseId(id);
        updated = { ...updated, stage: 'VERIFIED', detail: 'Finalized, consensus agreed and authoritative readback completed.' };
      }
      saveJournal(journal.map((item) => item.hash === row.hash ? updated : item));
      setNotice(updated.detail);
    } catch (error) { setNotice(errorText(error)); }
    finally { setBusy(false); }
  }

  function createRelease(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    send('create_release', [String(data.get('packageName')), String(data.get('oldVersion')), String(data.get('newVersion')), String(data.get('policy')), oldApi, newApi]);
  }

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="SemVer Sentinel home">
          <img src="/semver-sentinel-logo.png" alt="SemVer Sentinel shield" />
          <span>SemVer<br /><b>Sentinel</b></span>
        </a>
        <nav><a href="#review">Review desk</a><a href="#registry">Registry</a><a href="#protocol">Protocol</a></nav>
        <button className="wallet" onClick={connect} disabled={busy || !writesEnabled}><Wallet size={17} />{wallet ? short(wallet) : 'Connect wallet'}</button>
      </header>

      <section className="hero" id="top">
        <div className="eyebrow"><Radar size={15} /> GenLayer compatibility intelligence</div>
        <h1>Know when a release<br /><em>crosses the line.</em></h1>
        <p>Seal two API snapshots. Let independent validators inspect semantic change. Keep the version decision deterministic and reviewable.</p>
        <div className="hero-actions"><a className="primary" href="#review">Open review desk <ArrowRight size={18} /></a><a className="secondary" href="#protocol">Read the protocol</a></div>
        <div className="release-rail" aria-label="Release review stages">
          {['Snapshot', 'Seal', 'Consensus', 'Record'].map((label, index) => <div key={label}><span>{index < 2 ? <Check size={14} /> : index + 1}</span><b>{label}</b><small>{['Exact inputs', 'Publisher lock', 'Independent review', 'Immutable outcome'][index]}</small></div>)}
        </div>
      </section>

      <section className="workspace" id="review">
        <div className="section-heading"><div><span className="kicker">01 / REVIEW DESK</span><h2>Compare the contract, not the marketing.</h2></div><div className={`network ${configured ? 'ready' : ''}`}><i /> Studionet · {configured ? short(address) : 'deployment pending'}</div></div>
        <div className="review-grid">
          <form className="release-form" onSubmit={createRelease}>
            <div className="panel-title"><Braces /><div><b>Release envelope</b><span>Publisher-sealed inputs</span></div></div>
            <label>Package name<input name="packageName" defaultValue="signal-kit" maxLength={100} required /></label>
            <div className="version-row"><label>Previous version<input name="oldVersion" defaultValue="1.4.2" pattern="(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)" required /></label><GitCompareArrows /><label>Candidate version<input name="newVersion" defaultValue="1.5.0" pattern="(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)" required /></label></div>
            <label>Compatibility policy<textarea name="policy" defaultValue="Existing operations, required request fields, response fields and documented behavior must remain compatible." maxLength={1200} required /></label>
            <button className="submit" disabled={!writesEnabled || busy}>Create release record <ArrowRight size={17} /></button>
            {!writesEnabled && <p className="guard"><LockKeyhole size={15} /> Write actions remain locked until the reviewed contract is deployed and live-verified.</p>}
          </form>
          <div className="diff-panel">
            <div className="diff-head"><div><span className="dot coral" /> Previous API</div><div><span className="dot mint" /> Candidate API</div></div>
            <div className="editors"><label><span>OLD SNAPSHOT</span><textarea value={oldApi} onChange={(e) => setOldApi(e.target.value)} maxLength={3500} /></label><label><span>NEW SNAPSHOT</span><textarea value={newApi} onChange={(e) => setNewApi(e.target.value)} maxLength={3500} /></label></div>
            <div className="line-summary"><span>− {lines.old.length} sealed line{lines.old.length === 1 ? '' : 's'}</span><span>+ {lines.next.length} candidate line{lines.next.length === 1 ? '' : 's'}</span></div>
          </div>
        </div>
      </section>

      <section className="registry" id="registry">
        <div className="section-heading"><div><span className="kicker">02 / ON-CHAIN REGISTRY</span><h2>Read the finalized record.</h2></div></div>
        <div className="registry-grid">
          <div className="lookup"><label>Release ID<input value={releaseId} onChange={(e) => setReleaseId(e.target.value)} inputMode="numeric" /></label><button onClick={loadRelease} disabled={!configured || busy}>Load record <RefreshCw size={16} /></button><div className="quick-actions"><button onClick={() => send('seal_release', [uint(releaseId)])} disabled={!writesEnabled || busy}>Seal</button><button onClick={() => send('assess_release', [uint(releaseId)])} disabled={!writesEnabled || busy}>Assess</button><button onClick={() => send('cancel_draft', [uint(releaseId)])} disabled={!writesEnabled || busy}>Cancel draft</button></div><output>{notice}</output></div>
          <article className="result-card">
            {record ? <><div className="result-top"><span className={`verdict ${record.compliance.toLowerCase()}`}>{record.compliance}</span><span>{record.bump} release</span></div><h3>{record.package}</h3><p className="version-title">{record.oldVersion} <ArrowRight size={18} /> {record.newVersion}</p><dl><div><dt>State</dt><dd>{record.status}</dd></div><div><dt>Semantic class</dt><dd>{record.category}</dd></div><div><dt>Reason</dt><dd>{record.reason}</dd></div><div><dt>Publisher</dt><dd>{short(record.publisher)}</dd></div></dl><div className="hashes"><span>OLD {short(record.oldHash)}</span><span>NEW {short(record.newHash)}</span></div></> : <div className="empty"><ShieldCheck /><h3>No record loaded</h3><p>After deployment, load a finalized release without trusting a frontend-generated verdict.</p></div>}
          </article>
        </div>
      </section>

      <section className="protocol" id="protocol">
        <div><span className="kicker">03 / SAFETY MODEL</span><h2>AI observes.<br />The protocol decides.</h2><p>The model never chooses compliance or version policy. It returns a closed set of compatibility observations; deterministic precedence maps those observations to the stored outcome.</p></div>
        <div className="principles">{[[Terminal, 'Text-only boundary', 'No images, browsing or mutable external sources.'], [GitCompareArrows, 'Effect-aligned consensus', 'Validators compare canonical outcome, not prose.'], [CircleAlert, 'Retry-safe failure', 'Runtime failure keeps the sealed release unchanged.'], [History, 'Terminal history', 'Reviewed and cancelled records cannot be overwritten.']].map(([Icon, title, text]) => { const C = Icon as typeof Terminal; return <article key={String(title)}><C /><div><b>{String(title)}</b><p>{String(text)}</p></div></article>; })}</div>
      </section>

      <section className="journal"><div className="journal-head"><div><span className="kicker">TRANSACTION JOURNAL</span><h2>One intent. One hash.</h2></div><span>{journal.length} entries</span></div>{journal.length ? journal.map((row) => <div className="journal-row" key={row.hash}><span className="journal-icon"><History /></span><div><b>{row.method}</b><small>{short(row.hash)} · {row.stage}</small></div><button onClick={() => reconcile(row)} disabled={busy || row.stage === 'VERIFIED'}>Recheck</button></div>) : <p className="no-journal">No browser transactions yet. Pending hashes will remain here across refreshes.</p>}</section>
      <footer><div className="brand mini"><img src="/semver-sentinel-logo.png" alt="" /><span>SemVer <b>Sentinel</b></span></div><p>A narrow compatibility record for submitted API descriptions. Not a security audit or proof of shipped code.</p><span>Built for GenLayer Studionet</span></footer>
    </main>
  );
}

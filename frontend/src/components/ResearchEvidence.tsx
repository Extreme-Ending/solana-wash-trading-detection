const FACTS = [
  ["Source events", "10,800", "Actual supplied DEX/swap rows"],
  ["Retained", "10,798", "Two invalid rows quarantined"],
  ["Wallets", "2,312", "Identifiers in the full supplied sample"],
  ["Features", "29", "Registered point-in-time wallet features"],
];

const EVALUATION = [
  ["Training reference", "1,754 wallets", "1 September 2025 UTC"],
  ["Holdout snapshot", "2,312 wallets", "1,754 repeated; 382 later entrants"],
  ["IF vs LOF rank agreement", "0.049", "Holdout Spearman correlation"],
  ["IF vs robust MAD", "0.866", "Agreement is not correctness"],
];

export function ResearchEvidence() {
  return (
    <section className="section-shell research-evidence" id="evidence" aria-labelledby="evidence-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Verified experimental snapshot</p>
          <h2 id="evidence-heading">Separate observations from model outputs</h2>
        </div>
        <p>
          These fixed values describe the audited local research snapshot and its label-free
          evaluation. They are not live blockchain statistics.
        </p>
      </div>
      <div className="evidence-grid">
        <article>
          <h3>Observed and processed data</h3>
          <dl>{FACTS.map(([label, value, note]) => <div key={label}><dt>{label}</dt><dd><strong>{value}</strong><span>{note}</span></dd></div>)}</dl>
        </article>
        <article>
          <h3>Experimental model evidence</h3>
          <dl>{EVALUATION.map(([label, value, note]) => <div key={label}><dt>{label}</dt><dd><strong>{value}</strong><span>{note}</span></dd></div>)}</dl>
        </article>
      </div>
      <div className="evidence-boundaries" role="note">
        <p><strong>Actual observations:</strong> audited event counts, processing outcomes and point-in-time snapshots.</p>
        <p><strong>Model outputs:</strong> unitless anomaly scores, ranks and detector-agreement diagnostics without verified outcomes.</p>
        <p><strong>Synthetic examples:</strong> interface and contract demonstrations only; never evaluation evidence.</p>
      </div>
    </section>
  );
}

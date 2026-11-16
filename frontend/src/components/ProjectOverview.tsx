export function ProjectOverview() {
  return (
    <section className="hero" id="overview" aria-labelledby="overview-heading">
      <div className="hero-copy">
        <p className="eyebrow">DSA 8401 · Applied Machine Learning</p>
        <h1 id="overview-heading">Inspect wallet behaviour without overstating the evidence.</h1>
        <p className="hero-lede">
          This research interface transforms user-supplied Solana DEX swap events into
          29 registered, point-in-time wallet features. It supports transparent inspection;
          it does not identify fraud or confirm wash trading. Checksum-pinned anomaly scoring
          is available only when explicitly enabled for the authenticated local demonstration.
        </p>
        <div className="hero-actions">
          <a className="button primary" href="#preview">Preview features</a>
          <a className="button secondary" href="#methodology">Review methodology</a>
        </div>
      </div>
      <aside className="scope-card" aria-label="Research scope">
        <p className="eyebrow">Current evidence boundary</p>
        <dl>
          <div><dt>Data domain</dt><dd>Solana DEX swap events</dd></div>
          <div><dt>Unit</dt><dd>Wallet at a UTC cutoff</dd></div>
          <div><dt>Output</dt><dd>Features and gated anomaly scores</dd></div>
          <div><dt>Ground truth</dt><dd>No verified wash-trading labels</dd></div>
          <div><dt>Anomaly methods</dt><dd>Experimental local mode only</dd></div>
        </dl>
        <p className="scope-note">
          The available data differs from the original NFT marketplace framing. Results must
          therefore be interpreted as trading-behaviour summaries, not NFT fraud evidence.
        </p>
      </aside>
    </section>
  );
}

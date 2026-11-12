export function Header() {
  return (
    <header className="site-header">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <div className="header-inner">
        <a className="brand" href="#overview" aria-label="Solana wallet research dashboard home">
          <span className="brand-mark" aria-hidden="true">S</span>
          <span>
            <strong>Solana Wallet Research</strong>
            <small>Point-in-time feature explorer</small>
          </span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#status">Service</a>
          <a href="#preview">Preview</a>
          <a href="#results">Results</a>
          <a href="#methodology">Methodology</a>
        </nav>
      </div>
    </header>
  );
}

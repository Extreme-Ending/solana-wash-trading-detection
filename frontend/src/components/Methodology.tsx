const PRINCIPLES = [
  {
    number: "01",
    title: "Prepare before modelling",
    text: "Validate schema, types, missingness, event identity, and cutoff semantics before any algorithm sees the data.",
  },
  {
    number: "02",
    title: "Preserve time order",
    text: "Each wallet snapshot uses only events strictly before its UTC scoring timestamp, preventing future information from entering features.",
  },
  {
    number: "03",
    title: "Separate evidence from interpretation",
    text: "Feature values describe submitted behaviour. Without independent labels, they cannot establish confirmed misconduct.",
  },
  {
    number: "04",
    title: "Make work reproducible",
    text: "Registered feature order, versioned rules, deterministic examples, typed contracts, and automated checks make outputs auditable.",
  },
];

export function Methodology() {
  return (
    <section className="section-shell methodology" id="methodology" aria-labelledby="methodology-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Academic foundations</p>
          <h2 id="methodology-heading">From laboratory discipline to research service</h2>
        </div>
        <p>The interface preserves the AML lab emphasis on preparation, validation, evaluation boundaries, and reproducibility.</p>
      </div>
      <div className="principle-grid">
        {PRINCIPLES.map((principle) => (
          <article key={principle.number}>
            <span>{principle.number}</span>
            <h3>{principle.title}</h3>
            <p>{principle.text}</p>
          </article>
        ))}
      </div>
      <div className="limitations">
        <h3>Known limits</h3>
        <ul>
          <li>The source domain is DEX swap activity, not authenticated NFT marketplace trades.</li>
          <li>Submitted events are user-supplied and are not independently verified by this interface.</li>
          <li>No verified wash-trading target is available; unusual behaviour is not ground-truth fraud.</li>
          <li>Feature results depend on the completeness and correctness of the submitted event history.</li>
        </ul>
      </div>
    </section>
  );
}

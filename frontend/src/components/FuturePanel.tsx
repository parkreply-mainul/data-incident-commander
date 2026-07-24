export function FuturePanel({
  title,
  description,
  textAlternative,
}: {
  title: string;
  description: string;
  textAlternative?: string;
}) {
  return (
    <section className="future-panel" aria-disabled="true">
      <div className="future-panel-head"><h3>{title}</h3><span>Unavailable</span></div>
      <p>{description}</p>
      {textAlternative && <small className="text-alternative">{textAlternative}</small>}
    </section>
  );
}

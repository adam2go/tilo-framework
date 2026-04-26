const stages = ["Render", "Observe", "Act", "Memorize"];

export function RoamStatusStrip({ activeIndex = 1 }: { activeIndex?: number }) {
  return (
    <div className="roam-status-strip">
      {stages.map((stage, index) => (
        <div className={index <= activeIndex ? "roam-status-step active" : "roam-status-step"} key={stage}>
          <span>{index + 1}</span>
          <strong>{stage}</strong>
        </div>
      ))}
    </div>
  );
}

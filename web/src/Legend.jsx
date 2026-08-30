import React from "react";

// Composable legend, adapted from the @bklitui/ui/charts `Legend` component to
// this application's dark theme. `@bklitui` is not installed in this project,
// so this is a local equivalent that keeps the same composable API:
//
//   <Legend hoveredIndex={i} onHoverChange={setI}>
//     <LegendItemComponent>
//       <LegendMarker color dashed />
//       <LegendLabel />
//       <LegendValue>…</LegendValue>
//     </LegendItemComponent>
//   </Legend>
//
// LegendItemComponent is cloned with an `index` and the shared hover profile so
// individual items can report hover/focus up to the owning chart.
function Legend({
  title,
  hoveredIndex = null,
  onHoverChange = () => {},
  children,
  className = "",
}) {
  const profile = { hoveredIndex, onHoverChange };
  return (
    <div
      className={`legend${className ? ` ${className}` : ""}`}
      role="group"
      aria-label={title || "Chart series legend"}
      onMouseLeave={() => {
        // A mouse that leaves the legend no longer selects a series.
        if (hoveredIndex != null) onHoverChange(null);
      }}
    >
      {title ? <span className="legend-title">{title}</span> : null}
      <ul className="legend-items">
        {React.Children.map(children, (child, index) =>
          React.isValidElement(child)
            ? React.cloneElement(child, { index, ...profile })
            : child,
        )}
      </ul>
    </div>
  );
}

// One legend entry. Rendered as a real <button> so it is keyboard reachable and
// focuses visibly (the skill's "not hover-only" rule). Every child element
// receives `label` for use as the item's accessible name.
function LegendItemComponent({ index, hoveredIndex, onHoverChange, label, children }) {
  const active = hoveredIndex === index;
  const dimmed = hoveredIndex != null && hoveredIndex !== index;
  return (
    <li className={`legend-item${active ? " is-active" : ""}${dimmed ? " is-dimmed" : ""}`}>
      <button
        type="button"
        className="legend-item-button"
        aria-pressed={active}
        aria-label={label}
        onMouseEnter={() => onHoverChange(index)}
        onFocus={() => onHoverChange(index)}
        onBlur={() => onHoverChange(null)}
      >
        {children}
      </button>
    </li>
  );
}

// Series swatch. `dashed` keeps the distinct line treatment so a series that is
// plotted dashed in the chart reads the same way in the legend (never color-only);
// `variant="bar"` renders a small rounded tile for bar series.
function LegendMarker({ color, dashed = false, variant = "line" }) {
  return (
    <span
      className={`legend-marker${dashed ? " is-dashed" : ""}${variant === "bar" ? " is-bar" : ""}`}
      style={{ "--marker-color": color }}
      aria-hidden="true"
    />
  );
}

function LegendLabel({ children, muted = false }) {
  return <span className={`legend-label${muted ? " is-muted" : ""}`}>{children}</span>;
}

// Optional value column; renders nothing when empty so the row stays compact.
function LegendValue({ children }) {
  return children ? <span className="legend-value">{children}</span> : null;
}

export { Legend, LegendItemComponent, LegendMarker, LegendLabel, LegendValue };
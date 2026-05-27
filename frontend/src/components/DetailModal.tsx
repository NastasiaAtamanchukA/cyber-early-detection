import { useState, type ReactNode } from "react";

type Props = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
  onClose: () => void;
};

export function DetailModal({ title, subtitle, children, footer, onClose }: Props) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <section
        className={expanded ? "modal-card modal-card-fullscreen" : "modal-card"}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="modal-header">
          <div>
            {subtitle && <p>{subtitle}</p>}
            <h2>{title}</h2>
          </div>
          <div className="modal-header-actions">
            <button
              className="secondary-button modal-expand-button"
              onClick={() => setExpanded((value) => !value)}
              type="button"
            >
              {expanded ? "Свернуть" : "На весь экран"}
            </button>
            <button className="icon-button" onClick={onClose} aria-label="Закрыть" type="button">×</button>
          </div>
        </header>
        <div className="modal-body">{children}</div>
        {footer && <footer className="modal-footer">{footer}</footer>}
      </section>
    </div>
  );
}

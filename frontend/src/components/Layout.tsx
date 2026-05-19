import { NavLink } from "react-router-dom";
import type { PropsWithChildren } from "react";

export function Layout({ children }: PropsWithChildren) {
  const linkClass = ({ isActive }: { isActive: boolean }) => (isActive ? "nav-link active" : "nav-link");

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">IS</div>
          <div>
            <h1>Невидимый щит</h1>
            <p>ML-анализ логов</p>
          </div>
        </div>
        <nav>
          <NavLink to="/" className={linkClass}>Дашборд</NavLink>
          <NavLink to="/collection" className={linkClass}>Сбор событий</NavLink>
          <NavLink to="/events" className={linkClass}>События</NavLink>
          <NavLink to="/alerts" className={linkClass}>Алерты</NavLink>
          <NavLink to="/incidents" className={linkClass}>Инциденты</NavLink>
        </nav>
        <div className="sidebar-note">
          <strong>Учебный стенд</strong>
          <span>FastAPI · PostgreSQL · ML · Docker</span>
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}

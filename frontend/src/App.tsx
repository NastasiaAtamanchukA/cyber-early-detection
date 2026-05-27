import { NavLink, Route, Routes } from "react-router-dom";
import { AlertsPage } from "./pages/AlertsPage";
import { CollectionPage } from "./pages/CollectionPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EventsPage } from "./pages/EventsPage";
import { IncidentsPage } from "./pages/IncidentsPage";

const navItems = [
  ["/", "Дашборд"],
  ["/events", "События"],
  ["/alerts", "Алерты"],
  ["/incidents", "Инциденты"],
  ["/collectors", "Сбор логов"],
];

export function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">IS</div>
          <div>
            <strong>Невидимый щит</strong>
            <span>Cyber Early Detection</span>
          </div>
        </div>

        <nav>
          {navItems.map(([to, label]) => (
            <NavLink key={to} to={to} className={({ isActive }) => (isActive ? "active" : undefined)}>
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/collectors" element={<CollectionPage />} />
        </Routes>
      </main>
    </div>
  );
}

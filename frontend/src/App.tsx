import { Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { AlertDetailsPage } from "./pages/AlertDetailsPage";
import { AlertsPage } from "./pages/AlertsPage";
import { CollectionPage } from "./pages/CollectionPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EventsPage } from "./pages/EventsPage";
import { IncidentDetailsPage } from "./pages/IncidentDetailsPage";
import { IncidentsPage } from "./pages/IncidentsPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/collection" element={<CollectionPage />} />
        <Route path="/events" element={<EventsPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/alerts/:id" element={<AlertDetailsPage />} />
        <Route path="/incidents" element={<IncidentsPage />} />
        <Route path="/incidents/:id" element={<IncidentDetailsPage />} />
      </Routes>
    </Layout>
  );
}

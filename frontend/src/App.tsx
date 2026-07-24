import { AppShell } from "./components/AppShell";
import { useRoute } from "./hooks/useRoute";
import { DashboardPage } from "./pages/DashboardPage";
import { InvestigationDetailPage } from "./pages/InvestigationDetailPage";
import { InvestigationsPage } from "./pages/InvestigationsPage";
import { NewInvestigationPage } from "./pages/NewInvestigationPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { SystemStatusPage } from "./pages/SystemStatusPage";

function decodeIncidentId(path: string): string | null {
  const match = /^\/investigations\/([^/]+)$/.exec(path);
  if (!match) return null;
  try {
    return decodeURIComponent(match[1]);
  } catch {
    return null;
  }
}

export default function App() {
  const path = useRoute();
  const incidentId = decodeIncidentId(path);
  let page: React.ReactNode;
  if (path === "/") page = <DashboardPage />;
  else if (path === "/investigations") page = <InvestigationsPage />;
  else if (path === "/investigations/new") page = <NewInvestigationPage />;
  else if (path === "/status") page = <SystemStatusPage />;
  else if (incidentId !== null) page = <InvestigationDetailPage incidentId={incidentId} />;
  else page = <NotFoundPage />;
  return <AppShell path={path}>{page}</AppShell>;
}

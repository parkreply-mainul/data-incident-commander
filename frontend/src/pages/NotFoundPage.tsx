import { EmptyState } from "../components/Feedback";
import { PageHeader } from "../components/PageHeader";
import { navigate } from "../hooks/useRoute";

export function NotFoundPage() {
  return <><PageHeader eyebrow="Navigation" title="Page not found" description="The requested workspace route does not exist." /><EmptyState title="Choose a workspace page" body="Return to the operations overview to continue." action={<button className="button button-secondary" onClick={() => navigate("/")}>Back to overview</button>} /></>;
}

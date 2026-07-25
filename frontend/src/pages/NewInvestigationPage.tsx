import { FormEvent, useRef, useState } from "react";
import { ApiError, api } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { navigate } from "../hooks/useRoute";

type Fields = {
  title: string;
  target: string;
  description: string;
  category: string;
  requesterName: string;
  requesterTeam: string;
};

const EMPTY: Fields = {
  title: "",
  target: "",
  description: "",
  category: "",
  requesterName: "",
  requesterTeam: "",
};

export function NewInvestigationPage() {
  const [fields, setFields] = useState(EMPTY);
  const [errors, setErrors] = useState<Partial<Record<keyof Fields, string>>>({});
  const [submitting, setSubmitting] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const [apiError, setApiError] = useState<ApiError | null>(null);
  const errorRef = useRef<HTMLDivElement>(null);

  const update = (name: keyof Fields, value: string) =>
    setFields((current) => ({ ...current, [name]: value }));

  async function submit(event: FormEvent) {
    event.preventDefault();
    const next: typeof errors = {};
    if (!fields.title.trim()) next.title = "Enter an incident title.";
    if (fields.title.length > 200) next.title = "Use 200 characters or fewer.";
    if (!fields.target.trim()) next.target = "Enter a target asset identifier.";
    if (fields.target.length > 500) next.target = "Use 500 characters or fewer.";
    if (fields.description.length > 4000) next.description = "Use 4,000 characters or fewer.";
    if (fields.category.length > 100) next.category = "Use 100 characters or fewer.";
    setErrors(next);
    if (Object.keys(next).length) {
      setAnnouncement("Review the highlighted form fields.");
      window.setTimeout(() => document.querySelector<HTMLElement>("[aria-invalid='true']")?.focus());
      return;
    }
    setSubmitting(true);
    setApiError(null);
    setAnnouncement("Creating draft investigation.");
    try {
      const requester =
        fields.requesterName.trim() || fields.requesterTeam.trim()
          ? {
              ...(fields.requesterName.trim() && { name: fields.requesterName.trim() }),
              ...(fields.requesterTeam.trim() && { team: fields.requesterTeam.trim() }),
            }
          : undefined;
      const created = await api.createInvestigation({
        title: fields.title.trim(),
        target_asset_id: fields.target.trim(),
        ...(fields.description.trim() && { description: fields.description.trim() }),
        ...(fields.category.trim() && { issue_category: fields.category.trim() }),
        ...(requester && { requester }),
      });
      setAnnouncement(`Draft created with identifier ${created.incident_id}, revision ${created.revision}.`);
      navigate(`/investigations/${created.incident_id}`);
    } catch (caught) {
      const safe = caught instanceof ApiError ? caught : new ApiError("Draft creation failed.", "unknown", "UNKNOWN");
      setApiError(safe);
      setAnnouncement(safe.message);
      window.setTimeout(() => errorRef.current?.focus());
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader eyebrow="Incident intake" title="New investigation" description="Create a factual draft. Evidence and conclusions remain empty until verified dependencies are available." />
      <div className="form-layout">
        <form className="form-card" onSubmit={submit} noValidate>
          <div className="form-section">
            <span className="section-number">01</span><div><h2>Incident identity</h2><p>Describe the signal without assuming a root cause.</p></div>
          </div>
          <Field label="Incident title" name="title" value={fields.title} error={errors.title} required maxLength={200} onChange={(value) => update("title", value)} placeholder="Example: Revenue dashboard data appears stale" />
          <Field label="Target asset identifier" name="target" value={fields.target} error={errors.target} required maxLength={500} onChange={(value) => update("target", value)} placeholder="DataHub dataset URN" hint="Use the identifier from the incident signal. DIC resolves it during verified evidence collection." />
          <Field label="Description" name="description" value={fields.description} error={errors.description} maxLength={4000} textarea onChange={(value) => update("description", value)} placeholder="What was observed, when, and by whom?" />
          <Field label="Issue category" name="category" value={fields.category} error={errors.category} maxLength={100} onChange={(value) => update("category", value)} placeholder="Optional, for example freshness" />
          <div className="form-section form-section-spaced">
            <span className="section-number">02</span><div><h2>Requester context</h2><p>Optional public-safe attribution stored as metadata.</p></div>
          </div>
          <div className="field-row">
            <Field label="Requester name" name="requesterName" value={fields.requesterName} onChange={(value) => update("requesterName", value)} placeholder="Optional" />
            <Field label="Requester team" name="requesterTeam" value={fields.requesterTeam} onChange={(value) => update("requesterTeam", value)} placeholder="Optional" />
          </div>
          {apiError && <div className="inline-error" role="alert" tabIndex={-1} ref={errorRef}><strong>{apiError.code}</strong><p>{apiError.message}</p>{apiError.requestId && <small>Request ID: <code>{apiError.requestId}</code></small>}</div>}
          <div className="form-actions">
            <button type="button" className="button button-secondary" onClick={() => navigate("/investigations")}>Cancel</button>
            <button type="submit" className="button button-primary" disabled={submitting}>{submitting ? "Creating draft…" : "Create draft"}</button>
          </div>
          <p className="sr-only" aria-live="polite">{announcement}</p>
        </form>
        <aside className="context-card">
          <span className="eyebrow">What happens next</span>
          <h2>Draft only</h2>
          <ol><li><strong>A record is created</strong><span>The backend returns an incident ID and revision.</span></li><li><strong>No evidence is inferred</strong><span>Owners, lineage, severity, and remediation wait for verified evidence.</span></li><li><strong>Investigation remains gated</strong><span>DataHub and mandatory MCP verification must complete before evidence collection can proceed.</span></li></ol>
        </aside>
      </div>
    </>
  );
}

function Field({
  label, name, value, onChange, error, required, hint, textarea, maxLength, placeholder
}: {
  label: string; name: string; value: string; onChange: (value: string) => void;
  error?: string; required?: boolean; hint?: string; textarea?: boolean;
  maxLength?: number; placeholder?: string;
}) {
  const describedBy = [hint && `${name}-hint`, error && `${name}-error`].filter(Boolean).join(" ") || undefined;
  const props = {
    id: name, name, value, onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => onChange(event.target.value),
    "aria-invalid": Boolean(error), "aria-describedby": describedBy, required,
    maxLength, placeholder,
  };
  return <div className="field"><label htmlFor={name}>{label}{required && <span aria-hidden="true"> *</span>}</label>{textarea ? <textarea {...props} rows={5} /> : <input {...props} />}{hint && <small id={`${name}-hint`}>{hint}</small>}{error && <small className="field-error" id={`${name}-error`}>{error}</small>}</div>;
}

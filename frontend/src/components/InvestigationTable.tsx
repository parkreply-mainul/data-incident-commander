import type { Investigation } from "../types/api";
import { formatTimestamp } from "../utils/format";
import { navigate } from "../hooks/useRoute";
import { StatusBadge } from "./StatusBadge";

export function InvestigationTable({ items }: { items: Investigation[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Investigation</th><th>Target asset</th><th>State</th><th>Updated</th><th>Revision</th></tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.incident_id}>
              <td>
                <a
                  href={`/investigations/${item.incident_id}`}
                  onClick={(event) => {
                    event.preventDefault();
                    navigate(`/investigations/${item.incident_id}`);
                  }}
                >
                  <strong>{item.title}</strong><small>{item.incident_id}</small>
                </a>
              </td>
              <td><code>{item.target_asset_id}</code></td>
              <td><StatusBadge status={item.state} /></td>
              <td>{formatTimestamp(item.updated_at)}</td>
              <td>r{item.revision}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

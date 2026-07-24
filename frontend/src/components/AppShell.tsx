import { Brand } from "./Brand";
import { navigate } from "../hooks/useRoute";

const NAV = [
  { path: "/", label: "Overview", icon: "⌂" },
  { path: "/investigations", label: "Investigations", icon: "▤" },
  { path: "/investigations/new", label: "New investigation", icon: "+" },
  { path: "/status", label: "System status", icon: "◎" },
];

export function AppShell({
  path,
  children,
}: {
  path: string;
  children: React.ReactNode;
}) {
  const active = (item: string) => {
    if (item === "/") return path === "/";
    if (item === "/investigations/new") return path === item;
    if (item === "/investigations") {
      return path === item || (path.startsWith(`${item}/`) && path !== "/investigations/new");
    }
    return path === item;
  };
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <aside className="sidebar">
        <Brand />
        <nav aria-label="Primary navigation">
          {NAV.map((item) => (
            <a
              key={item.path}
              href={item.path}
              className={active(item.path) ? "nav-link active" : "nav-link"}
              aria-current={active(item.path) ? "page" : undefined}
              onClick={(event) => {
                event.preventDefault();
                navigate(item.path);
              }}
            >
              <span aria-hidden="true">{item.icon}</span>
              <span>{item.label}</span>
            </a>
          ))}
        </nav>
        <div className="sidebar-foot">
          <span className="environment-dot" aria-hidden="true" />
          <div><strong>Local workspace</strong><small>Development boundary</small></div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div><span className="eyebrow">Incident operations</span></div>
          <div className="truth-label"><span aria-hidden="true">◇</span> Evidence-first · No simulated results</div>
        </header>
        <main id="main-content" tabIndex={-1}>{children}</main>
      </div>
    </div>
  );
}

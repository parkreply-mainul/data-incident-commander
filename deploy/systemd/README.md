# systemd Boundary

Future units must run under dedicated users, reference server-side environment
files with restrictive permissions, restart only bounded project services, and
never embed tokens. No unit is active or installed.

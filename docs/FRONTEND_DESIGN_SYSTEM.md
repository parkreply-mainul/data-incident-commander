# Frontend Design System

## Direction

The interface uses a restrained light enterprise incident-operations language:
neutral surfaces, dense but readable records, a dark navigation rail, and
limited blue, green, amber, and red status accents. It is not chat-first and
does not copy DataHub or any third-party branding.

The CSS-authored product mark combines an original geometric shield/grid shape
with the Data Incident Commander name. No stock assets, remote fonts, or
third-party logos are used.

## Tokens

`frontend/src/styles/index.css` defines variables for:

- canvas, surface, elevated surface, and borders;
- primary and secondary text;
- accent, success, warning, danger, and information states;
- spacing, radii, shadows, and typography.

Components use shared primitives for page headers, badges, notices, empty
states, tables, cards, and disabled capability panels. Color is always paired
with a text label, icon/shape, or explanatory message.

## Accessibility baseline

- semantic `header`, `nav`, `main`, `section`, form, and table structures;
- skip link and visible `:focus-visible` treatment;
- actual links and buttons;
- associated labels, descriptions, and field error references;
- `aria-live` feedback for asynchronous outcomes;
- table headings and meaningful empty-state text;
- textual alternatives for future lineage/evidence visualization;
- motion disabled under `prefers-reduced-motion`; and
- layouts that reflow at compact laptop/tablet widths.

Automated component tests cover labels, keyboard activation, focus after
validation and successful creation, live announcements, and non-color status
text. Manual contrast, zoom, and assistive-technology review remain submission
gates.

## Operational states

Implemented visual states include initial loading, empty, populated, API
unavailable, backend validation, dependency unavailable, not found, conflict,
safe internal error, successful draft creation, pagination, not-ready,
partially ready, disabled capability, and offline/network failure.

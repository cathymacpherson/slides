# mq_colloquium_2026

Custom HTML slide deck for a research portfolio colloquium.

## Files

- Edit slides in `index.html`.
- Edit styling in `theme/portfolio-html.css`.
- Edit keyboard navigation and notes behaviour in `scripts/slides.js`.

This deck is a static HTML page with local CSS, JS, and assets.

For repo-wide instructions on creating future talks, see the [root README](../README.md).

## Commands

Use `npm.cmd` on this machine because PowerShell script execution blocks `npm.ps1`.

```powershell
npm.cmd run serve
```

`serve` starts a local browser server at `http://localhost:8000`, so you can open the deck in your browser without any extra build step.

Export a PDF version:

```powershell
npm.cmd run export:pdf
```

The exporter uses local Chrome or Edge to capture the HTML deck and writes `exports/mq_colloquium_2026.pdf`. Slides with fragment animations are expanded into multiple PDF pages, so each build step is preserved for presenting or sharing.

## Slide controls

- `Arrow keys`, `Page Up`, `Page Down`, or `Space` navigate
- `Home` and `End` jump to the start or end
- `N` toggles speaker notes
- `O` toggles overview mode
- `F` toggles fullscreen
- `P` opens a separate presenter view

## Notes

Speaker notes live in `<aside class="notes">` blocks inside each slide in `index.html`.

## Presenter view

- Open the main deck in the browser
- Press `P`
- A separate presenter window will open showing:
  - current slide
  - next slide
  - speaker notes
  - timer
  - slide count

The main deck and presenter window stay in sync through local browser storage.

# slides

Repository for browser-based HTML slide decks.

## How this repo is organized

- Each talk can live in its own folder.
- A talk folder contains:
  - `index.html` for slide content
  - `theme/` for CSS
  - `scripts/` for navigation, notes, and presenter logic
  - `assets/` for images, figures, and diagrams
  - an optional local `README.md` for talk-specific notes

## Create a new presentation

1. Duplicate an existing talk folder such as `mq_colloquium_2026`.
2. Rename the copied folder for the new talk.
3. Replace the slide content in that folder's `index.html`.
4. Add any new figures or images to that folder's `assets/`.
5. Update the local `README.md` if the talk needs specific notes.

## Edit a presentation

- Add or edit slides in `index.html`.
- Use one `<section class="slide">...</section>` block per slide.
- Add speaker notes inside `<aside class="notes">...</aside>` within a slide.
- Put reusable layout and visual styles in the talk's CSS file under `theme/`.
- Put presentation behaviour in the talk's JS file under `scripts/`.

## Run a presentation locally

From inside a talk folder:

```powershell
npm.cmd run serve
```

Then open `http://localhost:8000` in your browser.

Use `npm.cmd` on this machine because PowerShell script execution blocks `npm.ps1`.

## Presenter controls

- `Arrow keys`, `Page Up`, `Page Down`, or `Space` navigate
- `Home` and `End` jump to the start or end
- `N` toggles speaker notes
- `O` toggles overview mode
- `F` toggles fullscreen
- `P` opens presenter view

## Current talks

- [mq_colloquium_2026](./mq_colloquium_2026/README.md)

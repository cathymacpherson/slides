const slides = Array.from(document.querySelectorAll(".slide"));
const counter = document.getElementById("deck-counter");
const notesBody = document.getElementById("notes-body");
const deck = document.getElementById("deck");
const deckViewport = document.querySelector(".deck-viewport");
const params = new URLSearchParams(window.location.search);
const isPresenter = params.get("view") === "presenter";
const isExport = params.get("export") === "1";
const exportStep = Number.parseInt(params.get("step") || "", 10);
const STORAGE_KEY = "perc_conference_slide_state";
const CHANNEL_KEY = "perc_conference_slide_channel";
const MEDIA_STORAGE_KEY = "perc_conference_media_state";
const CLIENT_ID = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
const syncChannel = "BroadcastChannel" in window ? new BroadcastChannel(CHANNEL_KEY) : null;

let currentIndex = 0;
let currentStep = 0;
let presenterRefs = null;
let timerStartedAt = Date.now();

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

function getFragments(index) {
  // Fragments reveal in page order, unless one sets data-order to move it in the sequence.
  const frags = Array.from(slides[index]?.querySelectorAll('.fragment') || []);
  const rank = (frag, i) => (frag.dataset.order !== undefined ? Number(frag.dataset.order) : i);
  return frags.map((frag, i) => [rank(frag, i), i, frag]).sort((a, b) => a[0] - b[0] || a[1] - b[1]).map((x) => x[2]);
}

function applyFragmentState(fragments, step) {
  fragments.forEach((frag, i) => {
    const revealClass = frag.dataset.revealClass || 'visible';
    frag.classList.toggle(revealClass, i < step);
  });
}

function renderFragments(slideIndex, step) {
  applyFragmentState(getFragments(slideIndex), step);
}

function exportFragmentStep(slideIndex) {
  if (!isExport || Number.isNaN(exportStep)) return currentStep;
  return clamp(exportStep, 0, getFragments(slideIndex).length);
}

function readStoredState() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
  } catch {
    return {};
  }
}

function statePayload() {
  return { index: currentIndex, step: currentStep, source: CLIENT_ID, updatedAt: Date.now() };
}

function writeStoredState() {
  const payload = statePayload();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  syncChannel?.postMessage(payload);
}

function mediaKey(media) {
  return media.currentSrc || media.getAttribute("src") || media.dataset.mediaId || "";
}

function mediaPayload(media, paused) {
  return {
    type: "media",
    key: mediaKey(media),
    paused,
    currentTime: media.currentTime,
    source: CLIENT_ID,
    updatedAt: Date.now()
  };
}

function applyRemoteMediaState(state) {
  if (!state || state.type !== "media" || state.source === CLIENT_ID || !state.key) return;

  document.querySelectorAll("[data-click-play]").forEach((media) => {
    if (mediaKey(media) !== state.key) return;

    if (typeof state.currentTime === "number" && Math.abs(media.currentTime - state.currentTime) > 0.5) {
      media.currentTime = state.currentTime;
    }

    if (state.paused) {
      media.pause();
    } else {
      media.play().catch(() => {});
    }
  });
}

function writeMediaState(media, paused) {
  const payload = mediaPayload(media, paused);
  localStorage.setItem(MEDIA_STORAGE_KEY, JSON.stringify(payload));
  syncChannel?.postMessage(payload);
}

function pauseInactiveMedia() {
  document.querySelectorAll(".slide:not(.active) [data-click-play]").forEach((media) => {
    media.pause();
  });
}

function applyRemoteState(state) {
  if (state?.type === "media") {
    applyRemoteMediaState(state);
    return;
  }

  if (!state || state.source === CLIENT_ID || typeof state.index !== "number") return;

  const nextIndex = clamp(state.index, 0, slides.length - 1);
  const nextStep = clamp(typeof state.step === "number" ? state.step : 0, 0, getFragments(nextIndex).length);

  if (nextIndex !== currentIndex) {
    currentStep = nextStep;
    render(nextIndex, { skipHash: isPresenter, skipStorage: true });
  } else if (nextStep !== currentStep) {
    currentStep = nextStep;
    renderFragments(currentIndex, currentStep);
    updatePresenter(currentIndex);
  }
}

function updateNotes(index) {
  const notes = slides[index]?.querySelector(".notes");
  if (notesBody) notesBody.innerHTML = notes ? notes.innerHTML : "No speaker notes for this slide.";
}

function cloneSlide(index) {
  if (index < 0 || index >= slides.length) return null;
  const clone = slides[index].cloneNode(true);
  clone.classList.add("active");
  clone.removeAttribute("aria-hidden");
  const cloneFrags = Array.from(clone.querySelectorAll(".fragment"));
  const order = getFragments(index).map((frag) => Array.from(slides[index].querySelectorAll(".fragment")).indexOf(frag));
  applyFragmentState(order.map((i) => cloneFrags[i]), index === currentIndex ? currentStep : 0);
  return clone;
}

function updatePresenterScale() {
  if (!presenterRefs?.currentHost) return;
  const slide = presenterRefs.currentHost.querySelector(".slide");
  if (!slide) return;

  const hostRect = presenterRefs.currentHost.getBoundingClientRect();
  const scale = Math.min(hostRect.width / 1600, hostRect.height / 900);
  presenterRefs.currentHost.style.setProperty("--presenter-slide-scale", scale);
}

function formatDuration(ms) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return [hours, minutes, seconds].map((part, idx) => (idx === 0 ? String(part).padStart(2, "0") : String(part).padStart(2, "0"))).join(":");
}

function updatePresenter(index) {
  if (!presenterRefs) return;

  presenterRefs.currentHost.innerHTML = "";

  const currentSlide = cloneSlide(index);

  if (currentSlide) presenterRefs.currentHost.appendChild(currentSlide);
  updatePresenterScale();

  const notes = slides[index]?.querySelector(".notes");
  presenterRefs.notes.innerHTML = notes ? notes.innerHTML : "<p>No speaker notes for this slide.</p>";
  presenterRefs.currentLabel.textContent = slides[index]?.dataset.title || `Slide ${index + 1}`;
  presenterRefs.page.textContent = `${index + 1} / ${slides.length}`;
}

function render(index, options = {}) {
  currentIndex = clamp(index, 0, slides.length - 1);

  if (!isPresenter) {
    slides.forEach((slide, slideIndex) => {
      slide.classList.toggle("active", slideIndex === currentIndex);
      slide.setAttribute("aria-hidden", slideIndex === currentIndex ? "false" : "true");
    });

    if (counter) counter.textContent = `${currentIndex + 1} / ${slides.length}`;
    updateNotes(currentIndex);
    pauseInactiveMedia();

    if (!options.skipHash) {
      window.location.hash = `slide-${currentIndex + 1}`;
    }
  } else {
    updatePresenter(currentIndex);
  }

  if (!options.skipStorage && !isExport) writeStoredState();
  renderFragments(currentIndex, exportFragmentStep(currentIndex));
}

function fromHash() {
  const match = window.location.hash.match(/slide-(\d+)/);
  const stored = readStoredState();

  if (match) {
    const index = Number.parseInt(match[1], 10) - 1;
    if (isExport) currentStep = exportFragmentStep(index);
    render(index, { skipHash: true, skipStorage: true });
  } else if (typeof stored.index === "number") {
    currentStep = clamp(typeof stored.step === "number" ? stored.step : 0, 0, getFragments(stored.index).length);
    render(stored.index, { skipHash: true, skipStorage: true });
  } else {
    render(0, { skipHash: true, skipStorage: true });
  }
}

function toggleNotes() {
  if (!isPresenter) document.body.classList.toggle("notes-visible");
}

function updateDeckScale() {
  if (isPresenter || isExport || !deck || !deckViewport || document.body.classList.contains("overview")) return;

  const viewportRect = deckViewport.getBoundingClientRect();
  const baseWidth = 1600;
  const baseHeight = 900;
  const scale = Math.min(viewportRect.width / baseWidth, viewportRect.height / baseHeight);

  deck.style.setProperty("--deck-scale", String(scale));
}

function toggleOverview() {
  if (!isPresenter) {
    document.body.classList.toggle("overview");
    updateDeckScale();
  }
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen?.();
  } else {
    document.exitFullscreen?.();
  }
}

function presenterUrl() {
  const url = new URL(window.location.href);
  url.searchParams.set("view", "presenter");
  return url.toString();
}

function openPresenterView() {
  const width = Math.max(Math.floor(window.innerWidth * 0.85), 1100);
  const height = Math.max(Math.floor(window.innerHeight * 0.85), 700);
  window.open(presenterUrl(), "perc_conference_presenter", `width=${width},height=${height},menubar=no,toolbar=no`);
}

function setupPresenter() {
  document.body.classList.add("presenter-mode");

  const shell = document.createElement("div");
  shell.className = "presenter-shell";
  shell.innerHTML = `
    <div class="presenter-main">
      <div class="presenter-panel">
        <div class="presenter-toolbar">
          <div>
            <div class="presenter-panel-header">Current Slide</div>
            <div class="presenter-panel-title" id="presenter-current-label"></div>
          </div>
          <div class="presenter-toolbar-meta">
            <div class="presenter-page" id="presenter-page">1 / ${slides.length}</div>
            <button class="presenter-timer" id="presenter-timer" type="button">00:00:00</button>
          </div>
        </div>
        <div class="presenter-slide-host" id="presenter-current"></div>
      </div>
      <div class="presenter-notes">
        <div class="presenter-panel-header">Speaker Notes</div>
        <div class="presenter-notes-body" id="presenter-notes"></div>
      </div>
    </div>
  `;

  document.body.appendChild(shell);

  presenterRefs = {
    currentHost: document.getElementById("presenter-current"),
    currentLabel: document.getElementById("presenter-current-label"),
    notes: document.getElementById("presenter-notes"),
    page: document.getElementById("presenter-page"),
    timer: document.getElementById("presenter-timer")
  };

  window.addEventListener("resize", updatePresenterScale);
  new ResizeObserver(updatePresenterScale).observe(presenterRefs.currentHost);

  presenterRefs.timer.addEventListener("click", () => {
    timerStartedAt = Date.now();
  });

  setInterval(() => {
    if (presenterRefs?.timer) presenterRefs.timer.textContent = formatDuration(Date.now() - timerStartedAt);
  }, 500);
}

document.addEventListener("keydown", (event) => {
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;

  switch (event.key) {
    case "ArrowRight":
    case "ArrowDown":
    case "PageDown":
    case " ": {
      event.preventDefault();
      const forwardFragments = getFragments(currentIndex);
      if (currentStep < forwardFragments.length) {
        currentStep++;
        renderFragments(currentIndex, currentStep);
        updatePresenter(currentIndex);
        writeStoredState();
      } else {
        currentStep = 0;
        // Past the last slide, loop back to the start.
        render(currentIndex === slides.length - 1 ? 0 : currentIndex + 1);
      }
      break;
    }
    case "ArrowLeft":
    case "ArrowUp":
    case "PageUp": {
      event.preventDefault();
      if (currentStep > 0) {
        currentStep--;
        renderFragments(currentIndex, currentStep);
        updatePresenter(currentIndex);
        writeStoredState();
      } else {
        const prevIndex = clamp(currentIndex - 1, 0, slides.length - 1);
        currentStep = getFragments(prevIndex).length;
        render(currentIndex - 1);
      }
      break;
    }
    case "Home":
      event.preventDefault();
      currentStep = 0;
      render(0);
      break;
    case "End":
      event.preventDefault();
      currentStep = 0;
      render(slides.length - 1);
      break;
    case "n":
    case "N":
      event.preventDefault();
      toggleNotes();
      break;
    case "o":
    case "O":
      event.preventDefault();
      toggleOverview();
      break;
    case "f":
    case "F":
      event.preventDefault();
      toggleFullscreen();
      break;
    case "p":
    case "P":
      if (!isPresenter) {
        event.preventDefault();
        openPresenterView();
      }
      break;
    case "Escape":
      if (document.body.classList.contains("overview")) {
        document.body.classList.remove("overview");
        updateDeckScale();
      }
      break;
    default:
      break;
  }
});

slides.forEach((slide, index) => {
  slide.addEventListener("click", () => {
    if (document.body.classList.contains("overview")) {
      document.body.classList.remove("overview");
      updateDeckScale();
      currentStep = 0;
      render(index);
    }
  });
});

document.addEventListener("click", (event) => {
  const media = event.target.closest?.("[data-click-play]");
  if (!media) return;

  event.stopPropagation();
  if (media.paused) {
    media.play().catch(() => {});
    writeMediaState(media, false);
  } else {
    media.pause();
    writeMediaState(media, true);
  }
});

window.addEventListener("storage", (event) => {
  if (![STORAGE_KEY, MEDIA_STORAGE_KEY].includes(event.key) || !event.newValue) return;
  try {
    applyRemoteState(JSON.parse(event.newValue));
  } catch {
    // ignore malformed state
  }
});

syncChannel?.addEventListener("message", (event) => {
  applyRemoteState(event.data);
});

// Draw-on animation for the time series: a clip rectangle widens from left to right
// whenever its figure is revealed. (Animating stroke dashes breaks lines into pieces in Safari.)
document.querySelectorAll(".trace-reveal").forEach((figure, n) => {
  const svgEl = figure.querySelector("svg");
  const traces = figure.querySelectorAll(".trace");
  if (!svgEl || !traces.length) return;

  // Clip to the horizontal extent of the traces so the highlight timings line up.
  // Measured on reveal, because hidden slides report zero-size boxes.
  const vb = svgEl.viewBox.baseVal;
  const box = { x: vb.x, y: vb.y, width: vb.width, height: vb.height };
  const measure = () => {
    const boxes = Array.from(traces, (path) => path.getBBox()).filter((b) => b.width > 0);
    if (!boxes.length) return;
    const left = Math.min(...boxes.map((b) => b.x));
    const right = Math.max(...boxes.map((b) => b.x + b.width));
    box.x = left - 2;
    box.width = right - left + 4;
    rect.setAttribute("x", box.x);
  };
  const ns = "http://www.w3.org/2000/svg";
  const clip = document.createElementNS(ns, "clipPath");
  clip.id = `trace-clip-${n}`;
  const rect = document.createElementNS(ns, "rect");
  rect.setAttribute("x", box.x);
  rect.setAttribute("y", box.y);
  rect.setAttribute("height", box.height);
  rect.setAttribute("width", 0);
  clip.appendChild(rect);
  svgEl.prepend(clip);
  traces.forEach((path) => path.setAttribute("clip-path", `url(#${clip.id})`));

  let frame = null;
  const draw = () => {
    cancelAnimationFrame(frame);
    measure();
    const duration = (parseFloat(getComputedStyle(figure).getPropertyValue("--trace-duration")) || 5) * 1000;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const start = performance.now();
    const step = (now) => {
      const t = reduced ? 1 : Math.min((now - start) / duration, 1);
      rect.setAttribute("width", box.width * t);
      if (t < 1) frame = requestAnimationFrame(step);
    };
    frame = requestAnimationFrame(step);
  };
  const reset = () => {
    cancelAnimationFrame(frame);
    rect.setAttribute("width", 0);
  };

  let shown = figure.classList.contains("visible");
  if (shown) draw();
  new MutationObserver(() => {
    const now = figure.classList.contains("visible");
    if (now === shown) return;
    shown = now;
    if (now) draw();
    else reset();
  }).observe(figure, { attributes: true, attributeFilter: ["class"] });
});

if (isExport) document.body.classList.add("export-mode");
if (isPresenter) setupPresenter();

window.addEventListener("hashchange", () => {
  if (!isPresenter) fromHash();
});

window.addEventListener("resize", updateDeckScale);

fromHash();
updateDeckScale();

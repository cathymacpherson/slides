const slides = Array.from(document.querySelectorAll(".slide"));
const counter = document.getElementById("deck-counter");
const notesBody = document.getElementById("notes-body");
const deck = document.getElementById("deck");
const deckViewport = document.querySelector(".deck-viewport");
const params = new URLSearchParams(window.location.search);
const isPresenter = params.get("view") === "presenter";
const STORAGE_KEY = "mq_colloquium_slide_state";

let currentIndex = 0;
let currentStep = 0;
let presenterRefs = null;
let timerStartedAt = Date.now();

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

function getFragments(index) {
  return Array.from(slides[index]?.querySelectorAll('.fragment') || []);
}

function renderFragments(slideIndex, step) {
  const fragments = getFragments(slideIndex);
  fragments.forEach((frag, i) => {
    const revealClass = frag.dataset.revealClass || 'visible';
    frag.classList.toggle(revealClass, i < step);
  });
}

function readStoredState() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
  } catch {
    return {};
  }
}

function writeStoredState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ index: currentIndex, updatedAt: Date.now() }));
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
  return clone;
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
  presenterRefs.nextHost.innerHTML = "";

  const currentSlide = cloneSlide(index);
  const nextSlide = cloneSlide(Math.min(index + 1, slides.length - 1));

  if (currentSlide) presenterRefs.currentHost.appendChild(currentSlide);
  if (nextSlide) presenterRefs.nextHost.appendChild(nextSlide);

  const notes = slides[index]?.querySelector(".notes");
  presenterRefs.notes.innerHTML = notes ? notes.innerHTML : "<p>No speaker notes for this slide.</p>";
  presenterRefs.currentLabel.textContent = slides[index]?.dataset.title || `Slide ${index + 1}`;
  presenterRefs.nextLabel.textContent = slides[index + 1]?.dataset.title || "End of deck";
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

    if (!options.skipHash) {
      window.location.hash = `slide-${currentIndex + 1}`;
    }
  } else {
    updatePresenter(currentIndex);
  }

  if (!options.skipStorage) writeStoredState();
  renderFragments(currentIndex, currentStep);
}

function fromHash() {
  const match = window.location.hash.match(/slide-(\d+)/);
  const stored = readStoredState();

  if (match) {
    render(Number.parseInt(match[1], 10) - 1, { skipHash: true, skipStorage: true });
  } else if (typeof stored.index === "number") {
    render(stored.index, { skipHash: true, skipStorage: true });
  } else {
    render(0, { skipHash: true, skipStorage: true });
  }
}

function toggleNotes() {
  if (!isPresenter) document.body.classList.toggle("notes-visible");
}

function updateDeckScale() {
  if (isPresenter || !deck || !deckViewport || document.body.classList.contains("overview")) return;

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
  window.open(presenterUrl(), "mq_colloquium_presenter", `width=${width},height=${height},menubar=no,toolbar=no`);
}

function setupPresenter() {
  document.body.classList.add("presenter-mode");

  const shell = document.createElement("div");
  shell.className = "presenter-shell";
  shell.innerHTML = `
    <div class="presenter-main">
      <div class="presenter-stage">
        <div class="presenter-panel">
          <div class="presenter-panel-header">Current Slide</div>
          <div class="presenter-panel-title" id="presenter-current-label"></div>
          <div class="presenter-slide-host" id="presenter-current"></div>
        </div>
        <div class="presenter-panel">
          <div class="presenter-panel-header">Next Slide</div>
          <div class="presenter-panel-title" id="presenter-next-label"></div>
          <div class="presenter-slide-host presenter-next-host" id="presenter-next"></div>
        </div>
      </div>
      <aside class="presenter-sidebar">
        <div class="presenter-meta">
          <div class="presenter-meta-card">
            <div class="presenter-panel-header">Slide</div>
            <div class="presenter-page" id="presenter-page">1 / ${slides.length}</div>
          </div>
          <div class="presenter-meta-card">
            <div class="presenter-panel-header">Timer</div>
            <button class="presenter-timer" id="presenter-timer" type="button">00:00:00</button>
          </div>
        </div>
        <div class="presenter-notes">
          <div class="presenter-panel-header">Speaker Notes</div>
          <div class="presenter-notes-body" id="presenter-notes"></div>
        </div>
      </aside>
    </div>
  `;

  document.body.appendChild(shell);

  presenterRefs = {
    currentHost: document.getElementById("presenter-current"),
    nextHost: document.getElementById("presenter-next"),
    currentLabel: document.getElementById("presenter-current-label"),
    nextLabel: document.getElementById("presenter-next-label"),
    notes: document.getElementById("presenter-notes"),
    page: document.getElementById("presenter-page"),
    timer: document.getElementById("presenter-timer")
  };

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
      } else {
        currentStep = 0;
        render(currentIndex + 1);
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

window.addEventListener("storage", (event) => {
  if (event.key !== STORAGE_KEY || !event.newValue) return;
  try {
    const state = JSON.parse(event.newValue);
    if (typeof state.index === "number" && state.index !== currentIndex) {
      render(state.index, { skipHash: isPresenter, skipStorage: true });
    }
  } catch {
    // ignore malformed state
  }
});

if (isPresenter) setupPresenter();

window.addEventListener("hashchange", () => {
  if (!isPresenter) fromHash();
});

window.addEventListener("resize", updateDeckScale);

fromHash();
updateDeckScale();

const state = {
  articles: [],
  flashcards: [],
  journal: "",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

async function api(path, payload) {
  const response = await fetch(new URL(path, window.location.origin).toString(), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  let data;
  try {
    data = await response.json();
  } catch {
    data = { message: "Le serveur a renvoyé une réponse illisible. Recharge l'app puis réessaie." };
  }
  if (!response.ok) throw new Error(data.message || "Erreur inconnue");
  return data;
}

async function loadConfig() {
  const response = await fetch("/api/config");
  const data = await response.json();
  $("#disclaimer").textContent = data.disclaimer;
}

function setStatus(message, kind = "neutral") {
  const status = $("#status");
  status.textContent = message;
  status.style.color = kind === "error" ? "#b91c1c" : kind === "ok" ? "#0f7b5c" : "#627174";
}

function renderArticles() {
  const container = $("#articlesList");
  container.className = "article-list";
  container.innerHTML = state.articles
    .map(
      (article) => `
      <article class="article">
        <h2>${escapeHtml(article.title)}</h2>
        <p class="meta">${escapeHtml(article.topic)} · ${escapeHtml(article.journal || "Revue non renseignée")} · ${escapeHtml(article.date || "Date non renseignée")}</p>
        <p><strong>Résumé :</strong> ${escapeHtml(article.summary || "Résumé non disponible.")}</p>
        <p><strong>Pourquoi c'est important :</strong> ${escapeHtml(article.importance || "")}</p>
        <details>
          <summary>Lire l'explication développée</summary>
          <p>${escapeHtml(article.explanation || "")}</p>
          <p><strong>Niveau de preuve :</strong> ${escapeHtml(article.evidence || "")}</p>
          <p><strong>Limites :</strong> ${escapeHtml(article.limits || "")}</p>
          <p><strong>Résumé PubMed traduit :</strong> ${escapeHtml(article.abstract_fr || "Non disponible.")}</p>
          <p><a href="${article.link}" target="_blank" rel="noreferrer">Ouvrir PubMed</a></p>
        </details>
      </article>
      `
    )
    .join("");
}

function renderJournal() {
  $("#journalText").textContent = state.journal || "Le journal quotidien apparaîtra ici.";
}

function renderFlashcards() {
  const container = $("#flashcards");
  container.className = "card-grid";
  container.innerHTML = state.flashcards
    .map(
      (card, index) => `
      <button class="flip-card" type="button" aria-label="Carte ${index + 1}">
        <span class="flip-inner">
          <span class="face front">
            <span class="card-label">Carte ${index + 1}</span>
            <span class="card-text">${escapeHtml(card.question)}</span>
          </span>
          <span class="face back">
            <span class="card-label">Réponse</span>
            <span class="card-text">${escapeHtml(card.answer)}</span>
          </span>
        </span>
      </button>
      `
    )
    .join("");

  $$(".flip-card").forEach((card) => {
    card.addEventListener("click", () => card.classList.toggle("flipped"));
  });
}

function switchView(view) {
  $$(".tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.view === view));
  $$(".view").forEach((section) => section.classList.toggle("active", section.id === view));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function runWatch() {
  setStatus("Génération en cours : PubMed, traduction, journal, cartes...", "neutral");
  $("#runWatch").disabled = true;
  try {
    const data = await api("/api/watch", {
      topics: ["immunology", "oncology", "neuroscience", "pharmacology", "microbiology", "genetics", "public health"],
      articles_per_topic: Number($("#articleCount").value),
      days_back: Number($("#daysBack").value),
      ntfy_topic: $("#ntfyTopic").value.trim(),
      auto_notify: $("#autoNotify").checked,
    });
    if (data.ok === false) throw new Error(data.message || "La veille n'a pas pu être générée.");
    state.articles = data.articles;
    state.flashcards = data.flashcards;
    state.journal = data.journal_markdown;
    renderArticles();
    renderJournal();
    renderFlashcards();
    setStatus(`Veille prête. Notification ntfy : ${data.notification_status}.`, "ok");
    switchView("articles");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    $("#runWatch").disabled = false;
  }
}

async function sendNotification() {
  try {
    const data = await api("/api/notify", { ntfy_topic: $("#ntfyTopic").value.trim() });
    setStatus(data.message, "ok");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function testNotification() {
  try {
    const data = await api("/api/test-notify", { ntfy_topic: $("#ntfyTopic").value.trim() });
    setStatus(data.message, "ok");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function askQuestion() {
  try {
    const data = await api("/api/ask", { question: $("#question").value });
    $("#answer").textContent = data.answer;
  } catch (error) {
    $("#answer").textContent = error.message;
  }
}

function previewImage() {
  const file = $("#imageInput").files[0];
  const preview = $("#imagePreview");
  if (!file) {
    preview.hidden = true;
    return;
  }
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
}

function wireEvents() {
  $$(".tab").forEach((tab) => tab.addEventListener("click", () => switchView(tab.dataset.view)));
  $("#runWatch").addEventListener("click", runWatch);
  $("#sendNotify").addEventListener("click", sendNotification);
  $("#testNotify").addEventListener("click", testNotification);
  $("#askButton").addEventListener("click", askQuestion);
  $("#imageInput").addEventListener("change", previewImage);
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

loadConfig();
wireEvents();

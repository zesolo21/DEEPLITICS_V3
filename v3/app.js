(() => {
  "use strict";

  const TOPICS = [
    ["security", "Sicherheit"], ["diplomacy", "Diplomatie"], ["trade", "Wirtschaft"],
    ["rights", "Rechte & Migration"], ["conflict", "Konflikt"], ["surveillance", "Überwachung"]
  ];
  const TENANT_KEY = "deeplitics:tenant";
  const AUTH_TX_KEY = "deeplitics:oidc-transaction";
  const state = {
    config: null,
    stories: [],
    token: null,
    workspace: null,
    preferences: { saved_story_ids: [], topics: [] },
    activeTopics: new Set(TOPICS.map(([id]) => id)),
    search: "",
    savedOnly: false,
    noticeTimer: null
  };

  const $ = (selector, root = document) => root.querySelector(selector);
  const storyDialog = $("#story-dialog");
  const authDialog = $("#auth-dialog");

  function make(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined && text !== null) {
      element.textContent = String(text).replace(/\[\[([^\]]+)\]\]/g, "$1");
    }
    return element;
  }

  function showNotice(message) {
    const notice = $("#notice");
    notice.textContent = message;
    notice.hidden = false;
    window.clearTimeout(state.noticeTimer);
    state.noticeTimer = window.setTimeout(() => { notice.hidden = true; }, 3400);
  }

  function topicName(id) {
    return TOPICS.find(([key]) => key === id)?.[1] || "Weitere Themen";
  }

  function validTenantId(value) {
    return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
  }

  function currentTenant() {
    return sessionStorage.getItem(TENANT_KEY) || state.config?.default_tenant_id || "";
  }

  function renderTopics() {
    const nav = $("#topic-filters");
    nav.replaceChildren();
    const all = make("button", "topic-chip", "Alle Themen");
    all.type = "button";
    all.dataset.topic = "all";
    all.setAttribute("aria-pressed", String(state.activeTopics.size === TOPICS.length));
    nav.append(all);
    for (const [id, label] of TOPICS) {
      const button = make("button", "topic-chip", label);
      button.type = "button";
      button.dataset.topic = id;
      button.setAttribute("aria-pressed", String(state.activeTopics.has(id) && state.activeTopics.size < TOPICS.length));
      nav.append(button);
    }
  }

  function safeImageUrl(raw) {
    if (typeof raw !== "string") return "";
    try {
      const url = new URL(raw, window.location.origin);
      return url.protocol === "https:" ? url.href : "";
    } catch (_error) { return ""; }
  }

  function addImage(container, raw, alt, className) {
    const src = safeImageUrl(raw);
    if (!src) return;
    const image = make("img", className);
    image.src = src;
    image.alt = alt || "";
    image.loading = "lazy";
    image.referrerPolicy = "no-referrer";
    image.addEventListener("error", () => image.remove(), { once: true });
    container.append(image);
  }

  function storyMatches(story) {
    if (state.savedOnly && !state.preferences.saved_story_ids.includes(String(story.id))) return false;
    if (state.activeTopics.size < TOPICS.length && !state.activeTopics.has(story.theme_category)) return false;
    const query = state.search.trim().toLocaleLowerCase("de");
    if (!query) return true;
    const searchable = [story.title, story.one_line, story.theme_category,
      ...(Array.isArray(story.entities) ? story.entities.map(entity => entity.name) : [])]
      .filter(Boolean).join(" ").toLocaleLowerCase("de");
    return searchable.includes(query);
  }

  function renderStories() {
    const grid = $("#story-list");
    const filtered = state.stories.filter(storyMatches);
    grid.replaceChildren();
    $("#empty-state").hidden = filtered.length > 0;
    $("#story-total").textContent = `${filtered.length} Story${filtered.length === 1 ? "" : "s"}`;
    for (const story of filtered) grid.append(createStoryCard(story));
    $("#saved-count").textContent = String(state.preferences.saved_story_ids.length);
    $("#saved-open").setAttribute("aria-pressed", String(state.savedOnly));
  }

  function createStoryCard(story) {
    const card = make("article", `story-card cat-${story.theme_category || "other"}`);
    const imageButton = make("button", "card-image");
    imageButton.type = "button";
    imageButton.dataset.openStory = String(story.id);
    imageButton.setAttribute("aria-label", `Story öffnen: ${story.title || "Ohne Titel"}`);
    addImage(imageButton, story.image_url, "", "");
    imageButton.append(make("span", "category-tag", topicName(story.theme_category)));
    card.append(imageButton);

    const content = make("div", "card-content");
    const topline = make("div", "card-topline");
    topline.append(make("span", "card-date", story.generated_at ? formatDate(story.generated_at) : "Hintergrund & Analyse"));
    content.append(topline);

    const titleButton = make("button", "card-title-button");
    titleButton.type = "button";
    titleButton.dataset.openStory = String(story.id);
    titleButton.append(make("h2", "", story.title || "Ohne Titel"));
    content.append(titleButton);
    content.append(make("p", "card-summary", story.one_line || ""));

    const footer = make("div", "card-footer");
    const sourceCount = Array.isArray(story.article_urls) ? story.article_urls.length : 0;
    footer.append(make("span", "source-count", `${sourceCount} ${sourceCount === 1 ? "Quelle" : "Quellen"}`));
    const save = make("button", "save-button");
    save.type = "button";
    save.dataset.saveStory = String(story.id);
    const isSaved = state.preferences.saved_story_ids.includes(String(story.id));
    save.setAttribute("aria-pressed", String(isSaved));
    save.setAttribute("aria-label", isSaved ? "Story aus Gespeichert entfernen" : "Story speichern");
    save.append(make("span", "save-icon", isSaved ? "▰" : "▱"), make("span", "", isSaved ? "Gespeichert" : "Speichern"));
    footer.append(save);
    content.append(footer);
    card.append(content);
    return card;
  }

  function formatDate(raw) {
    const date = new Date(raw);
    if (Number.isNaN(date.getTime())) return "Hintergrund & Analyse";
    return new Intl.DateTimeFormat("de-DE", { day: "numeric", month: "short", year: "numeric" }).format(date);
  }

  function addSection(parent, title) {
    const section = make("section", "detail-section");
    section.append(make("h3", "", title));
    parent.append(section);
    return section;
  }

  function safeExternalLink(raw) {
    if (typeof raw !== "string") return "";
    try {
      const url = new URL(raw);
      return url.protocol === "https:" ? url.href : "";
    } catch (_error) { return ""; }
  }

  function openStory(storyId) {
    const story = state.stories.find(item => String(item.id) === String(storyId));
    if (!story) return;
    const detail = $("#story-detail");
    detail.replaceChildren();
    const hero = make("header", "detail-hero");
    addImage(hero, story.image_url, "", "");
    const heroContent = make("div", "detail-hero-content");
    heroContent.append(make("span", "category-tag", topicName(story.theme_category)));
    heroContent.append(make("h2", "", story.title || "Ohne Titel"));
    hero.append(heroContent);
    detail.append(hero);

    const body = make("div", "detail-body");
    body.append(make("p", "detail-lead", story.one_line || ""));
    const actions = make("div", "detail-actions");
    const save = make("button", "save-button");
    save.type = "button";
    save.dataset.saveStory = String(story.id);
    const saved = state.preferences.saved_story_ids.includes(String(story.id));
    save.setAttribute("aria-pressed", String(saved));
    save.append(make("span", "save-icon", saved ? "▰" : "▱"), make("span", "", saved ? "Gespeichert" : "Story speichern"));
    actions.append(save);
    body.append(actions);

    if (Array.isArray(story.summary) && story.summary.length) {
      const section = addSection(body, "Das Wichtigste");
      const list = make("ul", "summary-list");
      for (const point of story.summary) list.append(make("li", "", point));
      section.append(list);
    }
    if (story.deep_dive) {
      const section = addSection(body, "Der größere Zusammenhang");
      section.append(make("p", "", story.deep_dive));
    }

    for (const thread of Array.isArray(story.historical_threads) ? story.historical_threads : []) {
      const section = addSection(body, thread.title || "Historische Linie");
      const timeline = make("div", "timeline");
      for (const entry of Array.isArray(thread.entries) ? thread.entries : []) {
        const item = make("article", "timeline-item");
        item.append(make("span", "timeline-date", entry.date || ""));
        item.append(make("h4", "", entry.title || ""));
        item.append(make("p", "", entry.one_line || entry.extended || ""));
        timeline.append(item);
      }
      section.append(timeline);
    }

    if (Array.isArray(story.quotes) && story.quotes.length) {
      const section = addSection(body, "Zitate");
      for (const quote of story.quotes) {
        const block = make("figure", "quote");
        block.append(make("blockquote", "", `„${quote.text || ""}”`));
        block.append(make("figcaption", "quote-caption", ""));
        const caption = $("figcaption", block);
        caption.append(make("cite", "", quote.attribution || "Unbekannte Quelle"));
        if (quote.context) caption.append(make("span", "", ` · ${quote.context}`));
        section.append(block);
      }
    }

    const sources = [];
    if (Array.isArray(story.article_urls)) sources.push(...story.article_urls.map(url => ({ url, label: "Berichterstattung" })));
    if (Array.isArray(story.primary_sources)) {
      sources.push(...story.primary_sources.map(item => ({ url: item.url, label: item.title || item.issuer || "Primärquelle" })));
    }
    if (sources.length) {
      const section = addSection(body, "Quellen");
      const list = make("div", "source-list");
      for (const source of sources) {
        const href = safeExternalLink(source.url);
        if (!href) continue;
        const link = make("a", "source-link");
        link.href = href;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.append(make("span", "", source.label), make("span", "", new URL(href).hostname.replace(/^www\./, "")));
        list.append(link);
      }
      section.append(list);
    }
    detail.append(body);
    if (!storyDialog.open) storyDialog.showModal();
  }

  function updateAccountUi() {
    const button = $("#account-open");
    const signedIn = Boolean(state.token && state.workspace);
    button.textContent = signedIn ? "Workspace" : "Anmelden";
    $("#workspace-label").textContent = signedIn ? state.workspace.name : "Öffentliche Übersicht";
    $("#signout-button").hidden = !signedIn;
    $("#clear-preferences").hidden = !signedIn;
    $("#signup-button").hidden = signedIn || !state.config?.signup_enabled;
    $("#signup-note").hidden = signedIn || !state.config?.signup_enabled;
    $("#tenant-id").value = currentTenant();
    $("#saved-open").title = signedIn ? "Gespeicherte Storys" : "Zum Speichern anmelden";
  }

  async function api(path, options = {}) {
    const headers = new Headers(options.headers || {});
    if (state.token) headers.set("Authorization", `Bearer ${state.token}`);
    const tenantId = currentTenant();
    if (tenantId) headers.set("X-Tenant-ID", tenantId);
    if (options.body) headers.set("Content-Type", "application/json");
    const response = await fetch(path, { ...options, headers, cache: "no-store", credentials: "omit" });
    if (!response.ok) {
      let message = `Anfrage fehlgeschlagen (${response.status}).`;
      try { message = (await response.json()).error || message; } catch (_error) { /* keep generic message */ }
      const error = new Error(message);
      error.status = response.status;
      throw error;
    }
    if (response.status === 204) return null;
    return response.json();
  }

  async function loadMemberData() {
    const [me, prefs] = await Promise.all([api("/api/v1/me"), api("/api/v1/me/preferences")]);
    state.workspace = me.workspace;
    state.preferences = prefs.preferences;
    state.activeTopics = new Set(state.preferences.topics.length ? state.preferences.topics : TOPICS.map(([id]) => id));
    renderTopics();
    renderStories();
    updateAccountUi();
  }

  async function persistPreferences() {
    if (!state.token) return;
    try {
      const topics = state.activeTopics.size === TOPICS.length ? [] : [...state.activeTopics];
      const response = await api("/api/v1/me/preferences", {
        method: "PUT",
        body: JSON.stringify({ ...state.preferences, topics })
      });
      state.preferences = response.preferences;
    } catch (error) {
      showNotice(error.status === 401 ? "Bitte melde dich erneut an." : "Einstellungen konnten nicht gespeichert werden.");
    }
  }

  async function toggleSaved(storyId) {
    if (!state.token) {
      $("#auth-message").textContent = "Melde dich an, um Storys in deinem Workspace zu speichern.";
      authDialog.showModal();
      return;
    }
    const saved = new Set(state.preferences.saved_story_ids);
    if (saved.has(storyId)) saved.delete(storyId);
    else saved.add(storyId);
    state.preferences.saved_story_ids = [...saved];
    renderStories();
    if (storyDialog.open) openStory(storyId);
    await persistPreferences();
    if (saved.has(storyId)) showNotice("Story in deinem Workspace gespeichert.");
  }

  async function randomToken(bytes = 32) {
    const value = crypto.getRandomValues(new Uint8Array(bytes));
    return value;
  }

  function base64Url(bytes) {
    let binary = "";
    for (const byte of bytes) binary += String.fromCharCode(byte);
    return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
  }

  async function startLogin(tenantId, createAccount = false) {
    if (!state.config?.auth_enabled) {
      $("#auth-message").textContent = "Die Anmeldung ist noch nicht konfiguriert. Öffentliche Storys bleiben verfügbar.";
      return;
    }
    if (createAccount && !state.config.signup_enabled) {
      $("#auth-message").textContent = "Die Kontoerstellung ist in dieser Umgebung deaktiviert.";
      return;
    }
    if (!validTenantId(tenantId)) {
      $("#auth-message").textContent = "Bitte gib eine gültige Workspace-ID ein.";
      return;
    }
    sessionStorage.setItem(TENANT_KEY, tenantId);
    const verifier = base64Url(await randomToken(48));
    const stateValue = base64Url(await randomToken(32));
    const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier));
    sessionStorage.setItem(AUTH_TX_KEY, JSON.stringify({
      state: stateValue, verifier, tenantId, intent: createAccount ? "signup" : "signin"
    }));

    const oidc = state.config.oidc;
    const authorization = new URL(oidc.authorization_endpoint);
    authorization.searchParams.set("response_type", "code");
    authorization.searchParams.set("client_id", oidc.client_id);
    authorization.searchParams.set("redirect_uri", oidc.redirect_uri);
    authorization.searchParams.set("scope", "openid");
    authorization.searchParams.set("state", stateValue);
    if (createAccount) authorization.searchParams.set("prompt", "create");
    authorization.searchParams.set("code_challenge", base64Url(new Uint8Array(digest)));
    authorization.searchParams.set("code_challenge_method", "S256");
    if (oidc.audience) authorization.searchParams.set("audience", oidc.audience);
    window.location.assign(authorization.href);
  }

  async function completeLogin() {
    const url = new URL(window.location.href);
    const code = url.searchParams.get("code");
    const returnedState = url.searchParams.get("state");
    const providerError = url.searchParams.get("error");
    if (!code && !providerError) return;
    const transactionText = sessionStorage.getItem(AUTH_TX_KEY);
    sessionStorage.removeItem(AUTH_TX_KEY);
    history.replaceState(null, "", "/app/");
    if (providerError) throw new Error("Die Anmeldung wurde vom Identitätsanbieter abgebrochen.");
    let transaction;
    try { transaction = JSON.parse(transactionText || "null"); } catch (_error) { transaction = null; }
    if (!transaction || !returnedState || transaction.state !== returnedState || !transaction.verifier) {
      throw new Error("Die Anmeldung konnte aus Sicherheitsgründen nicht bestätigt werden. Bitte erneut versuchen.");
    }
    sessionStorage.setItem(TENANT_KEY, transaction.tenantId);
    const body = new URLSearchParams({
      grant_type: "authorization_code",
      client_id: state.config.oidc.client_id,
      code,
      redirect_uri: state.config.oidc.redirect_uri,
      code_verifier: transaction.verifier
    });
    const response = await fetch(state.config.oidc.token_endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
      cache: "no-store",
      credentials: "omit",
      referrerPolicy: "no-referrer"
    });
    if (!response.ok) throw new Error("Der Identitätsanbieter hat die Anmeldung abgelehnt. Bitte erneut versuchen.");
    const tokenResponse = await response.json();
    if (typeof tokenResponse.access_token !== "string" || typeof tokenResponse.token_type !== "string"
        || tokenResponse.token_type.toLowerCase() !== "bearer") {
      throw new Error("Der Identitätsanbieter hat kein verwendbares Zugriffstoken zurückgegeben.");
    }
    state.token = tokenResponse.access_token;
    try {
      if (transaction.intent === "signup") {
        if (!state.config.signup_enabled) throw new Error("Die Kontoerstellung ist in dieser Umgebung deaktiviert.");
        await api("/api/v1/staging-signup", { method: "POST" });
      }
      await loadMemberData();
    } catch (error) {
      state.token = null;
      state.workspace = null;
      throw error;
    }
    authDialog.close();
    showNotice("Du bist mit deinem Workspace verbunden.");
  }

  async function loadPublicData() {
    const [configResponse, storyResponse] = await Promise.all([
      fetch("/api/v1/public-config", { cache: "no-store", credentials: "omit" }),
      fetch("/api/v1/stories", { cache: "default", credentials: "omit" })
    ]);
    if (!configResponse.ok || !storyResponse.ok) throw new Error("Deeplitics konnte die Übersicht gerade nicht laden.");
    state.config = await configResponse.json();
    try {
      const redirect = new URL(state.config.oidc?.redirect_uri);
      if (redirect.origin !== window.location.origin || redirect.pathname !== window.location.pathname ||
          redirect.username || redirect.password || redirect.search || redirect.hash) {
        state.config.auth_enabled = false;
        state.config.signup_enabled = false;
      }
    } catch (_error) {
      state.config.auth_enabled = false;
      state.config.signup_enabled = false;
    }
    const payload = await storyResponse.json();
    state.stories = Array.isArray(payload.stories) ? payload.stories : [];
    if (state.config.default_tenant_id && !sessionStorage.getItem(TENANT_KEY)) {
      sessionStorage.setItem(TENANT_KEY, state.config.default_tenant_id);
    }
    const tenantFromInvite = new URLSearchParams(window.location.search).get("tenant");
    if (tenantFromInvite && validTenantId(tenantFromInvite)) sessionStorage.setItem(TENANT_KEY, tenantFromInvite);
    const latest = state.stories.map(story => new Date(story.generated_at)).filter(date => !Number.isNaN(date.getTime())).sort((a, b) => b - a)[0];
    if (latest) $("#feed-updated").textContent = `Stand ${formatDate(latest.toISOString())}`;
  }

  function signOut() {
    state.token = null;
    state.workspace = null;
    state.preferences = { saved_story_ids: [], topics: [] };
    state.activeTopics = new Set(TOPICS.map(([id]) => id));
    state.savedOnly = false;
    renderTopics();
    renderStories();
    updateAccountUi();
    authDialog.close();
    showNotice("Die lokale Sitzung wurde beendet. Das Identitätskonto kann separat abgemeldet werden.");
  }

  async function clearPreferences() {
    if (!state.token || !window.confirm("Gespeicherte Storys und Themenfilter dauerhaft aus deinem Workspace löschen?")) return;
    try {
      await api("/api/v1/me/preferences", { method: "DELETE" });
      state.preferences = { saved_story_ids: [], topics: [] };
      state.activeTopics = new Set(TOPICS.map(([id]) => id));
      state.savedOnly = false;
      renderTopics();
      renderStories();
      authDialog.close();
      showNotice("Deine gespeicherten Einstellungen wurden gelöscht.");
    } catch (_error) {
      $("#auth-message").textContent = "Die Einstellungen konnten nicht gelöscht werden. Bitte erneut versuchen.";
    }
  }

  function bindEvents() {
    $("#topic-filters").addEventListener("click", event => {
      const button = event.target.closest("button[data-topic]");
      if (!button) return;
      const topic = button.dataset.topic;
      if (topic === "all") state.activeTopics = new Set(TOPICS.map(([id]) => id));
      else {
        if (state.activeTopics.size === TOPICS.length) state.activeTopics = new Set([topic]);
        else if (state.activeTopics.has(topic)) state.activeTopics.delete(topic);
        else state.activeTopics.add(topic);
        if (state.activeTopics.size === 0) state.activeTopics = new Set(TOPICS.map(([id]) => id));
      }
      renderTopics();
      renderStories();
      window.clearTimeout(state.preferenceTimer);
      state.preferenceTimer = window.setTimeout(persistPreferences, 300);
    });

    $("#search").addEventListener("input", event => {
      state.search = event.target.value;
      renderStories();
    });
    $("#story-list").addEventListener("click", event => {
      const save = event.target.closest("[data-save-story]");
      if (save) { toggleSaved(save.dataset.saveStory); return; }
      const open = event.target.closest("[data-open-story]");
      if (open) openStory(open.dataset.openStory);
    });
    $("#story-detail").addEventListener("click", event => {
      const save = event.target.closest("[data-save-story]");
      if (save) toggleSaved(save.dataset.saveStory);
    });
    $("#saved-open").addEventListener("click", () => {
      if (!state.token) { authDialog.showModal(); return; }
      state.savedOnly = !state.savedOnly;
      renderStories();
      if (state.savedOnly) window.scrollTo({ top: $("#story-list").offsetTop - 20, behavior: "smooth" });
    });
    $("#account-open").addEventListener("click", () => {
      $("#auth-message").textContent = state.token ? `Verbunden mit ${state.workspace.name}.` : "";
      authDialog.showModal();
    });
    $("#tenant-form").addEventListener("submit", event => {
      event.preventDefault();
      const tenantId = $("#tenant-id").value.trim();
      if (!validTenantId(tenantId)) {
        $("#auth-message").textContent = "Bitte gib eine gültige Workspace-ID ein.";
        return;
      }
      startLogin(tenantId).catch(error => { $("#auth-message").textContent = error.message; });
    });
    $("#signup-button").addEventListener("click", () => {
      const tenantId = $("#tenant-id").value.trim();
      if (!validTenantId(tenantId)) {
        $("#auth-message").textContent = "Bitte gib eine gültige Workspace-ID ein.";
        return;
      }
      startLogin(tenantId, true).catch(error => { $("#auth-message").textContent = error.message; });
    });
    $("#signout-button").addEventListener("click", signOut);
    $("#clear-preferences").addEventListener("click", clearPreferences);
    document.addEventListener("click", event => {
      const close = event.target.closest("[data-close]");
      if (close) document.getElementById(close.dataset.close).close();
    });
    for (const dialog of [storyDialog, authDialog]) {
      dialog.addEventListener("click", event => {
        if (event.target === dialog) dialog.close();
      });
    }
    document.addEventListener("keydown", event => {
      if (event.key === "/" && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {
        event.preventDefault();
        $("#search").focus();
      }
      if (event.key === "Escape" && state.savedOnly) {
        state.savedOnly = false;
        renderStories();
      }
    });
  }

  async function init() {
    bindEvents();
    renderTopics();
    updateAccountUi();
    try {
      await loadPublicData();
      renderTopics();
      renderStories();
      await completeLogin();
      updateAccountUi();
    } catch (error) {
      showNotice(error.message);
      $("#auth-message").textContent = error.message;
      $("#story-list").replaceChildren(make("p", "loading-card", error.message));
      updateAccountUi();
    }
  }

  init();
})();

const queryApiBase = new URLSearchParams(window.location.search).get("api");
const API_BASE =
  window.__FIELDNOTE_API_BASE__ ||
  queryApiBase ||
  (window.location.port === "5173"
    ? `${window.location.protocol}//${window.location.hostname}:8080`
    : window.location.origin);
const APP_NAME = "agent";
const USER_ID_KEY = "fieldnote-user-id";

const conversation = document.querySelector("#conversation");
const form = document.querySelector("#message-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const locationToggle = document.querySelector("#location-toggle");
const connectionStatus = document.querySelector("#connection-status");
const messageTemplate = document.querySelector("#message-template");

const state = {
  userId: localStorage.getItem(USER_ID_KEY) || crypto.randomUUID(),
  sessionId: null,
  busy: false,
  renderedArtifacts: new Set(),
};
localStorage.setItem(USER_ID_KEY, state.userId);

function setConnection(label, mode = "online") {
  connectionStatus.lastChild.textContent = ` ${label}`;
  connectionStatus.classList.toggle("is-online", mode === "online");
  connectionStatus.classList.toggle("is-error", mode === "error");
}

function scrollToLatest() {
  requestAnimationFrame(() => {
    conversation.scrollTo({ top: conversation.scrollHeight, behavior: "smooth" });
  });
}

function createMessage(role, text = "") {
  const element = messageTemplate.content.firstElementChild.cloneNode(true);
  const avatar = element.querySelector(".message-avatar");
  const meta = element.querySelector(".message-meta");
  const content = element.querySelector(".message-content");

  element.classList.add(`is-${role}`);
  avatar.textContent = role === "user" ? "YOU" : "AI";
  meta.textContent = role === "user" ? "あなた" : "調査チーム";
  content.textContent = text;
  conversation.append(element);
  scrollToLatest();
  return element;
}

function addContextChips(element, context) {
  const holder = element.querySelector(".message-context");
  const chips = [context.timeLabel, context.timeZone];
  if (context.position) {
    chips.push(
      `位置 ${context.position.latitude.toFixed(4)}, ${context.position.longitude.toFixed(4)}`,
    );
  } else if (locationToggle.checked) {
    chips.push("位置情報なし");
  }

  for (const label of chips) {
    const chip = document.createElement("span");
    chip.className = "context-chip";
    chip.textContent = label;
    holder.append(chip);
  }
}

function getPosition() {
  return new Promise((resolve) => {
    if (!locationToggle.checked || !("geolocation" in navigator)) {
      resolve(null);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      ({ coords }) =>
        resolve({
          latitude: coords.latitude,
          longitude: coords.longitude,
          accuracyMeters: Math.round(coords.accuracy),
        }),
      () => resolve(null),
      { enableHighAccuracy: false, timeout: 6000, maximumAge: 60000 },
    );
  });
}

async function collectClientContext() {
  const now = new Date();
  return {
    isoTime: now.toISOString(),
    timeLabel: new Intl.DateTimeFormat("ja-JP", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(now),
    timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    position: await getPosition(),
  };
}

function enrichMessage(message, context) {
  const lines = [
    message,
    "",
    "[クライアントコンテキスト]",
    `送信時刻: ${context.isoTime}`,
    `タイムゾーン: ${context.timeZone}`,
  ];
  if (context.position) {
    lines.push(
      `位置情報: 緯度 ${context.position.latitude}, 経度 ${context.position.longitude}, 精度 約${context.position.accuracyMeters}m`,
    );
  } else {
    lines.push("位置情報: 未取得");
  }
  return lines.join("\n");
}

async function ensureSession() {
  if (state.sessionId) return;

  const response = await fetch(
    `${API_BASE}/apps/${APP_NAME}/users/${encodeURIComponent(state.userId)}/sessions`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    },
  );
  if (!response.ok) throw new Error(`セッション作成に失敗しました (${response.status})`);
  const session = await response.json();
  state.sessionId = session.id;
}

async function renderArtifact(filename, version, messageElement) {
  const artifactKey = `${filename}:${version}`;
  if (state.renderedArtifacts.has(artifactKey)) return;

  const url =
    `${API_BASE}/apps/${APP_NAME}/users/${encodeURIComponent(state.userId)}` +
    `/sessions/${encodeURIComponent(state.sessionId)}/artifacts/${encodeURIComponent(filename)}` +
    `/versions/${version}`;
  const response = await fetch(url);
  if (!response.ok) return;
  const artifact = await response.json();
  const inlineData = artifact.inlineData || artifact.inline_data;
  if (!inlineData?.data) return;

  appendGeneratedImage(inlineData, messageElement);
  state.renderedArtifacts.add(artifactKey);
  scrollToLatest();
}

function base64ImageToBlob(data, mimeType) {
  const payload = data.includes(",") ? data.slice(data.indexOf(",") + 1) : data;
  const normalized = payload
    .replace(/\s/g, "")
    .replace(/-/g, "+")
    .replace(/_/g, "/");
  const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new Blob([bytes], { type: mimeType });
}

function appendGeneratedImage(inlineData, messageElement) {
  const mimeType = inlineData.mimeType || inlineData.mime_type || "image/png";
  const blob = base64ImageToBlob(inlineData.data, mimeType);
  const objectUrl = URL.createObjectURL(blob);
  const image = document.createElement("img");
  image.src = objectUrl;
  image.alt = "エージェントが生成した画像";
  image.loading = "eager";
  image.addEventListener("load", () => URL.revokeObjectURL(objectUrl), { once: true });
  image.addEventListener(
    "error",
    () => {
      URL.revokeObjectURL(objectUrl);
      const error = document.createElement("p");
      error.className = "image-error";
      error.textContent = "補助画像を表示できませんでした。";
      image.replaceWith(error);
    },
    { once: true },
  );
  const content = messageElement.querySelector(".message-content");
  content.querySelector(".typing")?.remove();
  content.append(image);
}

function appendResponseText(messageElement, text) {
  const content = messageElement.querySelector(".message-content");
  content.querySelector(".typing")?.remove();
  const paragraph = document.createElement("p");
  paragraph.className = "response-text";
  paragraph.textContent = text;
  content.append(paragraph);
}

const progressStages = [
  ["geology", "地質を調査"],
  ["tourism", "観光を調査"],
  ["integration", "情報と地図を統合"],
  ["image", "補助画像を生成"],
];

function createResearchProgress(messageElement) {
  const progress = document.createElement("section");
  progress.className = "research-progress";
  progress.setAttribute("aria-label", "調査の進捗");

  const heading = document.createElement("div");
  heading.className = "progress-heading";
  heading.innerHTML =
    '<span class="progress-pulse" aria-hidden="true"></span>' +
    '<strong>調査の準備中</strong><small>2つの専門エージェントが連携します</small>';

  const steps = document.createElement("ol");
  steps.className = "progress-steps";
  for (const [stage, label] of progressStages) {
    const step = document.createElement("li");
    step.dataset.stage = stage;
    step.dataset.status = "waiting";
    step.innerHTML = `<span aria-hidden="true"></span><div><b>${label}</b><small>待機中</small></div>`;
    steps.append(step);
  }

  progress.append(heading, steps);
  messageElement.querySelector(".message-content").append(progress);
}

function setProgressHeadline(messageElement, title, detail) {
  const heading = messageElement.querySelector(".progress-heading");
  if (!heading) return;
  heading.querySelector("strong").textContent = title;
  heading.querySelector("small").textContent = detail;
}

function setProgressStage(messageElement, stage, status, detail) {
  const step = messageElement.querySelector(`[data-stage="${stage}"]`);
  if (!step) return;

  const rank = { waiting: 0, active: 1, done: 2, error: 3 };
  if (rank[status] < rank[step.dataset.status]) return;
  step.dataset.status = status;
  step.querySelector("small").textContent = detail;
}

function updateResearchProgress(event, messageElement) {
  const parts = event.content?.parts || [];
  const artifactDelta = event.actions?.artifactDelta || event.actions?.artifact_delta || {};
  const functionCalls = parts
    .map((part) => part.functionCall || part.function_call)
    .filter(Boolean);
  const functionResponses = parts
    .map((part) => part.functionResponse || part.function_response)
    .filter(Boolean);

  const callNames = new Set(functionCalls.map((call) => call.name));
  if (callNames.has("geology_research_agent")) {
    setProgressStage(messageElement, "geology", "active", "地質データを確認中");
  }
  if (callNames.has("tourism_research_agent")) {
    setProgressStage(messageElement, "tourism", "active", "観光プランを確認中");
  }
  if (
    callNames.has("geology_research_agent") ||
    callNames.has("tourism_research_agent")
  ) {
    setProgressHeadline(
      messageElement,
      "専門エージェントが調査中",
      "地質と観光をそれぞれ調べています",
    );
  }

  if (event.author === "geology_research_agent") {
    setProgressStage(
      messageElement,
      "geology",
      parts.some((part) => part.text) ? "done" : "active",
      parts.some((part) => part.text) ? "地質レポートを受け取りました" : "地質データを整理中",
    );
  }
  if (event.author === "tourism_research_agent") {
    setProgressStage(
      messageElement,
      "tourism",
      parts.some((part) => part.text) ? "done" : "active",
      parts.some((part) => part.text) ? "観光レポートを受け取りました" : "観光データを整理中",
    );
  }

  for (const response of functionResponses) {
    if (response.name === "geology_research_agent") {
      setProgressStage(messageElement, "geology", "done", "地質レポートを受け取りました");
    }
    if (response.name === "tourism_research_agent") {
      setProgressStage(messageElement, "tourism", "done", "観光レポートを受け取りました");
    }
    if (response.name === "create_mock_map_points") {
      setProgressStage(messageElement, "integration", "done", "解説と5地点を整理しました");
    }
    if (response.name === "generate_image") {
      const succeeded = response.response?.status === "success";
      setProgressStage(
        messageElement,
        "image",
        succeeded ? "done" : "error",
        succeeded ? "補助画像ができました" : "画像を生成できませんでした",
      );
    }
  }

  if (callNames.has("create_mock_map_points")) {
    setProgressStage(messageElement, "integration", "active", "2つの調査結果を関連付け中");
    setProgressHeadline(
      messageElement,
      "調査結果をまとめています",
      "地質と観光のつながり、地図地点を整理中",
    );
  }
  if (callNames.has("generate_image")) {
    setProgressStage(messageElement, "image", "active", "解説に合う景色を描画中");
    setProgressHeadline(
      messageElement,
      "補助画像を生成しています",
      "調査内容を一枚のイメージにしています",
    );
  }

  if (Object.keys(artifactDelta).length) {
    setProgressStage(messageElement, "image", "done", "補助画像ができました");
  }

  if (event.author === "root_agent" && parts.some((part) => part.text)) {
    for (const [stage] of progressStages) {
      const step = messageElement.querySelector(`[data-stage="${stage}"]`);
      if (step?.dataset.status !== "error") {
        setProgressStage(messageElement, stage, "done", step.querySelector("small").textContent);
      }
    }
    setProgressHeadline(messageElement, "調査が完了しました", "解説・地図・補助画像をまとめました");
    messageElement.querySelector(".research-progress")?.classList.add("is-complete");
  }
}

function renderMap(points, messageElement) {
  const validPoints = points.filter(
    (point) => Number.isFinite(point.latitude) && Number.isFinite(point.longitude),
  );
  if (!validPoints.length) return;

  const signature = JSON.stringify(validPoints);
  if (messageElement.dataset.mapSignature === signature) return;
  messageElement.dataset.mapSignature = signature;

  const latitudes = validPoints.map((point) => point.latitude);
  const longitudes = validPoints.map((point) => point.longitude);
  const minLatitude = Math.min(...latitudes);
  const maxLatitude = Math.max(...latitudes);
  const minLongitude = Math.min(...longitudes);
  const maxLongitude = Math.max(...longitudes);
  const latitudeRange = Math.max(maxLatitude - minLatitude, 0.008);
  const longitudeRange = Math.max(maxLongitude - minLongitude, 0.008);

  const card = document.createElement("section");
  card.className = "map-card";
  const header = document.createElement("div");
  header.className = "map-header";
  header.innerHTML = "<strong>調査地点</strong><span>MOCK MAP</span>";
  const map = document.createElement("div");
  map.className = "mock-map";
  const legend = document.createElement("ol");
  legend.className = "map-legend";

  validPoints.forEach((point, index) => {
    const pin = document.createElement("div");
    pin.className = "map-pin";
    pin.style.left = `${15 + ((point.longitude - minLongitude) / longitudeRange) * 70}%`;
    pin.style.top = `${85 - ((point.latitude - minLatitude) / latitudeRange) * 70}%`;
    pin.setAttribute("aria-label", point.title);
    const pinLabel = document.createElement("span");
    pinLabel.textContent = String(index + 1);
    pin.append(pinLabel);
    map.append(pin);

    const item = document.createElement("li");
    const number = document.createElement("b");
    number.textContent = String(index + 1);
    const details = document.createElement("div");
    const title = document.createElement("span");
    title.textContent = point.title;
    const coordinates = document.createElement("small");
    coordinates.textContent = `${point.latitude.toFixed(5)}, ${point.longitude.toFixed(5)}`;
    details.append(title, coordinates);
    item.append(number, details);
    legend.append(item);
  });

  card.append(header, map, legend);
  const content = messageElement.querySelector(".message-content");
  content.querySelector(".typing")?.remove();
  content.append(card);
  scrollToLatest();
}

async function handleEvent(event, messageElement) {
  if (event.errorCode || event.error_code || event.error) {
    throw new Error(
      event.errorMessage ||
        event.error_message ||
        event.error ||
        "エージェントでエラーが発生しました",
    );
  }

  updateResearchProgress(event, messageElement);

  const isRootEvent = event.author === "root_agent";

  for (const part of event.content?.parts || []) {
    if (part.text && isRootEvent) {
      appendResponseText(messageElement, part.text);
    }
    const functionResponse = part.functionResponse || part.function_response;
    if (
      isRootEvent &&
      functionResponse?.name === "create_mock_map_points" &&
      Array.isArray(functionResponse.response?.map_points)
    ) {
      renderMap(functionResponse.response.map_points, messageElement);
    }
    const inlineData = part.inlineData || part.inline_data;
    if (inlineData?.data && isRootEvent) {
      appendGeneratedImage(inlineData, messageElement);
    }
  }

  const artifactDelta = event.actions?.artifactDelta || event.actions?.artifact_delta || {};
  for (const [filename, version] of Object.entries(artifactDelta)) {
    await renderArtifact(filename, version, messageElement);
  }
  scrollToLatest();
}

async function consumeSse(response, onEvent) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";

    for (const block of blocks) {
      const data = block
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trim())
        .join("\n");
      if (data) await onEvent(JSON.parse(data));
    }
    if (done) break;
  }
}

async function sendMessage(message) {
  if (state.busy || !message.trim()) return;
  state.busy = true;
  sendButton.disabled = true;
  input.disabled = true;

  let assistantMessage;
  try {
    setConnection("コンテキスト取得中");
    const context = await collectClientContext();
    const userMessage = createMessage("user", message.trim());
    addContextChips(userMessage, context);

    assistantMessage = createMessage("assistant");
    createResearchProgress(assistantMessage);

    await ensureSession();
    setConnection("エージェント実行中");
    const response = await fetch(`${API_BASE}/run_sse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        appName: APP_NAME,
        userId: state.userId,
        sessionId: state.sessionId,
        newMessage: {
          role: "user",
          parts: [{ text: enrichMessage(message.trim(), context) }],
        },
        streaming: false,
      }),
    });
    if (!response.ok) throw new Error(`送信に失敗しました (${response.status})`);

    await consumeSse(response, (event) => handleEvent(event, assistantMessage));
    if (
      !assistantMessage
        .querySelector(".message-content")
        .querySelector(".response-text, .map-card, img")
    ) {
      appendResponseText(assistantMessage, "処理が完了しました。");
    }
    assistantMessage.querySelector(".message-meta").textContent = "調査チーム";
    setConnection("接続済み");
  } catch (error) {
    const target = assistantMessage || createMessage("assistant");
    target.classList.add("is-error");
    target.querySelector(".message-content").textContent = error.message;
    setConnection("エラー", "error");
  } finally {
    state.busy = false;
    sendButton.disabled = false;
    input.disabled = false;
    input.focus();
    scrollToLatest();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = input.value;
  input.value = "";
  input.style.height = "auto";
  sendMessage(message);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 130)}px`;
});

input.addEventListener("keydown", (event) => {
  if (
    event.key === "Enter" &&
    (event.ctrlKey || event.metaKey) &&
    !event.isComposing &&
    event.keyCode !== 229
  ) {
    event.preventDefault();
    form.requestSubmit();
  }
});

for (const button of document.querySelectorAll("[data-prompt]")) {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt;
    input.dispatchEvent(new Event("input"));
    input.focus();
  });
}

async function initialize() {
  try {
    const response = await fetch(`${API_BASE}/list-apps`);
    if (!response.ok) throw new Error();
    setConnection("接続済み");
  } catch {
    setConnection("ADK未接続", "error");
  }
}

initialize();

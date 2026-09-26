const TOKEN_KEY = "fieldnote-admin-token";
const STATUS_LABELS = {
  done: "完了",
  running: "実行中",
  incomplete: "未完了",
};

const $ = (id) => document.getElementById(id);
const usd = (value) => `$${value.toFixed(value < 1 ? 3 : 2)}`;
const count = (value) => value.toLocaleString("ja-JP");
const shortId = (id) => id.slice(-8);
const dateTime = new Intl.DateTimeFormat("ja-JP", {
  month: "numeric",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});
const formatTime = (value) => dateTime.format(new Date(value));
const formatSeconds = (value) =>
  value >= 60 ? `${Math.floor(value / 60)}分${Math.round(value % 60)}秒` : `${Math.round(value)}秒`;

function readToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY) || "";
  } catch {
    return "";
  }
}

function saveToken(token) {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // The token then lasts only for this page view.
  }
}

let token = readToken();

function cell(text, className) {
  const td = document.createElement("td");
  td.textContent = text;
  if (className) td.className = className;
  return td;
}

function badge(status) {
  const td = document.createElement("td");
  const span = document.createElement("span");
  span.className = `badge badge-${status}`;
  span.textContent = STATUS_LABELS[status] || status;
  td.append(span);
  return td;
}

function emptyRow(tbody, columns) {
  const tr = document.createElement("tr");
  const td = cell("なし", "empty");
  td.colSpan = columns;
  tr.append(td);
  tbody.replaceChildren(tr);
}

function render(data) {
  $("cost-total").textContent = usd(data.cost.total);
  $("cost-detail").textContent = `LLM ${usd(data.cost.llm)} · 画像 ${usd(data.cost.images)}`;

  const latest = data.latest_session;
  $("latest-cost").textContent = latest ? usd(latest.cost) : "—";
  $("latest-detail").textContent = latest
    ? `${shortId(latest.id)} ${latest.question}`
    : "まだありません";

  $("sessions-total").textContent = count(data.sessions.total);
  $("sessions-detail").textContent =
    `直近24時間 ${count(data.sessions.last_24h)} · ユーザー ${count(data.sessions.users)}`;

  $("latency-average").textContent =
    data.latency.average == null ? "—" : formatSeconds(data.latency.average);
  $("latency-detail").textContent =
    data.latency.max == null
      ? "完了したターンなし"
      : `最大 ${formatSeconds(data.latency.max)} · ${count(data.latency.turns)} ターン`;

  $("tool-rate").textContent = `${(data.tools.rate * 100).toFixed(1)}%`;
  $("tool-detail").textContent = `${count(data.tools.errors)} / ${count(data.tools.calls)} 件`;

  const incomplete = $("turns-incomplete");
  incomplete.textContent = count(data.turns.incomplete);
  incomplete.classList.toggle("alert", data.turns.incomplete > 0);

  $("images").textContent = count(data.images);

  const tokens = data.tokens.input + data.tokens.output;
  $("tokens-total").textContent = count(tokens);
  $("tokens-detail").textContent =
    `入力 ${count(data.tokens.input)} · 出力 ${count(data.tokens.output)}`;

  const sessionRows = $("session-rows");
  if (data.session_rows.length === 0) {
    emptyRow(sessionRows, 6);
  } else {
    sessionRows.replaceChildren(
      ...data.session_rows.map((row) => {
        const tr = document.createElement("tr");
        const question = cell(row.question || "（なし）", "question");
        question.title = row.question;
        tr.append(
          cell(formatTime(row.created), "nowrap"),
          badge(row.status),
          question,
          cell(count(row.turns), "num"),
          cell(usd(row.cost), "num"),
          cell(shortId(row.id), "mono"),
        );
        return tr;
      }),
    );
  }

  const errorRows = $("error-rows");
  if (data.errors.length === 0) {
    emptyRow(errorRows, 4);
  } else {
    errorRows.replaceChildren(
      ...data.errors.map((error) => {
        const tr = document.createElement("tr");
        tr.append(
          cell(formatTime(error.time), "nowrap"),
          cell(error.source, "mono"),
          cell(error.message, "question"),
          cell(shortId(error.session), "mono"),
        );
        return tr;
      }),
    );
  }

  $("updated").textContent = `${formatTime(data.generated_at)} 時点`;
}

function showLogin(message) {
  $("dashboard").hidden = true;
  $("actions").hidden = true;
  $("login").hidden = false;
  const error = $("login-error");
  error.hidden = !message;
  error.textContent = message || "";
  $("token").focus();
}

async function load(refresh = false) {
  if (!token) {
    showLogin();
    return;
  }
  $("actions").hidden = false;
  const button = $("refresh");
  button.disabled = true;
  $("updated").textContent = "読み込み中…";
  try {
    const response = await fetch(`/api/admin/summary${refresh ? "?refresh=true" : ""}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (response.status === 401) {
      token = "";
      saveToken("");
      showLogin("トークンが違います。");
      return;
    }
    if (!response.ok) {
      throw new Error(`${response.status} ${await response.text()}`);
    }
    render(await response.json());
    $("login").hidden = true;
    $("dashboard").hidden = false;
  } catch (error) {
    $("updated").textContent = `読み込みに失敗しました: ${error.message}`;
  } finally {
    button.disabled = false;
  }
}

$("login").addEventListener("submit", (event) => {
  event.preventDefault();
  token = $("token").value.trim();
  saveToken(token);
  load();
});
$("refresh").addEventListener("click", () => load(true));

load();

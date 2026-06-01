"""Web-Chat-Terminal für Stevi.

Startet einen kleinen HTTP-Server (nur Standardbibliothek, keine Extra-Pakete) mit
einer Browser-Oberfläche, über die du mit Stevi chatten kannst. Ideal, um Stevi
dauerhaft auf einem Server laufen zu lassen und von überall zu erreichen.

Start:
    python -m stevi web                  # http://127.0.0.1:8000
    python -m stevi web 0.0.0.0 8000     # von außen erreichbar (Server)

Sicherheit: Diese Oberfläche hat KEINE Anmeldung. Stelle sie nur in vertrauens-
würdigen Netzen bereit oder setze einen Reverse-Proxy mit Passwortschutz davor,
wenn du sie öffentlich machst.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .agent import Agent
from .config import Config

# Pro Browser-Sitzung ein eigener Agent (eigene Gesprächshistorie).
_sessions: dict[str, tuple[Agent, threading.Lock]] = {}
_sessions_lock = threading.Lock()
_config = Config.from_env()


def _get_session(session_id: str) -> tuple[Agent, threading.Lock]:
    with _sessions_lock:
        if session_id not in _sessions:
            _sessions[session_id] = (Agent(_config), threading.Lock())
        return _sessions[session_id]


class Handler(BaseHTTPRequestHandler):
    # Ruhigere Logs.
    def log_message(self, *args: Any) -> None:  # noqa: D401
        return

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._send_html(INDEX_HTML)
        elif self.path == "/api/health":
            self._send_json(
                200,
                {
                    "ok": True,
                    "backend": _config.backend,
                    "model": _config.model_label,
                },
            )
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if self.path != "/api/chat":
            self._send_json(404, {"error": "Not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, ValueError):
            self._send_json(400, {"error": "Ungültiges JSON"})
            return

        session_id = str(data.get("session_id", "")).strip() or "default"
        message = str(data.get("message", "")).strip()
        if not message:
            self._send_json(400, {"error": "Leere Nachricht"})
            return

        agent, lock = _get_session(session_id)
        tools_used: list[str] = []

        def on_tool(name: str, _inp: dict[str, Any]) -> None:
            tools_used.append(name)

        try:
            with lock:  # ein Agent verarbeitet immer nur eine Nachricht zugleich
                reply = agent.send(message, on_tool=on_tool)
        except Exception as exc:  # pragma: no cover - Laufzeitfehler
            self._send_json(500, {"error": str(exc)})
            return

        self._send_json(
            200,
            {"reply": reply, "tools": tools_used, "model": _config.model_label},
        )


def run_web(host: str = "127.0.0.1", port: int = 8000) -> int:
    """Startet den Web-Server. Gibt einen Exit-Code zurück."""
    server = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}"
    print("🟩 Stevi Web-Terminal")
    print(f"   Backend: {_config.backend}  ·  Modell: {_config.model_label}")
    print(f"   Läuft auf: {url}")
    print("   Zum Beenden: Strg+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer beendet. Bis bald! 🟩")
    finally:
        server.server_close()
    return 0


# ---------------------------------------------------------------------------
# Eingebettete Web-Oberfläche (eine einzige HTML-Datei, kein Build nötig)
# ---------------------------------------------------------------------------

INDEX_HTML = """\
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Stevi — Minecraft-Modding-KI</title>
<style>
  :root { --bg:#0e1116; --panel:#161b22; --green:#3fb950; --text:#e6edf3; --muted:#8b949e; --user:#1f6feb; }
  * { box-sizing: border-box; }
  body { margin:0; height:100vh; display:flex; flex-direction:column;
         background:var(--bg); color:var(--text);
         font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
  header { padding:12px 16px; background:var(--panel); border-bottom:1px solid #30363d;
           display:flex; align-items:center; gap:10px; }
  header .logo { font-size:20px; }
  header h1 { font-size:15px; margin:0; font-weight:600; }
  header .model { margin-left:auto; color:var(--muted); font-size:12px; }
  #chat { flex:1; overflow-y:auto; padding:18px 16px; display:flex; flex-direction:column; gap:14px; }
  .msg { max-width:820px; width:100%; margin:0 auto; }
  .msg .who { font-size:12px; color:var(--muted); margin-bottom:4px; }
  .bubble { padding:10px 14px; border-radius:10px; white-space:pre-wrap; word-wrap:break-word;
            line-height:1.5; background:var(--panel); border:1px solid #30363d; }
  .user .bubble { background:#11233f; border-color:#1f6feb55; }
  .stevi .who { color:var(--green); }
  .tool { font-size:12px; color:var(--muted); font-style:italic; margin:2px 0; }
  pre { background:#0b0f14; border:1px solid #30363d; border-radius:8px; padding:10px;
        overflow-x:auto; margin:8px 0; }
  code { font-family: inherit; }
  footer { padding:12px 16px; background:var(--panel); border-top:1px solid #30363d; }
  .inputrow { max-width:820px; margin:0 auto; display:flex; gap:8px; }
  textarea { flex:1; resize:none; background:#0b0f14; color:var(--text); border:1px solid #30363d;
             border-radius:8px; padding:10px; font-family:inherit; font-size:14px; height:46px; }
  button { background:var(--green); color:#07210f; border:none; border-radius:8px; padding:0 18px;
           font-weight:700; cursor:pointer; font-family:inherit; }
  button:disabled { opacity:.5; cursor:default; }
  .hint { max-width:820px; margin:6px auto 0; color:var(--muted); font-size:11px; text-align:center; }
</style>
</head>
<body>
<header>
  <span class="logo">🟩</span>
  <h1>Stevi — Minecraft-Modding-KI</h1>
  <span class="model" id="model">…</span>
</header>
<div id="chat"></div>
<footer>
  <div class="inputrow">
    <textarea id="input" placeholder="Frag Stevi etwas oder bitte um eine Mod/ein Modpack… (Enter zum Senden)"></textarea>
    <button id="send">Senden</button>
  </div>
  <div class="hint">Stevi läuft kostenlos auf deinem Server. Enter = senden · Shift+Enter = neue Zeile</div>
</footer>
<script>
const chat = document.getElementById('chat');
const input = document.getElementById('input');
const sendBtn = document.getElementById('send');
const modelEl = document.getElementById('model');

// Eindeutige Sitzungs-ID pro Browser merken.
let sid = localStorage.getItem('stevi_sid');
if (!sid) { sid = Math.random().toString(36).slice(2); localStorage.setItem('stevi_sid', sid); }

fetch('/api/health').then(r=>r.json()).then(d=>{ modelEl.textContent = d.model; }).catch(()=>{});

function escapeHtml(s){ return s.replace(/[&<>]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }

// Sehr einfaches Markdown: ```code``` -> <pre>, Rest escaped.
function render(text){
  const parts = text.split(/```/);
  let html = '';
  parts.forEach((p, i) => {
    if (i % 2 === 1) { html += '<pre><code>' + escapeHtml(p.replace(/^[a-zA-Z]*\\n/, '')) + '</code></pre>'; }
    else { html += escapeHtml(p); }
  });
  return html;
}

function addMessage(who, cls, htmlContent){
  const wrap = document.createElement('div');
  wrap.className = 'msg ' + cls;
  wrap.innerHTML = '<div class="who">' + who + '</div><div class="bubble">' + htmlContent + '</div>';
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
  return wrap;
}

addMessage('🟩 Stevi', 'stevi',
  'Hi! Ich bin Stevi, deine Minecraft-Modding-KI. Ich kann über Minecraft &amp; Fabric reden ' +
  'und dir echte Mods/Modpacks bauen. Was sollen wir machen?');

async function send(){
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  addMessage('Du', 'user', escapeHtml(text));
  sendBtn.disabled = true;
  const thinking = addMessage('🟩 Stevi', 'stevi', '<span class="tool">… denkt nach</span>');
  try {
    const res = await fetch('/api/chat', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ session_id: sid, message: text })
    });
    const data = await res.json();
    thinking.remove();
    if (data.error) { addMessage('🟩 Stevi', 'stevi', '<span class="tool">Fehler: ' + escapeHtml(data.error) + '</span>'); }
    else {
      let toolNote = '';
      if (data.tools && data.tools.length) {
        toolNote = '<div class="tool">🛠️ Werkzeuge: ' + data.tools.map(escapeHtml).join(', ') + '</div>';
      }
      addMessage('🟩 Stevi', 'stevi', toolNote + render(data.reply || '(keine Antwort)'));
    }
  } catch (e) {
    thinking.remove();
    addMessage('🟩 Stevi', 'stevi', '<span class="tool">Netzwerkfehler: ' + escapeHtml(String(e)) + '</span>');
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

sendBtn.addEventListener('click', send);
input.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
});
input.focus();
</script>
</body>
</html>
"""

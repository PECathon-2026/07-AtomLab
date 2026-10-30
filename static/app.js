document.addEventListener("DOMContentLoaded", () => {
  const prompt = document.getElementById("prompt");
  const send = document.getElementById("sendButton");
  const fileInput = document.getElementById("fileInput");
  const attachments = document.getElementById("attachments");
  const chat = document.getElementById("chat");
  const statusPill = document.getElementById("statusPill");
  let selectedFiles = [];
  let pollingTimer = null;

  document.querySelectorAll(".suggestion").forEach(button => {
    button.addEventListener("click", () => {
      prompt.value = button.textContent;
      prompt.focus();
    });
  });
  document.getElementById("newChat").addEventListener("click", () => {
    prompt.value = "";
    selectedFiles = [];
    renderAttachments();
    chat.innerHTML = `<div class="welcome" id="welcome"><div class="welcome-mark">✳</div><h2>Your coding partner,<br><em>running locally.</em></h2><p>Describe a change, attach your project files, and let DevPilot plan, edit, test, and package the result.</p><div class="suggestions"><button class="suggestion">Find and fix a bug in my project</button><button class="suggestion">Add a feature and write tests</button><button class="suggestion">Review these files for issues</button></div></div>`;
    document.querySelectorAll(".suggestion").forEach(button => button.onclick = () => {prompt.value=button.textContent;prompt.focus();});
    statusPill.textContent = "Ready";
  });
  fileInput.addEventListener("change", () => {
    selectedFiles.push(...Array.from(fileInput.files));
    selectedFiles = selectedFiles.filter((file, index, list) => list.findIndex(f => f.name === file.name && f.size === file.size) === index);
    renderAttachments();
    fileInput.value = "";
  });
  function renderAttachments() {
    attachments.innerHTML = "";
    selectedFiles.forEach((file, index) => {
      const chip = document.createElement("div");
      chip.className = "file-chip";
      chip.textContent = `${file.name} · ${formatSize(file.size)} `;
      const remove = document.createElement("button");
      remove.textContent = "×";
      remove.title = "Remove file";
      remove.onclick = () => { selectedFiles.splice(index, 1); renderAttachments(); };
      chip.appendChild(remove);
      attachments.appendChild(chip);
    });
  }
  function formatSize(bytes) { return bytes < 1024*1024 ? `${Math.ceil(bytes/1024)} KB` : `${(bytes/1024/1024).toFixed(1)} MB`; }
  function addMessage(role, text) {
    const node = document.createElement("div");
    node.className = `message ${role}`;
    const who = document.createElement("div");
    who.className = "who";
    who.textContent = role === "user" ? "YOU" : "DEVPILOT";
    const body = document.createElement("div");
    body.textContent = text;
    node.append(who, body);
    chat.appendChild(node);
    chat.scrollTop = chat.scrollHeight;
    return node;
  }
  async function sendPrompt() {
    const text = prompt.value.trim();
    if (!text) { prompt.focus(); return; }
    if (selectedFiles.reduce((sum, file) => sum + file.size, 0) > 20*1024*1024) {
      addMessage("assistant", "The combined upload is larger than 20 MB. Remove some files and try again.");
      return;
    }
    document.getElementById("welcome")?.remove();
    addMessage("user", text + (selectedFiles.length ? `\n\nAttached: ${selectedFiles.map(f=>f.name).join(", ")}` : ""));
    prompt.value = "";
    send.disabled = true;
    send.textContent = "Working…";
    statusPill.textContent = "Running";
    const responseBubble = addMessage("assistant", "Starting the local agent…");
    try {
      const form = new FormData();
      form.append("prompt", text);
      selectedFiles.forEach(file => form.append("files", file, file.name));
      const response = await fetch("/api/missions", {method:"POST", body:form});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not start mission.");
      selectedFiles = [];
      renderAttachments();
      await pollMission(data.id, responseBubble);
    } catch (error) {
      responseBubble.lastChild.textContent = `Could not start task: ${error.message}`;
      statusPill.textContent = "Error";
      send.disabled = false;
      send.innerHTML = 'Send <span>↗</span>';
    }
  }
  async function pollMission(id, bubble) {
    if (pollingTimer) clearTimeout(pollingTimer);
    const check = async () => {
      try {
        const response = await fetch(`/api/missions/${id}`);
        const mission = await response.json();
        if (!response.ok) throw new Error(mission.detail || "Could not read mission status.");
        const logs = Array.isArray(mission.logs) ? mission.logs : [];
        const latest = logs.slice(-5).map(log => `${log.agent || log.level || "Agent"}: ${log.message || log.text || ""}`).join("\n");
        bubble.lastChild.textContent = `${mission.status === "completed" ? "Task finished." : mission.status === "failed" ? "Task failed." : "DevPilot is working…"}\n\n${latest || "Preparing agents…"}`;
        if (mission.status === "completed" || mission.status === "failed") {
          statusPill.textContent = mission.status === "completed" ? "Complete" : "Failed";
          if (mission.download_ready) {
            const link = document.createElement("a");
            link.className = "download";
            link.href = `/api/missions/${id}/download`;
            link.download = mission.download_name || "devpilot-result.zip";
            link.textContent = "Download project result ↓";
            bubble.appendChild(link);
          }
          send.disabled = false;
          send.innerHTML = 'Send <span>↗</span>';
          return;
        }
        pollingTimer = setTimeout(check, 1800);
      } catch (error) {
        bubble.lastChild.textContent = `Status check error: ${error.message}`;
        send.disabled = false;
        send.innerHTML = 'Send <span>↗</span>';
        statusPill.textContent = "Error";
      }
    };
    await check();
  }
  send.addEventListener("click", sendPrompt);
  prompt.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); sendPrompt(); }
  });
});

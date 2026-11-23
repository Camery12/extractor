const $ = (id) => document.getElementById(id);

let currentUrl = "";
let kind = "video";

function showError(msg) {
  $("error").textContent = msg;
  $("error").classList.toggle("hidden", !msg);
}

function fmtDuration(s) {
  if (!s) return "";
  s = Math.round(s);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  return (h ? h + ":" + String(m).padStart(2, "0") : m) + ":" + String(sec).padStart(2, "0");
}

function fmtBytes(b) {
  if (!b) return "";
  const u = ["B", "KB", "MB", "GB"];
  let i = 0;
  while (b >= 1024 && i < u.length - 1) { b /= 1024; i++; }
  return b.toFixed(i ? 1 : 0) + " " + u[i];
}

$("paste").addEventListener("click", async () => {
  try {
    $("url").value = (await navigator.clipboard.readText()).trim();
    $("url").focus();
  } catch { showError("Zugriff auf die Zwischenablage nicht erlaubt – bitte manuell einfügen."); }
});

$("url-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = $("url").value.trim();
  if (!url) return;
  showError("");
  $("result").classList.add("hidden");
  $("platform-badge").classList.add("hidden");
  $("analyze").disabled = true;
  $("analyze").textContent = "Lädt…";
  try {
    const res = await fetch("/api/info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Fehler");
    currentUrl = url;
    renderInfo(data);
  } catch (err) {
    showError(err.message);
  } finally {
    $("analyze").disabled = false;
    $("analyze").textContent = "Analysieren";
  }
});

function renderInfo(d) {
  $("platform-badge").textContent = "Erkannt: " + d.platform;
  $("platform-badge").classList.remove("hidden");
  $("thumb").src = d.thumbnail || "";
  $("thumb").classList.toggle("hidden", !d.thumbnail);
  $("title").textContent = d.title;
  $("uploader").textContent = d.uploader;
  $("duration").textContent = d.duration ? "Dauer: " + fmtDuration(d.duration) : "";

  // Auflösungen, die nicht verfügbar sind, ausgrauen
  const maxH = d.heights && d.heights.length ? d.heights[0] : null;
  for (const opt of $("resolution").options) {
    if (opt.value === "best") { opt.disabled = false; continue; }
    const h = parseInt(opt.value, 10);
    opt.disabled = maxH !== null && !d.heights.some((x) => x <= h);
    const avail = maxH !== null && d.heights.includes(h);
    opt.textContent = opt.textContent.replace(" ✓", "") + (avail ? " ✓" : "");
  }
  $("resolution").value = "best";

  // Nur Audio (z.B. SoundCloud) -> direkt Audio-Tab
  setKind(d.has_video ? "video" : "audio");
  document.querySelector('.tab[data-kind="video"]').disabled = !d.has_video;

  $("progress-wrap").classList.add("hidden");
  $("download").disabled = false;
  $("download").textContent = "Herunterladen";
  $("result").classList.remove("hidden");
}

function setKind(k) {
  kind = k;
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.kind === k));
  $("video-options").classList.toggle("hidden", k !== "video");
  $("audio-options").classList.toggle("hidden", k !== "audio");
}

document.querySelectorAll(".tab").forEach((t) =>
  t.addEventListener("click", () => setKind(t.dataset.kind))
);

$("download").addEventListener("click", async () => {
  showError("");
  const body = {
    url: currentUrl,
    kind,
    format: kind === "video" ? $("video-format").value : $("audio-format").value,
    resolution: $("resolution").value,
    bitrate: $("bitrate").value,
  };
  $("download").disabled = true;
  $("progress-wrap").classList.remove("hidden");
  setProgress(0, "Wird gestartet…");

  try {
    const res = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Fehler");
    poll(data.job_id);
  } catch (err) {
    showError(err.message);
    $("download").disabled = false;
    $("progress-wrap").classList.add("hidden");
  }
});

function setProgress(pct, text, indeterminate = false) {
  const bar = $("progress-bar");
  bar.classList.toggle("indeterminate", indeterminate);
  bar.style.width = pct + "%";
  $("progress-text").textContent = text;
}

async function poll(jobId) {
  try {
    const res = await fetch("/api/progress/" + jobId);
    const j = await res.json();
    if (!res.ok) throw new Error(j.error || "Fehler");

    if (j.status === "error") throw new Error(j.error);
    if (j.status === "done") {
      setProgress(100, `Fertig: ${j.filename} (${fmtBytes(j.size)})`);
      window.location.href = "/api/file/" + jobId;
      $("download").disabled = false;
      $("download").textContent = "Erneut herunterladen";
      return;
    }
    if (j.status === "processing") {
      setProgress(100, "Wird konvertiert…", true);
    } else if (j.status === "downloading") {
      let t = `Download: ${j.progress}%`;
      if (j.speed) t += ` · ${fmtBytes(j.speed)}/s`;
      if (j.eta) t += ` · noch ${fmtDuration(j.eta)}`;
      setProgress(j.progress, t);
    } else {
      setProgress(0, "In Warteschlange…", true);
    }
    setTimeout(() => poll(jobId), 700);
  } catch (err) {
    showError(err.message);
    $("download").disabled = false;
    $("progress-wrap").classList.add("hidden");
  }
}

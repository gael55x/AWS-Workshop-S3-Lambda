const statusEl = document.querySelector("#status");
const uploadForm = document.querySelector("#uploadForm");
const fileInput = document.querySelector("#fileInput");
const gallery = document.querySelector("#gallery");
const refreshBtn = document.querySelector("#refreshBtn");

const apiBaseUrl = (window.CAT_UPLOAD_CONFIG?.apiBaseUrl || "").replace(/\/+$/, "");

function api() {
  return apiBaseUrl;
}

function setStatus(message, type = "info") {
  statusEl.textContent = message;
  statusEl.classList.remove("ok", "err");
  if (type === "ok") statusEl.classList.add("ok");
  if (type === "err") statusEl.classList.add("err");
}

async function loadImages() {
  gallery.innerHTML = "";
  setStatus("Loading images…");
  try {
    const res = await fetch(api());
    const data = await res.json();

    const images = Array.isArray(data.images) ? data.images : [];
    if (images.length === 0) {
      const empty = document.createElement("div");
      empty.className = "tile";
      empty.textContent = "No cats yet.";
      gallery.appendChild(empty);
      setStatus("No images found.", "ok");
      return;
    }

    for (const imgItem of images) {
      const url = typeof imgItem === "string" ? imgItem : imgItem?.url;
      const key = typeof imgItem === "string" ? null : imgItem?.key;
      if (!url) continue;

      const tile = document.createElement("div");
      tile.className = "tile";
      const imgEl = document.createElement("img");
      imgEl.alt = key ?? "cat";
      imgEl.src = url;
      tile.appendChild(imgEl);
      gallery.appendChild(tile);
    }
    setStatus(`Loaded ${images.length} image(s).`, "ok");
  } catch (err) {
    setStatus(`Failed to load images: ${err.message}`, "err");
  }
}

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = fileInput.files?.[0];
  if (!file) return setStatus("Pick an image first.", "err");

  setStatus("Requesting upload URL…");
  try {
    const res = await fetch(api(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: file.name,
        contentType: file.type || "application/octet-stream",
      }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.error || `Backend error (${res.status})`);
    }

    const { uploadUrl } = await res.json();
    if (!uploadUrl) throw new Error("Backend did not return uploadUrl.");

    setStatus("Uploading to S3…");
    const putRes = await fetch(uploadUrl, {
      method: "PUT",
      headers: { "Content-Type": file.type || "application/octet-stream" },
      body: file,
    });

    if (!putRes.ok) throw new Error(`S3 upload failed (${putRes.status}).`);

    setStatus("Upload complete. Refreshing gallery…", "ok");
    fileInput.value = "";
    await loadImages();
  } catch (err) {
    setStatus(err.message, "err");
  }
});

refreshBtn.addEventListener("click", loadImages);

loadImages();

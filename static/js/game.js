function getCSRF() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute("content") : "";
}

function formatNumber(n) {
  if (n < 10000) return String(Math.floor(n));
  const units = ["万", "亿", "兆", "京"];
  let i = -1;
  while (n >= 10000 && i < units.length - 1) {
    n /= 10000;
    i++;
  }
  const value = n >= 100 ? Math.floor(n) : n.toFixed(1);
  return value + units[i];
}

function parseNumber(text) {
  if (!text) return 0;
  const unitMap = { "万": 1e4, "亿": 1e8, "兆": 1e12, "京": 1e16 };
  const m = text.match(/([\d.]+)([万亿兆京]?)/);
  if (!m) return 0;
  const base = parseFloat(m[1] || "0");
  const unit = unitMap[m[2]] || 1;
  return base * unit;
}

function toast(msg, type = "info") {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = msg;
  el.classList.remove("error");
  if (type === "error") el.classList.add("error");
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 1800);
}

function floatText(text, x, y) {
  const el = document.createElement("div");
  el.className = "float-text";
  el.textContent = text;
  el.style.left = `${x}px`;
  el.style.top = `${y}px`;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 900);
}

function floatImg(x, y) {
  const el = document.createElement("img");
  el.className = "float-img";
  el.src = "/static/img/cxg-mini.png";
  el.style.left = `${x}px`;
  el.style.top = `${y}px`;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 900);
}

function flashBuilding(key) {
  const el = document.getElementById(`building-${key}`);
  if (!el) return;
  el.classList.add("flash");
  setTimeout(() => el.classList.remove("flash"), 300);
}

async function post(url, data) {
  const form = new FormData();
  Object.entries(data || {}).forEach(([k, v]) => form.append(k, v));
  const res = await fetch(url, {
    method: "POST",
    body: form,
    credentials: "same-origin",
    headers: { "X-CSRFToken": getCSRF() }
  });
  return res.json();
}

async function getState() {
  const res = await fetch("/api/state/");
  return res.json();
}

const LEVELS = [
  0, 800, 5000, 12000, 60000, 200000, 900000, 5000000, 18000000, 70000000,
  250000000, 900000000, 5500000000, 20000000000, 75000000000, 200000000000,
  800000000000, 4000000000000, 60000000000000, 200000000000000, 1000000000000000
];

function getLevel(total) {
  let level = 1;
  for (let i = 1; i < LEVELS.length; i++) {
    if (total >= LEVELS[i]) level = i + 1;
  }
  return level;
}

function updateLevel(total) {
  const level = getLevel(total);
  const prev = LEVELS[level - 1] || 0;
  const next = LEVELS[level] || (prev + prev);
  const pct = Math.min(100, Math.max(0, ((total - prev) / (next - prev)) * 100));
  document.getElementById("levelText").textContent = `Level ${level}`;
  document.getElementById("levelBar").style.width = `${pct}%`;
  document.getElementById("levelHint").textContent = `${formatNumber(total)} / ${formatNumber(next)}`;
  return level;
}

function rebuildStrip() {
  const strip = document.getElementById("buildingStrip");
  strip.innerHTML = "";
  document.querySelectorAll(".building").forEach(card => {
    const key = card.dataset.key;
    const amount = parseInt(card.dataset.amount || "0", 10);
    if (amount > 0) {
      const icon = document.createElement("img");
      icon.className = "strip-icon";
      icon.src = `/static/img/buildings/${key}.png`;
      strip.appendChild(icon);

      const badge = document.createElement("div");
      badge.className = "strip-badge";
      badge.textContent = `x${amount}`;
      strip.appendChild(badge);
    }
  });
}

function formatInitialNumbers() {
  const ids = ["apples", "totalApplesTop", "clicksTop", "perSecond", "perClick", "upgradePriceValue"];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    const raw = parseNumber(el.textContent);
    if (!isNaN(raw)) {
      if (id === "perSecond" || id === "perClick") {
        el.textContent = `+${formatNumber(raw)}`;
      } else {
        el.textContent = formatNumber(raw);
      }
    }
  });

  document.querySelectorAll("[id^='price-']").forEach(el => {
    const raw = parseNumber(el.textContent);
    if (!isNaN(raw)) el.textContent = formatNumber(raw);
  });

  document.querySelectorAll("[id^='effect-']").forEach(el => {
    const nums = el.textContent.match(/\d+(\.\d+)?/g);
    if (!nums) return;
    const a = formatNumber(parseFloat(nums[0] || "0"));
    const b = formatNumber(parseFloat(nums[1] || "0"));
    el.textContent = `+${a}/s，+${b}/点`;
  });
}

let currentPerClick = 1;
let currentPerSecond = 0;
let pendingClicks = parseInt(localStorage.getItem("pendingClicks") || "0", 10);
let clickTimer = null;

let localApples = parseNumber(document.getElementById("apples").textContent);
let localTotal = parseNumber(document.getElementById("totalApplesTop").textContent);
let currentUpgradeLevel = parseInt(document.getElementById("upgradeInfo").textContent.replace(/[^\d]/g, ""), 10) || 1;

let popBuffer = 0;
let lastPopTime = performance.now();

function popStatusGain() {
  const now = performance.now();
  if (now - lastPopTime < 400) return;
  if (popBuffer <= 0) return;

  const el = document.createElement("div");
  el.className = "float-text";
  el.textContent = `+${formatNumber(popBuffer)}`;
  const target = document.getElementById("apples");
  const rect = target.getBoundingClientRect();
  el.style.left = `${rect.left + rect.width / 2}px`;
  el.style.top = `${rect.top - 10}px`;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 900);

  popBuffer = 0;
  lastPopTime = now;
}

// -------- 小雌小鬼漂浮系统 --------
const sprites = [];
let spriteEnabled = true;
let spriteSpeed = 1.0;

function fieldSize() {
  const field = document.getElementById("spriteField");
  if (!field) return { w: 0, h: 0 };
  return { w: field.offsetWidth, h: field.offsetHeight };
}

function addSprite(staticMode = false) {
  const field = document.getElementById("spriteField");
  if (!field) return;

  const { w, h } = fieldSize();
  if (w <= 0 || h <= 0) {
    requestAnimationFrame(() => addSprite(staticMode));
    return;
  }

  const img = document.createElement("img");
  img.src = "/static/img/cxg-mini.png";
  img.className = "sprite";
  field.appendChild(img);

  const size = staticMode ? 28 : 26;
  img.style.width = `${size}px`;
  img.style.height = `${size}px`;

  const x = Math.random() * Math.max(1, w - size);
  const y = Math.random() * Math.max(1, h - size);
  const vx = (Math.random() * 1.5 + 0.6) * (Math.random() < 0.5 ? -1 : 1);
  const vy = (Math.random() * 1.5 + 0.6) * (Math.random() < 0.5 ? -1 : 1);

  sprites.push({ el: img, x, y, vx, vy, size });
}

function removeSprite() {
  const s = sprites.pop();
  if (s && s.el && s.el.parentNode) s.el.parentNode.removeChild(s.el);
}

function updateSprites() {
  if (!spriteEnabled) return;

  const { w, h } = fieldSize();
  if (w <= 0 || h <= 0) return;

  for (const s of sprites) {
    s.x += s.vx * spriteSpeed;
    s.y += s.vy * spriteSpeed;

    if (s.x <= 0) { s.x = 0; s.vx *= -1; }
    if (s.y <= 0) { s.y = 0; s.vy *= -1; }
    if (s.x + s.size >= w) { s.x = w - s.size; s.vx *= -1; }
    if (s.y + s.size >= h) { s.y = h - s.size; s.vy *= -1; }

    s.el.style.transform = `translate(${s.x}px, ${s.y}px)`;
  }
  requestAnimationFrame(updateSprites);
}

function layoutSpritesStatic() {
  const field = document.getElementById("spriteField");
  if (!field) return;
  field.classList.add("static");
  sprites.forEach(s => {
    s.el.style.transform = "none";
    s.el.style.width = "28px";
    s.el.style.height = "28px";
  });
}

function resumeSpriteMotion() {
  const field = document.getElementById("spriteField");
  if (!field) return;
  field.classList.remove("static");
  if (spriteEnabled) updateSprites();
}

function syncSpriteCount(level, upgradeLevel) {
  const target = level + upgradeLevel;
  while (sprites.length < target) addSprite(!spriteEnabled);
  while (sprites.length > target) removeSprite();
  if (!spriteEnabled) layoutSpritesStatic();
}

// ---------------------- 点击批量 ----------------------
async function flushClicks() {
  if (pendingClicks <= 0) return;
  const count = pendingClicks;
  pendingClicks = 0;
  localStorage.setItem("pendingClicks", "0");

  try {
    const data = await post("/api/click-batch/", { count });
    if (data.ok === false) throw new Error();
    localApples = data.apples;
    localTotal = data.apples_total;
    document.getElementById("apples").textContent = formatNumber(data.apples);
    document.getElementById("totalApplesTop").textContent = formatNumber(data.apples_total);
    document.getElementById("clicksTop").textContent = formatNumber(data.clicks);
    currentPerClick = data.per_click;
    currentPerSecond = data.per_second;
    document.getElementById("perClick").textContent = `+${formatNumber(currentPerClick)}`;
    document.getElementById("perSecond").textContent = `+${formatNumber(currentPerSecond)}`;
    const lvl = updateLevel(data.apples_total);
    syncSpriteCount(lvl, currentUpgradeLevel);
    if (data.unlocked && data.unlocked.length) {
      data.unlocked.forEach(a => toast(`成就解锁：${a.name}`));
    }
  } catch {
    pendingClicks += count;
    localStorage.setItem("pendingClicks", String(pendingClicks));
  }
}

// ---------------------- 随机事件倒计时 ----------------------
let buffTimer = null;
function startBuffCountdown(seconds) {
  const el = document.getElementById("buffCountdown");
  if (!el) return;
  el.classList.remove("hidden");
  let remaining = seconds;
  el.textContent = `加成剩余 ${remaining}s`;
  if (buffTimer) clearInterval(buffTimer);
  buffTimer = setInterval(() => {
    remaining -= 1;
    if (remaining <= 0) {
      el.classList.add("hidden");
      clearInterval(buffTimer);
      buffTimer = null;
    } else {
      el.textContent = `加成剩余 ${remaining}s`;
    }
  }, 1000);
}

// ---------------------- 状态同步 ----------------------
async function applyState(data) {
  localApples = data.apples;
  localTotal = data.apples_total;
  currentPerSecond = data.per_second;
  currentPerClick = data.per_click;
  currentUpgradeLevel = data.upgrade_level || currentUpgradeLevel;

  document.getElementById("apples").textContent = formatNumber(data.apples);
  document.getElementById("perSecond").textContent = `+${formatNumber(data.per_second)}`;
  document.getElementById("perClick").textContent = `+${formatNumber(data.per_click)}`;

  document.getElementById("totalApplesTop").textContent = formatNumber(data.apples_total);
  document.getElementById("clicksTop").textContent = formatNumber(data.clicks);

  const lvl = updateLevel(data.apples_total);
  syncSpriteCount(lvl, currentUpgradeLevel);

  if (data.buildings) {
    data.buildings.forEach(b => {
      const priceEl = document.getElementById(`price-${b.key}`);
      const ownedEl = document.getElementById(`owned-${b.key}`);
      const effectEl = document.getElementById(`effect-${b.key}`);
      const effectNextEl = document.getElementById(`effect-next-${b.key}`);
      const card = document.getElementById(`building-${b.key}`);
      if (priceEl) priceEl.textContent = formatNumber(b.price);
      if (ownedEl) ownedEl.textContent = b.amount;
      if (effectEl) effectEl.textContent = `+${formatNumber(b.per_second_total)}/s，+${formatNumber(b.per_click_total)}/点`;
      if (effectNextEl) effectNextEl.textContent = `+${formatNumber(b.per_second_next)}/s，+${formatNumber(b.per_click_next)}/点`;
      if (card) card.dataset.amount = b.amount;
    });
    rebuildStrip();
  }

  const eventBubble = document.getElementById("eventBubble");
  if (data.event && data.event.active) {
    eventBubble.classList.remove("hidden");
    eventBubble.dataset.eventId = data.event.id;
  } else {
    eventBubble.classList.add("hidden");
  }
}

// ---------------------- 本地平滑增长 ----------------------
function startLocalTicker() {
  let last = performance.now();
  function tick(now) {
    if (localApples != null) {
      const dt = (now - last) / 1000;
      const gain = currentPerSecond * dt;
      localApples += gain;
      localTotal += gain;
      popBuffer += gain;
      document.getElementById("apples").textContent = formatNumber(Math.floor(localApples));
      document.getElementById("totalApplesTop").textContent = formatNumber(Math.floor(localTotal));
      popStatusGain();
      const lvl = updateLevel(localTotal);
      syncSpriteCount(lvl, currentUpgradeLevel);
    }
    last = now;
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

document.addEventListener("DOMContentLoaded", async () => {
  formatInitialNumbers();
  rebuildStrip();
  startLocalTicker();
  updateSprites();

  const spriteToggle = document.getElementById("spriteToggle");
  spriteToggle.addEventListener("change", () => {
    spriteEnabled = spriteToggle.checked;
    if (!spriteEnabled) {
      layoutSpritesStatic();
    } else {
      resumeSpriteMotion();
    }
  });

  const spriteSpeedInput = document.getElementById("spriteSpeed");
  spriteSpeed = parseFloat(spriteSpeedInput.value);
  spriteSpeedInput.addEventListener("input", () => {
    spriteSpeed = parseFloat(spriteSpeedInput.value);
  });

  const initialLevel = getLevel(localTotal);
  syncSpriteCount(initialLevel, currentUpgradeLevel);

  const state = await getState();
  await applyState(state);

  setInterval(async () => {
    const s = await getState();
    await applyState(s);
  }, 5000);

  const clickBtn = document.getElementById("clickBtn");
  const sound = document.getElementById("clickSound");

  clickBtn.addEventListener("click", () => {
    clickBtn.classList.add("hit");
    setTimeout(() => clickBtn.classList.remove("hit"), 150);

    pendingClicks += 1;
    const currentClicks = parseNumber(document.getElementById("clicksTop").textContent) + 1;
    document.getElementById("clicksTop").textContent = formatNumber(currentClicks);

    const rect = clickBtn.getBoundingClientRect();
    const x = rect.left + rect.width / 2 + (Math.random() * 40 - 20);
    const y = rect.top + rect.height / 2 + (Math.random() * 40 - 20);
    floatText(`+${formatNumber(currentPerClick)}`, x + 10, y - 20);
    floatImg(x - 10, y + 10);

    if (sound && sound.src) {
      sound.currentTime = 0;
      sound.play().catch(() => {});
    }

    if (!clickTimer) {
      clickTimer = setInterval(async () => {
        await flushClicks();
        if (pendingClicks === 0) {
          clearInterval(clickTimer);
          clickTimer = null;
        }
      }, 600);
    }
  });

  const eventBubble = document.getElementById("eventBubble");
  eventBubble.addEventListener("click", async () => {
    const eventId = eventBubble.dataset.eventId;
    if (!eventId) return;
    const data = await post("/api/event-claim/", { event_id: eventId });
    if (data.ok === false) return toast(data.error || "领取失败", "error");
    toast(`恶作剧加成 x${data.multiplier}`);
    startBuffCountdown(data.seconds);
    eventBubble.classList.add("hidden");
  });

  document.querySelectorAll(".buy-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const key = btn.dataset.key;
      const data = await post("/api/buy/", { key });
      if (data.ok === false) return toast(data.error || "点数不足", "error");

      document.getElementById("apples").textContent = formatNumber(data.apples);
      document.getElementById(`owned-${key}`).textContent = data.amount;
      document.getElementById(`price-${key}`).textContent = formatNumber(data.next_price);
      document.getElementById(`effect-${key}`).textContent = `+${formatNumber(data.per_second_total)}/s，+${formatNumber(data.per_click_total)}/点`;
      document.getElementById(`effect-next-${key}`).textContent = `+${formatNumber(data.per_second_next)}/s，+${formatNumber(data.per_click_next)}/点`;
      document.getElementById(`building-${key}`).dataset.amount = data.amount;
      rebuildStrip();
      flashBuilding(key);

      currentPerSecond = data.per_second;
      currentPerClick = data.per_click;
      document.getElementById("perSecond").textContent = `+${formatNumber(currentPerSecond)}`;
      document.getElementById("perClick").textContent = `+${formatNumber(currentPerClick)}`;
    });
  });

  document.querySelectorAll(".buy-card-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const key = btn.dataset.key;
      const data = await post("/api/upgrade-card/", { key });
      if (data.ok === false) return toast(data.error || "点数不足", "error");
      toast("升级卡购买成功！");
      currentPerSecond = data.per_second;
      currentPerClick = data.per_click;
      document.getElementById("perSecond").textContent = `+${formatNumber(currentPerSecond)}`;
      document.getElementById("perClick").textContent = `+${formatNumber(currentPerClick)}`;
    });
  });

  const upgradeBtn = document.getElementById("upgradeBtn");
  upgradeBtn.addEventListener("click", async () => {
    const data = await post("/api/upgrade/");
    if (data.ok === false) return toast(data.error || "点数不足", "error");

    currentUpgradeLevel = data.upgrade_level;
    document.getElementById("upgradeInfo").textContent = `当前等级：${data.upgrade_level}`;
    document.getElementById("upgradePriceValue").textContent = formatNumber(data.next_price);

    currentPerSecond = data.per_second;
    currentPerClick = data.per_click;
    document.getElementById("perSecond").textContent = `+${formatNumber(currentPerSecond)}`;
    document.getElementById("perClick").textContent = `+${formatNumber(currentPerClick)}`;
  });

  const bgm = document.getElementById("bgm");
  const bgmBtn = document.getElementById("bgmBtn");
  const bgmVol = document.getElementById("bgmVol");

  const savedVol = localStorage.getItem("bgmVol");
  bgm.volume = savedVol ? parseFloat(savedVol) : 0.5;
  bgmVol.value = bgm.volume;

  bgm.muted = true;
  bgm.play().then(() => { bgmBtn.textContent = "暂停BGM"; })
    .catch(() => { bgmBtn.textContent = "播放BGM"; });

  function unlockAudio() {
    bgm.muted = false;
    bgm.volume = parseFloat(bgmVol.value);
    document.removeEventListener("click", unlockAudio);
    document.removeEventListener("keydown", unlockAudio);
  }
  document.addEventListener("click", unlockAudio);
  document.addEventListener("keydown", unlockAudio);

  bgmBtn.addEventListener("click", () => {
    if (bgm.paused) { bgm.play().catch(() => {}); bgmBtn.textContent = "暂停BGM"; }
    else { bgm.pause(); bgmBtn.textContent = "播放BGM"; }
  });

  bgmVol.addEventListener("input", () => {
    bgm.volume = parseFloat(bgmVol.value);
    localStorage.setItem("bgmVol", bgm.volume);
  });

  const achievementBtn = document.getElementById("achievementBtn");
  const achievementPanel = document.getElementById("achievementPanel");
  achievementBtn.addEventListener("click", () => achievementPanel.classList.toggle("hidden"));
});

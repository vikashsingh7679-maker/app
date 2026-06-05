const state = {
  token: localStorage.getItem("rvitm_token"),
  user: JSON.parse(localStorage.getItem("rvitm_user") || "null"),
  view: "dashboard",
  rooms: [],
  bookings: [],
};

const app = document.querySelector("#app");

const api = async (path, options = {}) => {
  const res = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}),
      ...(options.headers || {}),
    },
  });
  const data = await res.json();
  if (!res.ok) throw data;
  return data;
};

function renderLogin() {
  app.innerHTML = `
    <section class="site-landing">
      <header class="site-header">
        <div class="brand">
          <div class="brand-mark">RV</div>
          <div><strong>RVITM Rooms</strong><span>Smart allocation system</span></div>
        </div>
        <nav class="site-links">
          <a href="#rooms-preview">Rooms</a>
          <a href="#workflow-preview">Workflow</a>
          <a href="#login-preview">Login</a>
        </nav>
      </header>
      <section class="site-hero">
        <div class="site-hero-copy">
          <span class="eyebrow">RV Institute of Technology and Management</span>
          <h1>Book classrooms, labs, and seminar halls online.</h1>
          <p>Check availability, send requests, get approvals, and avoid room conflicts through one simple RVITM website.</p>
          <div class="hero-actions">
            <a class="primary link-button" href="#login-preview">Get started</a>
            <a class="ghost link-button" href="#rooms-preview">View rooms</a>
          </div>
        </div>
      </section>
      <section class="website-section" id="rooms-preview">
        <div class="section-heading">
          <span class="eyebrow">Campus spaces</span>
          <h2>Built around RVITM rooms and labs</h2>
        </div>
        <div class="login-gallery" aria-label="RVITM campus references">
          <span style="background-image:url('https://www.rvitm.edu.in/wp-content/uploads/2020/11/Design-and-Analysis-of-Algorithm-Laboratory-2-scaled-1.jpg')"></span>
          <span style="background-image:url('https://www.rvitm.edu.in/wp-content/uploads/2020/08/Microcontroller-and-Embedded-Systems-Lab-1-scaled.jpg')"></span>
          <span style="background-image:url('https://www.rvitm.edu.in/wp-content/uploads/2020/11/electronic-devices-and-instrumentation-lab-1.jpg')"></span>
        </div>
      </section>
      <section class="website-section" id="workflow-preview">
        <div class="section-heading">
          <span class="eyebrow">Same features</span>
          <h2>Simple website workflow</h2>
        </div>
        <div class="feature-grid">
          <article class="panel"><h3>Find rooms</h3><p class="muted">Search by capacity, department, room type, and equipment.</p></article>
          <article class="panel"><h3>Request booking</h3><p class="muted">Submit event details and requirements from one form.</p></article>
          <article class="panel"><h3>Approve requests</h3><p class="muted">Faculty, HOD, and Admin can approve or reject requests.</p></article>
        </div>
      </section>
      <section class="website-section login-section" id="login-preview">
        <div class="section-heading">
          <span class="eyebrow">Demo access</span>
          <h2>Choose a role</h2>
          <p class="muted">Open the full website features for each role.</p>
        </div>
        <div class="role-grid">
          ${["student", "faculty", "hod", "admin"]
            .map((role) => `<button class="role-btn" data-role="${role}">Login as ${role.toUpperCase()}</button>`)
            .join("")}
        </div>
      </section>
    </section>
  `;
  document.querySelectorAll("[data-role]").forEach((btn) =>
    btn.addEventListener("click", async () => {
      const data = await api("/api/login", {
        method: "POST",
        body: JSON.stringify({ role: btn.dataset.role }),
      });
      state.token = data.token;
      state.user = data.user;
      localStorage.setItem("rvitm_token", state.token);
      localStorage.setItem("rvitm_user", JSON.stringify(state.user));
      await boot();
    })
  );
}

function shell(title, body) {
  app.innerHTML = `
    <section class="shell website-shell">
      <header class="sidebar website-nav">
        <div class="brand">
          <div class="brand-mark">RV</div>
          <div><strong>RVITM Rooms</strong><span>${state.user.role.toUpperCase()}</span></div>
        </div>
        <nav class="nav">
          ${navButton("dashboard", "Dashboard")}
          ${navButton("rooms", "Rooms")}
          ${navButton("request", "New Booking")}
          ${navButton("approvals", "Approvals")}
          ${navButton("notifications", "Notifications")}
          ${navButton("admin", "Admin & Analytics")}
        </nav>
        <div class="user-pill">
          <span>${state.user.name}</span>
          <button class="ghost" id="logout">Logout</button>
        </div>
      </header>
      <section class="website-page-hero">
        <div>
          <span class="eyebrow">RVITM Smart Room Allocation</span>
          <h1>${title}</h1>
          <p>Same room booking and approval features, presented as a website with RVITM visual references.</p>
        </div>
      </section>
      <section class="content website-content">
        <div class="topbar">
          <div><h1>${title}</h1><span class="muted">RV Institute of Technology and Management</span></div>
        </div>
        ${body}
      </section>
    </section>
  `;
  document.querySelectorAll("[data-view]").forEach((btn) =>
    btn.addEventListener("click", () => {
      state.view = btn.dataset.view;
      render();
    })
  );
  document.querySelector("#logout").addEventListener("click", () => {
    localStorage.clear();
    state.token = null;
    state.user = null;
    renderLogin();
  });
}

function navButton(view, label) {
  return `<button data-view="${view}" class="${state.view === view ? "active" : ""}">${label}</button>`;
}

async function loadCore() {
  const [rooms, bookings] = await Promise.all([api("/api/rooms"), api("/api/bookings")]);
  state.rooms = rooms.rooms;
  state.bookings = bookings.bookings;
}

async function boot() {
  if (!state.token) return renderLogin();
  try {
    const me = await api("/api/me");
    state.user = me.user;
    await loadCore();
    render();
  } catch {
    localStorage.clear();
    renderLogin();
  }
}

function render() {
  const views = {
    dashboard: renderDashboard,
    rooms: renderRooms,
    request: renderRequest,
    approvals: renderApprovals,
    notifications: renderNotifications,
    admin: renderAdmin,
  };
  views[state.view]();
}

async function renderDashboard() {
  const data = await api("/api/dashboard");
  shell(
    "Dashboard",
    `
    <div class="notice">Added: login roles, live room status, booking workflow, approval queue, notifications, and admin analytics.</div>
    <div class="grid stats">
      ${stat("Rooms", data.stats.rooms)}
      ${stat("Available", data.stats.available)}
      ${stat("Pending", data.stats.pending)}
      ${stat("Approved", data.stats.approved)}
    </div>
    <div class="panel" style="margin-top:16px">
      <h2>Upcoming Events</h2>
      <div class="list">
        ${data.upcoming
          .map(
            (b) => `
            <div class="booking">
              <h3>${b.event_name}</h3>
              <p class="muted">${b.room_name} • ${b.event_date} • ${b.start_time}-${b.end_time}</p>
              <span class="status ${b.status}">${b.status}</span>
            </div>`
          )
          .join("")}
      </div>
    </div>`
  );
}

function stat(label, value) {
  return `<div class="panel stat"><span class="muted">${label}</span><strong>${value}</strong></div>`;
}

function renderRooms(filtered = state.rooms) {
  shell(
    "Room Availability",
    `
    <div class="filters">
      <input id="q" placeholder="Search room, department, equipment" />
      <select id="type">
        <option value="">All room types</option>
        <option>Classroom</option>
        <option>Computer Lab</option>
        <option>Electronics Lab</option>
        <option>Seminar Hall</option>
        <option>Conference Room</option>
      </select>
      <input id="capacity" type="number" min="0" placeholder="Min capacity" />
      <button class="primary" id="filter">Search</button>
    </div>
    <div class="grid cards">
      ${filtered.map(roomCard).join("")}
    </div>`
  );
  document.querySelector("#filter").addEventListener("click", async () => {
    const q = document.querySelector("#q").value;
    const type = document.querySelector("#type").value;
    const capacity = document.querySelector("#capacity").value;
    const data = await api(`/api/rooms?q=${encodeURIComponent(q)}&type=${encodeURIComponent(type)}&capacity=${capacity}`);
    renderRooms(data.rooms);
  });
}

function roomCard(room) {
  return `
    <article class="room">
      <img src="${room.image}" alt="${room.name}" />
      <div class="room-body">
        <h3>${room.name}</h3>
        <p class="muted">${room.building}, Floor ${room.floor} • ${room.department}</p>
        <div class="meta">
          <span class="tag">${room.type}</span>
          <span class="tag">${room.capacity} seats</span>
          <span class="status ${room.status}">${room.status}</span>
        </div>
        <p class="muted">${room.equipment}</p>
        <button class="primary" onclick="quickBook(${room.id})">Request room</button>
      </div>
    </article>
  `;
}

function quickBook(roomId) {
  state.view = "request";
  renderRequest(roomId);
}

function renderRequest(selectedRoomId = "") {
  shell(
    "New Booking Request",
    `
    <form class="panel form-grid" id="bookingForm">
      <input name="event_name" placeholder="Event name" required />
      <select name="room_id" required>
        <option value="">Select room</option>
        ${state.rooms.map((r) => `<option value="${r.id}" ${r.id === selectedRoomId ? "selected" : ""}>${r.name} (${r.capacity})</option>`).join("")}
      </select>
      <input name="department" value="${state.user.department}" placeholder="Department" required />
      <input name="participants" type="number" min="1" placeholder="Expected participants" required />
      <input name="event_date" type="date" required />
      <input name="start_time" type="time" required />
      <input name="end_time" type="time" required />
      <input name="requirements" placeholder="Projector, WiFi, Sound..." />
      <textarea class="full" name="purpose" rows="4" placeholder="Purpose" required></textarea>
      <button class="primary full">Submit request</button>
    </form>
    <div id="formMsg"></div>`
  );
  document.querySelector("#bookingForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = Object.fromEntries(new FormData(event.target));
    form.room_id = Number(form.room_id);
    form.participants = Number(form.participants);
    try {
      await api("/api/bookings", { method: "POST", body: JSON.stringify(form) });
      await loadCore();
      document.querySelector("#formMsg").innerHTML = `<div class="notice">Request submitted to faculty approval.</div>`;
      event.target.reset();
    } catch (error) {
      document.querySelector("#formMsg").innerHTML = `<div class="notice">${error.error || "Could not submit."} ${
        error.alternatives ? "Try: " + error.alternatives.map((r) => r.name).join(", ") : ""
      }</div>`;
    }
  });
}

function renderApprovals() {
  const canApprove = ["faculty", "hod", "admin"].includes(state.user.role);
  shell(
    "Approvals",
    `
    <div class="list">
      ${state.bookings
        .map(
          (b) => `
        <div class="booking">
          <h3>${b.event_name}</h3>
          <p class="muted">${b.room_name} • ${b.event_date} • ${b.start_time}-${b.end_time} • ${b.participants} participants</p>
          <div class="meta">
            <span class="status ${b.status}">${b.status}</span>
            <span class="tag">Stage: ${b.current_stage}</span>
          </div>
          <p>${b.purpose}</p>
          ${canApprove && b.status === "pending" ? `
            <div class="actions">
              <button class="primary" onclick="decision(${b.id}, 'approve')">Approve</button>
              <button class="danger" onclick="decision(${b.id}, 'reject')">Reject</button>
            </div>` : ""}
        </div>`
        )
        .join("")}
    </div>`
  );
}

async function decision(id, action) {
  await api(`/api/bookings/${id}/${action}`, {
    method: "POST",
    body: JSON.stringify({ remarks: action === "approve" ? "Looks good" : "Not available" }),
  });
  await loadCore();
  renderApprovals();
}

async function renderNotifications() {
  const data = await api("/api/notifications");
  shell(
    "Notifications",
    `<div class="list">
      ${data.notifications
        .map((n) => `<div class="booking"><h3>${n.title}</h3><p class="muted">${n.message}</p></div>`)
        .join("")}
    </div>`
  );
}

async function renderAdmin() {
  let analytics = { room_usage: [], department_usage: [] };
  if (["hod", "admin"].includes(state.user.role)) analytics = await api("/api/analytics");
  shell(
    "Admin & Analytics",
    `
    ${!["hod", "admin"].includes(state.user.role) ? `<div class="notice">Admin analytics are available for HOD and Admin roles.</div>` : ""}
    <div class="grid" style="grid-template-columns: 1fr 1fr">
      <div class="panel">
        <h2>Room Usage</h2>
        <div class="chart-row">${analytics.room_usage.map((r) => bar(r.name, r.bookings)).join("")}</div>
      </div>
      <div class="panel">
        <h2>Department Usage</h2>
        <div class="chart-row">${analytics.department_usage.map((r) => bar(r.department, r.bookings)).join("")}</div>
      </div>
    </div>
    ${
      state.user.role === "admin"
        ? `<form class="panel form-grid" id="roomForm" style="margin-top:16px">
            <h2 class="full">Add Room</h2>
            <input name="name" placeholder="Room name" required />
            <input name="building" placeholder="Building" required />
            <input name="floor" placeholder="Floor" required />
            <input name="department" placeholder="Department" required />
            <input name="type" placeholder="Type" required />
            <input name="capacity" type="number" placeholder="Capacity" required />
            <input class="full" name="equipment" placeholder="Equipment" />
            <button class="primary full">Add room</button>
          </form>`
        : ""
    }`
  );
  const form = document.querySelector("#roomForm");
  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const payload = Object.fromEntries(new FormData(event.target));
      payload.capacity = Number(payload.capacity);
      await api("/api/admin/rooms", { method: "POST", body: JSON.stringify(payload) });
      await loadCore();
      renderAdmin();
    });
  }
}

function bar(label, value) {
  const width = Math.max(8, Number(value) * 35);
  return `<div class="bar"><span>${label}</span><div><div class="bar-fill" style="width:${width}px"></div></div><strong>${value}</strong></div>`;
}

boot();

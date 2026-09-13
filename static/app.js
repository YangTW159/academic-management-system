const appMeta = window.APP_META || { appName: "校园综合事务管理数据库系统" };

const state = {
  user: null,
  activeView: "dashboard",
  filters: {},
  currentRows: [],
  lookups: {},
  currentDashboard: null,
  modal: null,
};

const sampleAccounts = [
  { label: "管理员", username: "admin", password: "123456", note: "系统总控与数据维护" },
  { label: "教师", username: "t001", password: "123456", note: "课程与成绩管理" },
  { label: "学生", username: "s2024001", password: "123456", note: "选课、查成绩与查宿舍" },
  { label: "宿管", username: "dm01", password: "123456", note: "宿舍与公告管理" },
];

const roleShortcuts = {
  admin: ["维护学生档案", "发布校园通知", "调整宿舍分配", "查看系统日志"],
  teacher: ["查看授课课程", "录入课程成绩", "追踪课程通知"],
  student: ["查看个人课表", "查询成绩分析", "确认宿舍信息"],
  dormManager: ["维护宿舍信息", "查看床位情况", "发布宿舍通知"],
};

const els = {
  healthBadge: document.getElementById("health-badge"),
  healthText: document.getElementById("health-text"),
  healthVersion: document.getElementById("health-version"),
  sessionText: document.getElementById("session-text"),
  authCard: document.getElementById("auth-card"),
  sessionCard: document.getElementById("session-card"),
  loginForm: document.getElementById("login-form"),
  username: document.getElementById("username"),
  password: document.getElementById("password"),
  loginSubmit: document.getElementById("login-submit"),
  loginMessage: document.getElementById("login-message"),
  sampleAccounts: document.getElementById("sample-accounts"),
  roleChip: document.getElementById("role-chip"),
  userDisplayName: document.getElementById("user-display-name"),
  userMeta: document.getElementById("user-meta"),
  shortcutList: document.getElementById("shortcut-list"),
  logoutBtn: document.getElementById("logout-btn"),
  navMenu: document.getElementById("nav-menu"),
  viewKicker: document.getElementById("view-kicker"),
  viewTitle: document.getElementById("view-title"),
  viewDescription: document.getElementById("view-description"),
  refreshView: document.getElementById("refresh-view"),
  dashboardView: document.getElementById("dashboard-view"),
  dashboardHero: document.getElementById("dashboard-hero"),
  summaryGrid: document.getElementById("summary-grid"),
  chartGrid: document.getElementById("chart-grid"),
  latestNotices: document.getElementById("latest-notices"),
  recentLogs: document.getElementById("recent-logs"),
  logBadge: document.getElementById("log-badge"),
  workspaceView: document.getElementById("workspace-view"),
  searchForm: document.getElementById("search-form"),
  searchInput: document.getElementById("search-input"),
  resetSearch: document.getElementById("reset-search"),
  workspaceActions: document.getElementById("workspace-actions"),
  workspaceStats: document.getElementById("workspace-stats"),
  tableTitle: document.getElementById("table-title"),
  tableBadge: document.getElementById("table-badge"),
  tableWrap: document.getElementById("table-wrap"),
  insightPanel: document.getElementById("insight-panel"),
  modalOverlay: document.getElementById("modal-overlay"),
  modalTitle: document.getElementById("modal-title"),
  modalForm: document.getElementById("modal-form"),
  modalMessage: document.getElementById("modal-message"),
  modalClose: document.getElementById("modal-close"),
  modalCancel: document.getElementById("modal-cancel"),
  modalSubmit: document.getElementById("modal-submit"),
  toastRoot: document.getElementById("toast-root"),
};

const viewConfigs = {
  dashboard: {
    label: "首页总览",
    kicker: "Overview",
    navNote: "统计与快捷入口",
    description: () => "登录后可查看校园事务总览、业务统计与角色化功能入口。",
  },
  students: {
    label: "学生档案",
    kicker: "Students",
    navNote: "档案与归属信息",
    description: (user) =>
      user.role === "admin"
        ? "维护学生基础信息、班级归属、宿舍分配与在读状态。"
        : user.role === "student"
          ? "查看个人学籍档案、班级信息与宿舍分配结果。"
          : "查看当前角色可访问的学生信息与业务关联数据。",
    searchPlaceholder: "输入学号、姓名或班级进行查询",
    searchable: true,
    load: (keyword) => loadWithKeyword("/api/students", keyword),
    columns: [
      { key: "sno", label: "学号" },
      { key: "sname", label: "姓名" },
      { key: "class_name", label: "班级" },
      { key: "major", label: "专业" },
      { key: "dorm_summary", label: "宿舍" },
      { key: "status", label: "状态" },
    ],
    statsBuilder: buildStudentStats,
    insightBuilder: buildStudentInsights,
    toolbarActions: (user) =>
      user.role === "admin" ? [{ id: "add-student", label: "新增学生", kind: "primary" }] : [],
    rowActions: (user) =>
      user.role === "admin"
        ? [
            { id: "edit-student", label: "编辑", kind: "primary" },
            { id: "delete-student", label: "删除", kind: "danger" },
          ]
        : [],
  },
  courses: {
    label: "课程中心",
    kicker: "Courses",
    navNote: "课程与授课安排",
    description: (user) =>
      user.role === "admin"
        ? "维护课程基础信息、开课状态、教室与授课教师安排。"
        : user.role === "teacher"
          ? "查看自己的授课课程与学生选课规模。"
          : "查看当前已选课程、教师安排与上课时间地点。",
    searchPlaceholder: "输入课程号或课程名称查询",
    searchable: true,
    load: (keyword) => loadWithKeyword("/api/courses", keyword),
    columns: [
      { key: "cno", label: "课程号" },
      { key: "cname", label: "课程名称" },
      { key: "teacher_name", label: "授课教师" },
      { key: "schedule_info", label: "上课时间" },
      { key: "classroom", label: "教室" },
      { key: "selected_count", label: "选课人数" },
      { key: "status", label: "状态" },
    ],
    statsBuilder: buildCourseStats,
    insightBuilder: buildCourseInsights,
    toolbarActions: (user) =>
      user.role === "admin" ? [{ id: "add-course", label: "新增课程", kind: "primary" }] : [],
    rowActions: (user) =>
      user.role === "admin"
        ? [
            { id: "edit-course", label: "编辑", kind: "primary" },
            { id: "delete-course", label: "删除", kind: "danger" },
          ]
        : [],
  },
  dormitories: {
    label: "宿舍管理",
    kicker: "Dormitories",
    navNote: "宿舍与床位信息",
    description: (user) =>
      user.role === "dormManager"
        ? "维护本人负责楼栋的宿舍、床位与入住状态。"
        : user.role === "admin"
          ? "统一查看并维护全校宿舍与宿管分配情况。"
          : "查看宿舍基础信息与床位使用情况。",
    searchable: false,
    load: () => fetchJson("/api/dormitories"),
    columns: [
      { key: "dorm_id", label: "宿舍号" },
      { key: "building", label: "楼栋" },
      { key: "room", label: "房间" },
      { key: "manager_name", label: "宿管" },
      { key: "cur_num", label: "已住/容量", format: (_, row) => `${row.cur_num}/${row.max_num}` },
      { key: "available_beds", label: "空床位" },
      { key: "status", label: "状态" },
    ],
    statsBuilder: buildDormStats,
    insightBuilder: buildDormInsights,
    toolbarActions: (user) =>
      ["admin", "dormManager"].includes(user.role)
        ? [{ id: "add-dormitory", label: "新增宿舍", kind: "primary" }]
        : [],
    rowActions: (user) =>
      ["admin", "dormManager"].includes(user.role)
        ? [{ id: "edit-dormitory", label: "编辑", kind: "primary" }]
        : [],
  },
  notices: {
    label: "通知公告",
    kicker: "Notices",
    navNote: "按角色可见范围展示",
    description: (user) =>
      ["admin", "teacher", "dormManager"].includes(user.role)
        ? "查看、发布并维护当前角色可管理的公告信息。"
        : "查看与你身份和范围匹配的最新校园通知。",
    searchPlaceholder: "输入标题或正文关键字查询",
    searchable: true,
    load: (keyword) => loadWithKeyword("/api/notices", keyword),
    columns: [
      { key: "title", label: "标题" },
      { key: "category", label: "分类" },
      { key: "scope", label: "可见范围" },
      { key: "publisher", label: "发布人" },
      { key: "publish_time", label: "发布时间" },
      { key: "pinned", label: "置顶", format: (value) => (Number(value) ? "是" : "否") },
    ],
    statsBuilder: buildNoticeStats,
    insightBuilder: buildNoticeInsights,
    toolbarActions: (user) =>
      ["admin", "teacher", "dormManager"].includes(user.role)
        ? [{ id: "add-notice", label: "发布公告", kind: "primary" }]
        : [],
    rowActions: (user, row) => {
      if (!["admin", "teacher", "dormManager"].includes(user.role)) {
        return [];
      }
      if (user.role !== "admin" && row.publisher !== user.display_name) {
        return [];
      }
      return [
        { id: "edit-notice", label: "编辑", kind: "primary" },
        { id: "delete-notice", label: "删除", kind: "danger" },
      ];
    },
  },
  enrollments: {
    label: "选课与成绩",
    kicker: "Enrollments",
    navNote: "选课记录与成绩录入",
    description: (user) =>
      user.role === "teacher"
        ? "维护自己授课课程的成绩，并查看学生选课情况。"
        : user.role === "student"
          ? "查看个人选课记录、课程成绩，并可发起选课或退课。"
          : "统一维护选课记录、成绩数据与课程分布情况。",
    searchable: false,
    load: () => fetchJson("/api/enrollments"),
    columns: [
      { key: "sno", label: "学号" },
      { key: "student_name", label: "学生" },
      { key: "cno", label: "课程号" },
      { key: "course_name", label: "课程名称" },
      { key: "score", label: "成绩", format: (value) => (value === null ? "待录入" : value) },
      { key: "gpa_point", label: "绩点", format: (value) => (value === null ? "-" : value) },
    ],
    statsBuilder: buildEnrollmentStats,
    insightBuilder: buildEnrollmentInsights,
    toolbarActions: (user) =>
      ["admin", "student"].includes(user.role)
        ? [{ id: "add-enrollment", label: user.role === "student" ? "我要选课" : "新增选课", kind: "primary" }]
        : [],
    rowActions: (user) => {
      if (user.role === "teacher") {
        return [{ id: "edit-enrollment", label: "录入成绩", kind: "primary" }];
      }
      if (user.role === "admin") {
        return [
          { id: "edit-enrollment", label: "编辑成绩", kind: "primary" },
          { id: "delete-enrollment", label: "删除", kind: "danger" },
        ];
      }
      if (user.role === "student") {
        return [{ id: "delete-enrollment", label: "退课", kind: "danger" }];
      }
      return [];
    },
  },
  logs: {
    label: "系统日志",
    kicker: "Logs",
    navNote: "管理员专属日志追踪",
    description: () => "查看登录、数据维护、公告发布等关键操作日志。",
    searchable: false,
    load: () => fetchJson("/api/logs"),
    columns: [
      { key: "log_id", label: "日志号" },
      { key: "actor", label: "操作人" },
      { key: "action_name", label: "动作" },
      { key: "target_name", label: "目标" },
      { key: "created_at", label: "时间" },
    ],
    statsBuilder: buildLogStats,
    insightBuilder: buildLogInsights,
    toolbarActions: () => [],
    rowActions: () => [],
  },
};

const viewAccessMap = {
  admin: ["dashboard", "students", "courses", "dormitories", "notices", "enrollments", "logs"],
  teacher: ["dashboard", "students", "courses", "notices", "enrollments"],
  student: ["dashboard", "students", "courses", "dormitories", "notices", "enrollments"],
  dormManager: ["dashboard", "students", "dormitories", "notices"],
};

const lookupLoaders = {
  classes: () => fetchJson("/api/classes"),
  teachers: () => fetchJson("/api/teachers"),
  dormManagers: () => fetchJson("/api/dorm-managers"),
  dormitories: () => fetchJson("/api/dormitories"),
  courseCatalog: () => fetchJson("/api/course-catalog"),
  students: () => fetchJson("/api/students"),
};

init();

function init() {
  document.title = appMeta.appName;
  renderSampleAccounts();
  bindEvents();
  renderNav();
  refreshHealth();
  refreshSession();
}

function bindEvents() {
  els.loginForm.addEventListener("submit", handleLogin);
  els.logoutBtn.addEventListener("click", handleLogout);
  els.refreshView.addEventListener("click", () => activateView(state.activeView, true));
  els.searchForm.addEventListener("submit", handleSearch);
  els.resetSearch.addEventListener("click", resetSearch);
  els.navMenu.addEventListener("click", handleNavClick);
  els.workspaceActions.addEventListener("click", handleToolbarAction);
  els.tableWrap.addEventListener("click", handleTableAction);
  els.modalClose.addEventListener("click", closeModal);
  els.modalCancel.addEventListener("click", closeModal);
  els.modalSubmit.addEventListener("click", submitModal);
  els.modalOverlay.addEventListener("click", (event) => {
    if (event.target === els.modalOverlay) {
      closeModal();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !els.modalOverlay.classList.contains("hidden")) {
      closeModal();
    }
  });
}

async function refreshHealth() {
  try {
    const data = await fetchJson("/api/health");
    els.healthBadge.className = "badge badge-accent";
    els.healthBadge.textContent = "运行正常";
    els.healthText.textContent = data.message || "数据库连接正常";
    els.healthVersion.textContent = data.version || "未知";
  } catch (error) {
    els.healthBadge.className = "badge badge-danger";
    els.healthBadge.textContent = "连接异常";
    els.healthText.textContent = "连接失败";
    els.healthVersion.textContent = error.message;
  }
}

async function refreshSession() {
  try {
    const session = await fetchJson("/api/session");
    if (session.authenticated) {
      state.user = session.user;
      updateAuthUi();
      renderNav();
      await activateView(ensureAllowedView(state.activeView), true);
      return;
    }
  } catch (error) {
    showToast(error.message, "error");
  }

  state.user = null;
  state.lookups = {};
  updateAuthUi();
  renderNav();
  await activateView("dashboard", true);
}

async function handleLogin(event) {
  event.preventDefault();
  els.loginMessage.textContent = "";
  setButtonBusy(els.loginSubmit, true, "登录中...");
  try {
    const data = await fetchJson("/api/login", {
      method: "POST",
      body: JSON.stringify({
        username: els.username.value.trim(),
        password: els.password.value,
      }),
    });
    state.user = data.user;
    state.lookups = {};
    updateAuthUi();
    renderNav();
    await activateView("dashboard", true);
    showToast(`欢迎回来，${data.user.display_name}`, "success");
  } catch (error) {
    els.loginMessage.textContent = error.message;
    showToast(error.message, "error");
  } finally {
    setButtonBusy(els.loginSubmit, false, "登录系统");
  }
}

async function handleLogout() {
  try {
    await fetchJson("/api/logout", { method: "POST" });
  } catch (error) {
    showToast(error.message, "error");
    return;
  }

  state.user = null;
  state.lookups = {};
  state.currentDashboard = null;
  state.currentRows = [];
  state.filters = {};
  updateAuthUi();
  renderNav();
  await activateView("dashboard", true);
  showToast("已退出登录", "info");
}

function updateAuthUi() {
  const user = state.user;
  const shortcuts = user ? roleShortcuts[user.role] || [] : [];

  els.authCard.classList.toggle("hidden", Boolean(user));
  els.sessionCard.classList.toggle("hidden", !user);

  if (!user) {
    els.sessionText.textContent = "未登录";
    els.userDisplayName.textContent = "访客";
    els.userMeta.textContent = "请先登录后查看系统数据";
    els.roleChip.textContent = "访客";
    els.roleChip.className = "badge badge-muted";
    renderShortcutList(shortcuts);
    return;
  }

  els.sessionText.textContent = `${user.role_label} · ${user.display_name}`;
  els.userDisplayName.textContent = user.display_name;
  els.userMeta.textContent = `${user.role_label} | 账号：${user.username}`;
  els.roleChip.textContent = user.role_label;
  els.roleChip.className = "badge badge-accent";
  renderShortcutList(shortcuts);
}

function renderShortcutList(items) {
  if (!items.length) {
    els.shortcutList.innerHTML = "<li>登录后显示角色快捷能力</li>";
    return;
  }
  els.shortcutList.innerHTML = items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderSampleAccounts() {
  els.sampleAccounts.innerHTML = sampleAccounts
    .map(
      (account) => `
        <button class="sample-account" type="button" data-username="${account.username}" data-password="${account.password}">
          <strong>${escapeHtml(account.label)}</strong>
          <span>${escapeHtml(account.username)} / ${escapeHtml(account.password)}</span>
          <span>${escapeHtml(account.note)}</span>
        </button>
      `
    )
    .join("");

  els.sampleAccounts.addEventListener("click", (event) => {
    const button = event.target.closest(".sample-account");
    if (!button) {
      return;
    }
    els.username.value = button.dataset.username || "";
    els.password.value = button.dataset.password || "";
    els.loginMessage.textContent = "示例账号已填入，可直接登录体验。";
  });
}

function renderNav() {
  const allowedViews = getAllowedViews();
  els.navMenu.innerHTML = allowedViews
    .map((viewId) => {
      const config = viewConfigs[viewId];
      const activeClass = state.activeView === viewId ? "active" : "";
      return `
        <button class="nav-item ${activeClass}" type="button" data-view="${viewId}">
          <div>
            <strong>${escapeHtml(config.label)}</strong>
            <small>${escapeHtml(config.navNote)}</small>
          </div>
          <span class="badge badge-outline">${escapeHtml(config.kicker)}</span>
        </button>
      `;
    })
    .join("");
}

function getAllowedViews() {
  if (!state.user) {
    return ["dashboard"];
  }
  return viewAccessMap[state.user.role] || ["dashboard"];
}

function ensureAllowedView(viewId) {
  return getAllowedViews().includes(viewId) ? viewId : "dashboard";
}

async function activateView(viewId, force = false) {
  const safeView = ensureAllowedView(viewId);
  state.activeView = safeView;
  renderNav();
  updateFrameMeta(safeView);

  if (safeView === "dashboard") {
    els.dashboardView.classList.remove("hidden");
    els.workspaceView.classList.add("hidden");
    await loadDashboard(force);
    return;
  }

  els.dashboardView.classList.add("hidden");
  els.workspaceView.classList.remove("hidden");
  await loadModule(safeView, force);
}

function updateFrameMeta(viewId) {
  const config = viewConfigs[viewId];
  els.viewKicker.textContent = config.kicker;
  els.viewTitle.textContent = config.label;
  els.viewDescription.textContent = state.user ? config.description(state.user) : config.description();
}

async function loadDashboard() {
  if (!state.user) {
    renderDashboardLocked();
    return;
  }

  try {
    const data = await fetchJson("/api/dashboard");
    state.currentDashboard = data;
    renderShortcutList(data.shortcuts || roleShortcuts[state.user.role] || []);
    renderDashboard(data);
  } catch (error) {
    renderDashboardError(error.message);
    showToast(error.message, "error");
  }
}

function renderDashboardLocked() {
  els.dashboardHero.innerHTML = `
    <div class="hero-main">
      <div>
        <p class="eyebrow">Ready To Launch</p>
        <h3>登录后开启校园事务总览</h3>
        <p>当前页面已经接通数据库接口。使用左侧示例账号登录后，即可查看统计图表、公告、业务数据与角色化操作入口。</p>
      </div>
      <div class="badge badge-outline">未登录</div>
    </div>
    <div class="hero-highlights">
      <div class="hero-card"><span>体验入口</span><strong>4 类角色</strong><small>管理员、教师、学生、宿管</small></div>
      <div class="hero-card"><span>业务范围</span><strong>6 大模块</strong><small>档案、课程、宿舍、公告、选课、日志</small></div>
      <div class="hero-card"><span>系统形态</span><strong>可运行</strong><small>Flask + MySQL + 单页前端</small></div>
    </div>
  `;
  els.summaryGrid.innerHTML = "";
  els.chartGrid.innerHTML = "";
  els.latestNotices.innerHTML = `<div class="empty-state">登录后查看公告动态。</div>`;
  els.recentLogs.innerHTML = `<div class="empty-state">登录后查看角色相关操作日志。</div>`;
  els.logBadge.textContent = "登录后展示";
}

function renderDashboardError(message) {
  els.dashboardHero.innerHTML = `
    <div class="hero-main">
      <div>
        <p class="eyebrow">Dashboard Error</p>
        <h3>总览数据暂时不可用</h3>
        <p>${escapeHtml(message)}</p>
      </div>
      <div class="badge badge-danger">加载失败</div>
    </div>
  `;
  els.summaryGrid.innerHTML = "";
  els.chartGrid.innerHTML = "";
  els.latestNotices.innerHTML = `<div class="empty-state">请刷新后重试。</div>`;
  els.recentLogs.innerHTML = `<div class="empty-state">请刷新后重试。</div>`;
}

function renderDashboard(data) {
  const summary = data.summary || {};
  const user = state.user;
  const shortcuts = data.shortcuts || roleShortcuts[user.role] || [];
  els.dashboardHero.innerHTML = `
    <div class="hero-main">
      <div>
        <p class="eyebrow">${escapeHtml(user.role_label)} Workspace</p>
        <h3>${escapeHtml(user.display_name)}，欢迎回来</h3>
        <p>当前以 ${escapeHtml(user.role_label)} 身份使用 ${escapeHtml(appMeta.appName)}。左侧模块会按照角色权限自动收敛，避免越权操作。</p>
      </div>
      <div class="badge badge-outline">${escapeHtml(user.username)}</div>
    </div>
    <div class="hero-highlights">
      ${buildHeroCard("当前角色", user.role_label, "基于登录身份自动切换可见功能")}
      ${buildHeroCard("学生总量", summary.total_students || 0, "覆盖学生档案、班级与宿舍归属")}
      ${buildHeroCard("开课课程", summary.open_courses || 0, "配合选课记录、成绩录入与课程统计")}
      ${buildHeroCard("快捷能力", shortcuts.length, shortcuts.join(" / "))}
    </div>
  `;

  const dashboardMetrics = [
    { label: "学生总数", value: summary.total_students || 0 },
    { label: "在读学生", value: summary.active_students || 0 },
    { label: "课程总数", value: summary.total_courses || 0 },
    { label: "开课课程", value: summary.open_courses || 0 },
    { label: "宿舍总数", value: summary.total_dorms || 0 },
    { label: "床位利用率", value: `${summary.bed_usage_rate || 0}%` },
    { label: "公告数量", value: summary.total_notices || 0 },
  ];

  els.summaryGrid.innerHTML = dashboardMetrics
    .map(
      (item) => `
        <article class="summary-card">
          <span>${escapeHtml(item.label)}</span>
          <strong>${escapeHtml(String(item.value))}</strong>
        </article>
      `
    )
    .join("");

  const charts = data.charts || {};
  els.chartGrid.innerHTML = [
    renderChartCard("班级人数分布", charts.class_distribution, "人"),
    renderChartCard("课程平均成绩", charts.course_scores, "分"),
    renderChartCard("公告分类分布", charts.notice_stats, "条"),
  ].join("");

  els.latestNotices.innerHTML = renderNoticeList(data.latest_notices || []);
  els.recentLogs.innerHTML = renderLogList(data.recent_logs || []);
  els.logBadge.textContent = user.role === "admin" ? "全局日志" : "我的日志";
}

function buildHeroCard(label, value, note) {
  return `
    <div class="hero-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(String(value))}</strong>
      <small>${escapeHtml(note)}</small>
    </div>
  `;
}

function renderChartCard(title, items = [], suffix = "") {
  const values = items.map((item) => normalizeNumber(item.value));
  const max = Math.max(...values, 0);
  const rows = items.length
    ? items
        .map((item) => {
          const value = normalizeNumber(item.value);
          const width = max ? Math.max((value / max) * 100, 6) : 6;
          return `
            <div class="chart-row">
              <div class="chart-label">
                <span>${escapeHtml(item.label)}</span>
                <strong>${escapeHtml(String(item.value))}${escapeHtml(suffix)}</strong>
              </div>
              <div class="bar-track">
                <div class="bar-fill" style="width:${width}%"></div>
              </div>
            </div>
          `;
        })
        .join("")
    : `<div class="empty-state">暂无图表数据</div>`;

  return `
    <article class="panel chart-card">
      <div class="panel-head">
        <h3>${escapeHtml(title)}</h3>
        <span class="badge badge-outline">${items.length} 项</span>
      </div>
      <div class="chart-bars">${rows}</div>
    </article>
  `;
}

function renderNoticeList(items) {
  if (!items.length) {
    return `<div class="empty-state">暂无公告</div>`;
  }
  return items
    .map(
      (item) => `
        <article class="stack-item">
          <strong>${escapeHtml(item.title)}</strong>
          <p>${escapeHtml(item.content)}</p>
          <div class="stack-meta">
            <span>${escapeHtml(item.category)}</span>
            <span>${escapeHtml(item.scope)}</span>
            <span>${escapeHtml(item.publisher)}</span>
            <span>${escapeHtml(item.publish_time)}</span>
          </div>
        </article>
      `
    )
    .join("");
}

function renderLogList(items) {
  if (!items.length) {
    return `<div class="empty-state">暂无日志记录</div>`;
  }
  return items
    .map(
      (item) => `
        <article class="stack-item">
          <strong>${escapeHtml(item.action_name)}</strong>
          <p>${escapeHtml(item.actor)} 对 ${escapeHtml(item.target_name)} 执行了操作。</p>
          <div class="stack-meta">
            <span>#${escapeHtml(String(item.log_id))}</span>
            <span>${escapeHtml(item.created_at)}</span>
          </div>
        </article>
      `
    )
    .join("");
}

async function loadModule(viewId) {
  if (!state.user) {
    renderModuleLocked();
    return;
  }

  const config = viewConfigs[viewId];
  const keyword = state.filters[viewId] || "";
  els.searchInput.value = keyword;
  els.searchInput.placeholder = config.searchPlaceholder || "当前模块暂不支持搜索";
  els.searchForm.classList.toggle("hidden", !config.searchable);

  try {
    const rows = await config.load(keyword);
    state.currentRows = Array.isArray(rows) ? rows : [];
    renderModule(viewId, state.currentRows);
  } catch (error) {
    renderModuleError(error.message);
    showToast(error.message, "error");
  }
}

function renderModuleLocked() {
  els.workspaceActions.innerHTML = "";
  els.workspaceStats.innerHTML = "";
  els.tableTitle.textContent = "数据列表";
  els.tableBadge.textContent = "0 条记录";
  els.tableWrap.innerHTML = `<div class="empty-state">请先登录后进入业务模块。</div>`;
  els.insightPanel.innerHTML = `
    <div class="insight-block">
      <h4>使用说明</h4>
      <p>左侧提供管理员、教师、学生、宿管四类示例账号。登录后页面会按角色切换可见模块与可执行操作。</p>
    </div>
  `;
}

function renderModuleError(message) {
  els.workspaceActions.innerHTML = "";
  els.workspaceStats.innerHTML = "";
  els.tableTitle.textContent = "数据列表";
  els.tableBadge.textContent = "加载失败";
  els.tableWrap.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
  els.insightPanel.innerHTML = `
    <div class="insight-block">
      <h4>排查建议</h4>
      <ul class="insight-list">
        <li>确认数据库连接正常，左侧状态显示为“运行正常”。</li>
        <li>检查当前角色是否具备访问该模块的权限。</li>
        <li>如刚修改数据，请点击右上角“刷新当前页面”。</li>
      </ul>
    </div>
  `;
}

function renderModule(viewId, rows) {
  const config = viewConfigs[viewId];
  const toolbarActions = config.toolbarActions(state.user) || [];
  const stats = config.statsBuilder ? config.statsBuilder(rows, state.user) : [];
  const insights = config.insightBuilder ? config.insightBuilder(rows, state.user) : [];

  els.workspaceActions.innerHTML = toolbarActions
    .map(
      (action) => `
        <button class="${action.kind === "primary" ? "primary-btn" : "ghost-btn"}" type="button" data-toolbar-action="${action.id}">
          ${escapeHtml(action.label)}
        </button>
      `
    )
    .join("");

  els.workspaceStats.innerHTML = stats
    .map(
      (item) => `
        <article class="metric-card">
          <span>${escapeHtml(item.label)}</span>
          <strong>${escapeHtml(String(item.value))}</strong>
          <span class="mini-copy">${escapeHtml(item.note || "")}</span>
        </article>
      `
    )
    .join("");

  els.tableTitle.textContent = config.label;
  els.tableBadge.textContent = `${rows.length} 条记录`;
  els.tableWrap.innerHTML = renderTable(viewId, rows);
  els.insightPanel.innerHTML = insights.length
    ? insights
        .map(
          (block) => `
            <section class="insight-block">
              <h4>${escapeHtml(block.title)}</h4>
              ${block.text ? `<p>${escapeHtml(block.text)}</p>` : ""}
              ${
                block.items && block.items.length
                  ? `<ul class="insight-list">${block.items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
                  : ""
              }
            </section>
          `
        )
        .join("")
    : `<div class="insight-block"><h4>页面说明</h4><p>当前模块暂无额外说明。</p></div>`;
}

function renderTable(viewId, rows) {
  if (!rows.length) {
    return `<div class="empty-state">当前条件下没有查询到数据。</div>`;
  }

  const config = viewConfigs[viewId];
  const hasActions = rows.some((row) => (config.rowActions(state.user, row) || []).length > 0);
  const headCells = config.columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join("");
  const actionHead = hasActions ? "<th>操作</th>" : "";

  const bodyRows = rows
    .map((row, index) => {
      const columns = config.columns
        .map((column) => {
          const rawValue = row[column.key];
          const text = column.format ? column.format(rawValue, row) : rawValue ?? "-";
          return `<td>${escapeHtml(String(text ?? "-"))}</td>`;
        })
        .join("");

      const actionButtons = hasActions
        ? `<td>
            <div class="table-actions">
              ${(config.rowActions(state.user, row) || [])
                .map(
                  (action) => `
                    <button class="table-action ${action.kind || ""}" type="button" data-row-index="${index}" data-row-action="${action.id}">
                      ${escapeHtml(action.label)}
                    </button>
                  `
                )
                .join("")}
            </div>
          </td>`
        : "";

      return `<tr>${columns}${actionButtons}</tr>`;
    })
    .join("");

  return `
    <table>
      <thead>
        <tr>${headCells}${actionHead}</tr>
      </thead>
      <tbody>${bodyRows}</tbody>
    </table>
  `;
}

async function handleSearch(event) {
  event.preventDefault();
  const config = viewConfigs[state.activeView];
  if (!config.searchable) {
    return;
  }
  state.filters[state.activeView] = els.searchInput.value.trim();
  await loadModule(state.activeView, true);
}

async function resetSearch() {
  state.filters[state.activeView] = "";
  els.searchInput.value = "";
  if (state.activeView !== "dashboard") {
    await loadModule(state.activeView, true);
  }
}

async function handleNavClick(event) {
  const button = event.target.closest("[data-view]");
  if (!button) {
    return;
  }
  await activateView(button.dataset.view, true);
}

async function handleToolbarAction(event) {
  const button = event.target.closest("[data-toolbar-action]");
  if (!button) {
    return;
  }
  const action = button.dataset.toolbarAction;
  switch (action) {
    case "add-student":
      await openStudentModal();
      break;
    case "add-course":
      await openCourseModal();
      break;
    case "add-dormitory":
      await openDormitoryModal();
      break;
    case "add-notice":
      await openNoticeModal();
      break;
    case "add-enrollment":
      await openEnrollmentCreateModal();
      break;
    default:
      break;
  }
}

async function handleTableAction(event) {
  const button = event.target.closest("[data-row-action]");
  if (!button) {
    return;
  }
  const row = state.currentRows[Number(button.dataset.rowIndex)];
  if (!row) {
    return;
  }

  const action = button.dataset.rowAction;
  switch (action) {
    case "edit-student":
      await openStudentModal(row);
      break;
    case "delete-student":
      await deleteStudent(row);
      break;
    case "edit-course":
      await openCourseModal(row);
      break;
    case "delete-course":
      await deleteCourse(row);
      break;
    case "edit-dormitory":
      await openDormitoryModal(row);
      break;
    case "edit-notice":
      await openNoticeModal(row);
      break;
    case "delete-notice":
      await deleteNotice(row);
      break;
    case "edit-enrollment":
      await openEnrollmentEditModal(row);
      break;
    case "delete-enrollment":
      await deleteEnrollment(row);
      break;
    default:
      break;
  }
}

async function openStudentModal(row = null) {
  await ensureLookups(["classes", "dormitories"]);
  const classes = state.lookups.classes || [];
  const dormitories = state.lookups.dormitories || [];
  const initialValues = row || {
    sgender: "男",
    status: "在读",
  };

  openModal({
    title: row ? "编辑学生档案" : "新增学生档案",
    submitLabel: row ? "保存学生信息" : "创建学生",
    successMessage: row ? "学生信息已更新" : "学生信息已新增",
    initialValues,
    fields: [
      { name: "sno", label: "学号", required: true, disabled: Boolean(row) },
      { name: "sname", label: "姓名", required: true },
      {
        name: "sgender",
        label: "性别",
        type: "select",
        options: ["男", "女"].map((value) => ({ value, label: value })),
      },
      { name: "sbirth", label: "出生日期", type: "date" },
      { name: "sphone", label: "联系电话", placeholder: "例如：13900000000" },
      {
        name: "class_id",
        label: "班级",
        type: "select",
        required: true,
        options: classes.map((item) => ({
          value: item.class_id,
          label: `${item.class_name} | ${item.major}`,
        })),
      },
      {
        name: "dorm_id",
        label: "宿舍",
        type: "select",
        options: [{ value: "", label: "未分配" }].concat(
          dormitories.map((item) => ({
            value: item.dorm_id,
            label: `${item.building}-${item.room} | 空床位 ${item.available_beds}`,
          }))
        ),
      },
      {
        name: "status",
        label: "状态",
        type: "select",
        options: ["在读", "毕业", "休学", "退学"].map((value) => ({ value, label: value })),
      },
    ],
    onSubmit: (payload) =>
      fetchJson(row ? `/api/students/${row.sno}` : "/api/students", {
        method: row ? "PUT" : "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: async () => {
      invalidateLookups(["students"]);
      await activateView("students", true);
    },
  });
}

async function deleteStudent(row) {
  const confirmed = window.confirm(`确认删除学生 ${row.sname}（${row.sno}）吗？`);
  if (!confirmed) {
    return;
  }
  await fetchJson(`/api/students/${row.sno}`, { method: "DELETE" });
  invalidateLookups(["students"]);
  showToast("学生记录已删除", "success");
  await activateView("students", true);
}

async function openCourseModal(row = null) {
  await ensureLookups(["teachers"]);
  const teachers = state.lookups.teachers || [];
  const initialValues = row || {
    status: "开课中",
    credit: 2,
    cperiod: 32,
  };

  openModal({
    title: row ? "编辑课程信息" : "新增课程",
    submitLabel: row ? "保存课程信息" : "创建课程",
    successMessage: row ? "课程信息已更新" : "课程已新增",
    initialValues,
    fields: [
      { name: "cno", label: "课程号", required: true, disabled: Boolean(row) },
      { name: "cname", label: "课程名称", required: true, fullSpan: true },
      { name: "cperiod", label: "学时", type: "number", valueType: "number", min: 0 },
      { name: "credit", label: "学分", type: "number", valueType: "number", min: 0, step: "0.5" },
      {
        name: "tno",
        label: "授课教师",
        type: "select",
        required: true,
        options: teachers.map((item) => ({
          value: item.tno,
          label: `${item.tname} | ${item.tpro || "教师"}`,
        })),
      },
      {
        name: "status",
        label: "状态",
        type: "select",
        options: ["开课中", "停开"].map((value) => ({ value, label: value })),
      },
      { name: "schedule_info", label: "上课时间", placeholder: "例如：周二1-2节" },
      { name: "classroom", label: "教室", placeholder: "例如：A201" },
      { name: "weeks", label: "周次", placeholder: "例如：1-16周", fullSpan: true },
    ],
    onSubmit: (payload) =>
      fetchJson(row ? `/api/courses/${row.cno}` : "/api/courses", {
        method: row ? "PUT" : "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: async () => {
      invalidateLookups(["courseCatalog"]);
      showToast(row ? "课程信息已更新" : "课程已新增", "success");
      await activateView("courses", true);
    },
  });
}

async function deleteCourse(row) {
  const confirmed = window.confirm(`确认删除课程 ${row.cname}（${row.cno}）吗？`);
  if (!confirmed) {
    return;
  }
  await fetchJson(`/api/courses/${row.cno}`, { method: "DELETE" });
  invalidateLookups(["courseCatalog"]);
  showToast("课程已删除", "success");
  await activateView("courses", true);
}

async function openDormitoryModal(row = null) {
  await ensureLookups(["dormManagers"]);
  const managers = state.lookups.dormManagers || [];
  const initialValues = row || {
    status: "正常",
    max_num: 4,
    cur_num: 0,
  };

  openModal({
    title: row ? "编辑宿舍信息" : "新增宿舍",
    submitLabel: row ? "保存宿舍信息" : "创建宿舍",
    successMessage: row ? "宿舍信息已更新" : "宿舍已新增",
    initialValues,
    fields: [
      { name: "dorm_id", label: "宿舍号", required: true, disabled: Boolean(row) },
      { name: "building", label: "楼栋", required: true },
      { name: "room", label: "房间号", required: true },
      {
        name: "dm_id",
        label: "宿管",
        type: "select",
        required: true,
        options: managers.map((item) => ({
          value: item.dm_id,
          label: `${item.dm_name} | ${item.dm_phone}`,
        })),
      },
      { name: "max_num", label: "床位容量", type: "number", valueType: "number", min: 1 },
      { name: "cur_num", label: "当前入住", type: "number", valueType: "number", min: 0 },
      {
        name: "status",
        label: "状态",
        type: "select",
        options: ["正常", "维修", "停用"].map((value) => ({ value, label: value })),
      },
    ],
    onSubmit: (payload) =>
      fetchJson(row ? `/api/dormitories/${row.dorm_id}` : "/api/dormitories", {
        method: row ? "PUT" : "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: async () => {
      invalidateLookups(["dormitories"]);
      await activateView("dormitories", true);
    },
  });
}

async function openNoticeModal(row = null) {
  const categoryOptions = ["学校", "教学", "宿舍", "活动"].map((value) => ({ value, label: value }));
  const statusOptions = ["已发布", "草稿"].map((value) => ({ value, label: value }));
  const initialValues = row
    ? { ...row, pinned: String(Boolean(row.pinned)) }
    : { category: "学校", scope: "全校", status: "已发布", pinned: "false" };

  openModal({
    title: row ? "编辑公告" : "发布公告",
    submitLabel: row ? "保存公告" : "立即发布",
    successMessage: row ? "公告已更新" : "公告已发布",
    initialValues,
    fields: [
      { name: "title", label: "标题", required: true, fullSpan: true },
      {
        name: "category",
        label: "分类",
        type: "select",
        options: categoryOptions,
      },
      { name: "scope", label: "可见范围", placeholder: "例如：全校 / 教师 / 1号楼" },
      {
        name: "status",
        label: "发布状态",
        type: "select",
        options: statusOptions,
      },
      {
        name: "pinned",
        label: "是否置顶",
        type: "select",
        valueType: "boolean",
        options: [
          { value: "false", label: "否" },
          { value: "true", label: "是" },
        ],
      },
      { name: "content", label: "正文内容", type: "textarea", required: true, fullSpan: true },
    ],
    onSubmit: (payload) =>
      fetchJson(row ? `/api/notices/${row.nid}` : "/api/notices", {
        method: row ? "PUT" : "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: async () => {
      await activateView("notices", true);
    },
  });
}

async function deleteNotice(row) {
  const confirmed = window.confirm(`确认删除公告《${row.title}》吗？`);
  if (!confirmed) {
    return;
  }
  await fetchJson(`/api/notices/${row.nid}`, { method: "DELETE" });
  showToast("公告已删除", "success");
  await activateView("notices", true);
}

async function openEnrollmentCreateModal() {
  const requiredLookups = state.user.role === "admin" ? ["students", "courseCatalog"] : ["courseCatalog"];
  await ensureLookups(requiredLookups);
  const courseCatalog = (state.lookups.courseCatalog || []).filter((item) => item.status === "开课中");
  const studentOptions = (state.lookups.students || []).map((item) => ({
    value: item.sno,
    label: `${item.sname} | ${item.sno} | ${item.class_name}`,
  }));
  const courseOptions = courseCatalog.map((item) => ({
    value: item.cno,
    label: `${item.cname} | ${item.cno} | ${item.teacher_name || "未分配教师"}`,
  }));

  openModal({
    title: state.user.role === "student" ? "发起选课" : "新增选课记录",
    submitLabel: state.user.role === "student" ? "确认选课" : "创建记录",
    successMessage: state.user.role === "student" ? "选课成功" : "选课记录已新增",
    initialValues: {},
    fields: [
      ...(state.user.role === "admin"
        ? [
            {
              name: "sno",
              label: "学生",
              type: "select",
              required: true,
              options: studentOptions,
            },
          ]
        : []),
      {
        name: "cno",
        label: "课程",
        type: "select",
        required: true,
        options: courseOptions,
        fullSpan: true,
      },
      ...(state.user.role === "admin"
        ? [
            {
              name: "score",
              label: "初始成绩（可选）",
              type: "number",
              valueType: "number",
              min: 0,
              max: 100,
            },
          ]
        : []),
    ],
    onSubmit: (payload) =>
      fetchJson("/api/enrollments", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: async () => {
      await activateView("enrollments", true);
    },
  });
}

async function openEnrollmentEditModal(row) {
  openModal({
    title: "录入或更新成绩",
    submitLabel: "保存成绩",
    successMessage: "成绩已更新",
    initialValues: {
      score: row.score ?? "",
    },
    fields: [
      {
        name: "score",
        label: "成绩",
        type: "number",
        valueType: "number",
        min: 0,
        max: 100,
        placeholder: "留空表示暂未录入",
      },
    ],
    onSubmit: (payload) =>
      fetchJson(`/api/enrollments/${row.sno}/${row.cno}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      }),
    onSuccess: async () => {
      await activateView("enrollments", true);
    },
  });
}

async function deleteEnrollment(row) {
  const confirmed = window.confirm(`确认处理 ${row.student_name} 的课程 ${row.course_name} 退选/删除吗？`);
  if (!confirmed) {
    return;
  }
  await fetchJson(`/api/enrollments/${row.sno}/${row.cno}`, { method: "DELETE" });
  showToast("选课记录已移除", "success");
  await activateView("enrollments", true);
}

function openModal(options) {
  state.modal = options;
  els.modalTitle.textContent = options.title;
  els.modalSubmit.textContent = options.submitLabel || "保存";
  els.modalMessage.textContent = "";
  els.modalForm.innerHTML = options.fields.map((field) => renderField(field, options.initialValues?.[field.name])).join("");
  els.modalOverlay.classList.remove("hidden");
}

function closeModal() {
  state.modal = null;
  els.modalOverlay.classList.add("hidden");
  els.modalForm.innerHTML = "";
  els.modalMessage.textContent = "";
}

async function submitModal() {
  if (!state.modal) {
    return;
  }
  const { fields, onSubmit, onSuccess, successMessage } = state.modal;
  const payload = collectFormPayload(fields);
  setButtonBusy(els.modalSubmit, true, "提交中...");
  try {
    await onSubmit(payload);
    closeModal();
    showToast(successMessage || "操作成功", "success");
    if (onSuccess) {
      await onSuccess();
    }
  } catch (error) {
    els.modalMessage.textContent = error.message;
  } finally {
    setButtonBusy(els.modalSubmit, false, state.modal?.submitLabel || "保存");
  }
}

function renderField(field, value) {
  const labelClass = field.fullSpan ? "full-span" : "";
  const required = field.required ? "required" : "";
  const disabled = field.disabled ? "disabled" : "";
  const placeholder = field.placeholder ? `placeholder="${escapeHtml(field.placeholder)}"` : "";
  const min = field.min !== undefined ? `min="${field.min}"` : "";
  const max = field.max !== undefined ? `max="${field.max}"` : "";
  const step = field.step !== undefined ? `step="${field.step}"` : "";
  const safeValue = value ?? "";

  if (field.type === "select") {
    const options = (field.options || [])
      .map((option) => {
        const selected = String(option.value) === String(safeValue) ? "selected" : "";
        return `<option value="${escapeHtml(String(option.value))}" ${selected}>${escapeHtml(option.label)}</option>`;
      })
      .join("");
    return `
      <label class="${labelClass}">
        <span>${escapeHtml(field.label)}</span>
        <select name="${field.name}" ${required} ${disabled}>${options}</select>
      </label>
    `;
  }

  if (field.type === "textarea") {
    return `
      <label class="${labelClass}">
        <span>${escapeHtml(field.label)}</span>
        <textarea name="${field.name}" ${required} ${disabled} ${placeholder}>${escapeHtml(String(safeValue))}</textarea>
      </label>
    `;
  }

  return `
    <label class="${labelClass}">
      <span>${escapeHtml(field.label)}</span>
      <input
        name="${field.name}"
        type="${field.type || "text"}"
        value="${escapeHtml(String(safeValue))}"
        ${required}
        ${disabled}
        ${placeholder}
        ${min}
        ${max}
        ${step}
      >
    </label>
  `;
}

function collectFormPayload(fields) {
  const formData = new FormData(els.modalForm);
  const payload = {};

  fields.forEach((field) => {
    if (field.disabled) {
      return;
    }
    let value = formData.get(field.name);
    if (typeof value === "string") {
      value = value.trim();
    }
    if (field.valueType === "number") {
      payload[field.name] = value === "" ? "" : Number(value);
      return;
    }
    if (field.valueType === "boolean") {
      payload[field.name] = value === "true";
      return;
    }
    payload[field.name] = value;
  });

  return payload;
}

async function ensureLookups(keys) {
  const tasks = keys
    .filter((key) => !state.lookups[key])
    .map(async (key) => {
      state.lookups[key] = await lookupLoaders[key]();
    });
  await Promise.all(tasks);
}

function invalidateLookups(keys) {
  keys.forEach((key) => {
    delete state.lookups[key];
  });
}

async function loadWithKeyword(endpoint, keyword) {
  const safeKeyword = (keyword || "").trim();
  const query = safeKeyword ? `?keyword=${encodeURIComponent(safeKeyword)}` : "";
  return fetchJson(`${endpoint}${query}`);
}

function buildStudentStats(rows, user) {
  const active = rows.filter((row) => row.status === "在读").length;
  const assignedDorm = rows.filter((row) => row.dorm_id).length;
  return [
    { label: user.role === "student" ? "我的档案" : "当前记录", value: rows.length, note: "接口已按角色权限自动过滤" },
    { label: "在读人数", value: active, note: "可用于快速校验学籍状态" },
    { label: "已分配宿舍", value: assignedDorm, note: "宿舍分配完成的学生数量" },
    { label: "未分配宿舍", value: rows.length - assignedDorm, note: "可作为宿舍管理待办" },
  ];
}

function buildCourseStats(rows) {
  const openCount = rows.filter((row) => row.status === "开课中").length;
  const avgSelected = rows.length ? (rows.reduce((sum, row) => sum + normalizeNumber(row.selected_count), 0) / rows.length).toFixed(1) : "0.0";
  const totalCredit = rows.reduce((sum, row) => sum + normalizeNumber(row.credit), 0).toFixed(1);
  return [
    { label: "课程记录", value: rows.length, note: "当前角色可见课程总数" },
    { label: "开课中", value: openCount, note: "处于可选或在授状态的课程" },
    { label: "平均选课人数", value: avgSelected, note: "按当前课程列表计算" },
    { label: "总学分", value: totalCredit, note: "课程学分总量" },
  ];
}

function buildDormStats(rows) {
  const occupied = rows.reduce((sum, row) => sum + normalizeNumber(row.cur_num), 0);
  const available = rows.reduce((sum, row) => sum + normalizeNumber(row.available_beds), 0);
  const capacity = rows.reduce((sum, row) => sum + normalizeNumber(row.max_num), 0);
  const usage = capacity ? ((occupied / capacity) * 100).toFixed(1) : "0.0";
  return [
    { label: "宿舍数量", value: rows.length, note: "当前角色可见楼栋/房间总数" },
    { label: "当前入住", value: occupied, note: "宿舍已入住床位数" },
    { label: "空余床位", value: available, note: "可供新生或调宿使用" },
    { label: "床位利用率", value: `${usage}%`, note: "入住床位 / 总床位" },
  ];
}

function buildNoticeStats(rows) {
  const pinned = rows.filter((row) => Number(row.pinned)).length;
  const categories = new Set(rows.map((row) => row.category)).size;
  const campusWide = rows.filter((row) => row.scope === "全校" || row.scope === "全员").length;
  return [
    { label: "公告数量", value: rows.length, note: "当前角色可见公告总数" },
    { label: "置顶公告", value: pinned, note: "首页优先展示的信息" },
    { label: "分类数量", value: categories, note: "学校 / 教学 / 宿舍 / 活动等分类" },
    { label: "全校范围", value: campusWide, note: "对全校或全员生效的公告" },
  ];
}

function buildEnrollmentStats(rows) {
  const scored = rows.filter((row) => row.score !== null).length;
  const scoreValues = rows.filter((row) => row.score !== null).map((row) => normalizeNumber(row.score));
  const average = scoreValues.length ? (scoreValues.reduce((sum, value) => sum + value, 0) / scoreValues.length).toFixed(1) : "0.0";
  const max = scoreValues.length ? Math.max(...scoreValues) : 0;
  return [
    { label: "选课记录", value: rows.length, note: "当前角色可访问的选课条目" },
    { label: "已录成绩", value: scored, note: "已有成绩的选课记录数量" },
    { label: "平均成绩", value: average, note: "仅统计已录入成绩的记录" },
    { label: "最高成绩", value: max, note: "便于查看优异课程表现" },
  ];
}

function buildLogStats(rows) {
  const actorCount = new Set(rows.map((row) => row.actor)).size;
  return [
    { label: "日志条数", value: rows.length, note: "最近操作日志总量" },
    { label: "涉及人员", value: actorCount, note: "当前日志中出现的操作人数量" },
    { label: "最近时间", value: rows[0]?.created_at || "-", note: "按时间逆序展示" },
    { label: "最近动作", value: rows[0]?.action_name || "-", note: "可快速判断系统最新操作" },
  ];
}

function buildStudentInsights(rows, user) {
  return [
    {
      title: "当前权限",
      items:
        user.role === "admin"
          ? ["可新增、编辑、删除学生档案。", "修改学生状态时可联动宿舍分配约束。", "支持按学号、姓名、班级检索。"]
          : user.role === "student"
            ? ["仅展示本人档案。", "可在本页核对班级、专业、宿舍与联系方式。", "若宿舍为空，可联系管理员处理分配。"]
            : ["接口已自动过滤为当前角色可访问学生。", "教师看到自己授课课程相关学生。", "宿管看到自己负责楼栋内学生。"],
    },
    {
      title: "快速预览",
      items: rows.slice(0, 4).map((row) => `${row.sname} | ${row.class_name} | ${row.dorm_summary}`),
    },
  ];
}

function buildCourseInsights(rows, user) {
  return [
    {
      title: "当前权限",
      items:
        user.role === "admin"
          ? ["可维护课程号、教师、教室、周次与开课状态。", "课程停开后，后端会清理对应选课记录。", "建议在课程变更后刷新首页统计。"]
          : user.role === "teacher"
            ? ["展示当前教师授课课程。", "成绩录入在“选课与成绩”模块完成。", "可结合课程列表核对上课时间地点。"]
            : ["这里只展示当前学生已选课程。", "若需要新增课程，请前往“选课与成绩”执行选课。", "可通过课程状态判断是否仍在开课中。"],
    },
    {
      title: "快速预览",
      items: rows.slice(0, 4).map((row) => `${row.cname} | ${row.schedule_info} | ${row.classroom}`),
    },
  ];
}

function buildDormInsights(rows, user) {
  return [
    {
      title: "当前权限",
      items:
        ["admin", "dormManager"].includes(user.role)
          ? ["可新增或编辑宿舍记录。", "后端会校验入住人数不能超过床位容量。", "宿管角色只能维护自己负责的宿舍。"]
          : ["当前模块以查询为主。", "宿舍详情可与学生档案页中的宿舍归属交叉核对。"],
    },
    {
      title: "快速预览",
      items: rows.slice(0, 4).map((row) => `${row.building}-${row.room} | 空床位 ${row.available_beds} | ${row.status}`),
    },
  ];
}

function buildNoticeInsights(rows, user) {
  return [
    {
      title: "当前权限",
      items:
        ["admin", "teacher", "dormManager"].includes(user.role)
          ? ["可发布公告。", "非管理员只能编辑或删除自己发布的公告。", "置顶公告会优先出现在首页。"]
          : ["只展示与自己身份匹配的公告。", "全校、全员以及角色专属范围会自动过滤。"],
    },
    {
      title: "快速预览",
      items: rows.slice(0, 4).map((row) => `${row.title} | ${row.category} | ${row.scope}`),
    },
  ];
}

function buildEnrollmentInsights(rows, user) {
  return [
    {
      title: "当前权限",
      items:
        user.role === "student"
          ? ["可为本人发起选课或退课。", "只能选择状态为“开课中”的课程。", "成绩由教师或管理员录入。"]
          : user.role === "teacher"
            ? ["只能录入自己授课课程的成绩。", "无法新增或删除选课关系。", "支持将成绩留空表示暂未录入。"]
            : ["管理员可新增选课、编辑成绩、删除记录。", "新增选课时会校验学生状态与课程状态。"],
    },
    {
      title: "快速预览",
      items: rows.slice(0, 4).map((row) => `${row.student_name} | ${row.course_name} | ${row.score === null ? "待录入" : `${row.score}分`}`),
    },
  ];
}

function buildLogInsights(rows) {
  return [
    {
      title: "日志说明",
      items: ["系统会记录登录、增删改、公告发布、成绩录入等关键动作。", "日志按时间倒序排列，越靠前越新。", "该模块仅管理员可见。"],
    },
    {
      title: "最近记录预览",
      items: rows.slice(0, 4).map((row) => `${row.actor} | ${row.action_name} | ${row.created_at}`),
    },
  ];
}

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  els.toastRoot.appendChild(toast);
  window.setTimeout(() => {
    toast.remove();
  }, 2600);
}

function setButtonBusy(button, busy, label) {
  button.disabled = busy;
  button.textContent = label;
}

async function fetchJson(url, options = {}) {
  const requestOptions = {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  };
  const response = await fetch(url, requestOptions);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || data.detail || `请求失败：${response.status}`);
  }
  return data;
}

function normalizeNumber(value) {
  const result = Number(value);
  return Number.isFinite(result) ? result : 0;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

/**
 * SaveIQ - Main Application Logic
 */

let allGoals = [];
let currentCategoryFilter = "All";
let activeGoalForDeposit = null;

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initEventListeners();
  loadDashboard();
});

// Theme Management
function initTheme() {
  const saved = localStorage.getItem("saveiq-theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  updateThemeIcon(saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("saveiq-theme", next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  const btn = document.getElementById("themeToggleBtn");
  if (!btn) return;
  btn.innerHTML = theme === "dark" 
    ? `<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`
    : `<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
}

// Event Listeners
function initEventListeners() {
  document.getElementById("themeToggleBtn")?.addEventListener("click", toggleTheme);
  document.getElementById("openCreateGoalBtn")?.addEventListener("click", () => openModal("createGoalModal"));
  document.getElementById("closeCreateModalBtn")?.addEventListener("click", () => closeModal("createGoalModal"));
  document.getElementById("closeDepositModalBtn")?.addEventListener("click", () => closeModal("depositModal"));
  document.getElementById("closeAiModalBtn")?.addEventListener("click", () => closeModal("aiModal"));
  document.getElementById("triggerAuditBtn")?.addEventListener("click", handleRunAudit);

  // Forms
  document.getElementById("createGoalForm")?.addEventListener("submit", handleCreateGoalSubmit);
  document.getElementById("depositForm")?.addEventListener("submit", handleDepositSubmit);

  // Category filter tabs
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");
      currentCategoryFilter = e.target.getAttribute("data-filter");
      renderGoalsGrid();
    });
  });

  // Modal overlay click outside to close
  document.querySelectorAll(".modal-overlay").forEach(overlay => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        overlay.classList.remove("active");
      }
    });
  });
}

// Load Dashboard & Data
async function loadDashboard() {
  try {
    const [summary, goals] = await Promise.all([
      api.getDashboardSummary(),
      api.getGoals()
    ]);

    allGoals = goals;
    renderSummaryMetrics(summary);
    renderUrgentAlerts(summary.urgent_goals, summary.recent_alerts);
    renderCategoryChart(summary.category_breakdown);
    renderProgressBarChart(goals);
    renderGoalsGrid();
  } catch (err) {
    showToast("Error loading financial data: " + err.message, "error");
  }
}

// Render Summary Cards
function renderSummaryMetrics(s) {
  document.getElementById("valTotalSaved").innerText = `$${s.total_saved.toLocaleString(undefined, {minimumFractionDigits: 0})}`;
  document.getElementById("valTotalTarget").innerText = `$${s.total_target.toLocaleString(undefined, {minimumFractionDigits: 0})}`;
  document.getElementById("valOverallProgress").innerText = `${s.overall_progress}%`;
  document.getElementById("valDisciplineScore").innerText = `${s.discipline_score}/100`;

  document.getElementById("statActiveGoals").innerText = `${s.active_goals} Active Goals`;
  document.getElementById("statCompletedGoals").innerText = `${s.completed_goals} Completed (${s.overdue_goals} Overdue)`;
}

// Render Urgent Alerts & Deadline Monitor
function renderUrgentAlerts(urgentGoals, alerts) {
  const container = document.getElementById("urgentAlertsList");
  if (!container) return;

  if (!urgentGoals || urgentGoals.length === 0) {
    container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem; padding: 1rem 0;">No urgent deadlines pending. All goals on track!</div>`;
    return;
  }

  container.innerHTML = urgentGoals.map(g => {
    const isCritical = g.days_remaining <= 7;
    const badgeClass = isCritical ? 'badge-urgent' : 'badge-warning';
    const badgeText = g.days_remaining <= 0 ? 'Due Today' : `${g.days_remaining}d left`;

    return `
      <div class="urgent-item">
        <div class="urgent-info">
          <h4>${escapeHtml(g.name)}</h4>
          <span>$${g.remaining_amount.toLocaleString()} remaining • Need $${g.daily_required}/day</span>
        </div>
        <span class="urgent-badge ${badgeClass}">${badgeText}</span>
      </div>
    `;
  }).join("");
}

// Render Goals Grid
function renderGoalsGrid() {
  const container = document.getElementById("goalsGridContainer");
  if (!container) return;

  let filtered = allGoals;
  if (currentCategoryFilter !== "All") {
    if (currentCategoryFilter === "Completed") {
      filtered = allGoals.filter(g => g.status === "Completed");
    } else {
      filtered = allGoals.filter(g => g.category.toLowerCase().includes(currentCategoryFilter.toLowerCase()));
    }
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-muted);">
        <p style="font-size: 1.1rem; margin-bottom: 1rem;">No savings goals found in this view.</p>
        <button class="btn btn-primary" onclick="openModal('createGoalModal')">+ Create Your First Goal</button>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(g => {
    const progress = Math.min(100, g.progress_percentage);
    const isCompleted = g.status === "Completed" || progress >= 100;
    const isOverdue = g.days_remaining < 0 && !isCompleted;
    const priorityClass = `tag-priority-${(g.priority || 'medium').toLowerCase()}`;

    return `
      <div class="glass-panel goal-card" id="goal-card-${g.id}">
        <div>
          <div class="goal-top">
            <div class="goal-tags">
              <span class="tag tag-category">${escapeHtml(g.category)}</span>
              <span class="tag ${priorityClass}">${g.priority || 'Medium'}</span>
              ${isCompleted ? '<span class="tag tag-priority-low">Completed</span>' : ''}
              ${isOverdue ? '<span class="tag tag-priority-high">Overdue</span>' : ''}
            </div>
            <button class="icon-btn btn-sm" onclick="handleDeleteGoal(${g.id})" title="Delete Goal" style="width: 28px; height: 28px;">
              <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M3 6h18m-2 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
          </div>

          <h3 class="goal-name">${escapeHtml(g.name)}</h3>
          <p class="goal-purpose">${escapeHtml(g.purpose || 'Personal savings objective')}</p>

          <div class="progress-meta">
            <div>
              <span class="amount-current">$${g.current_amount.toLocaleString()}</span>
              <span class="amount-target">/ $${g.target_amount.toLocaleString()}</span>
            </div>
            <span style="font-weight: 700; color: var(--accent-primary); font-size: 0.95rem;">${progress}%</span>
          </div>

          <div class="progress-track">
            <div class="progress-fill ${isCompleted ? 'completed' : ''}" style="width: ${progress}%;"></div>
          </div>

          <div class="pacing-stats">
            <div class="pacing-item">
              <span class="pacing-label">Deadline</span>
              <span class="pacing-val">${g.days_remaining > 0 ? `${g.days_remaining} days` : (isCompleted ? 'Goal Achieved' : 'Passed')}</span>
            </div>
            <div class="pacing-item">
              <span class="pacing-label">Daily Pace</span>
              <span class="pacing-val">${isCompleted ? '$0.00' : `$${g.daily_required}/d`}</span>
            </div>
          </div>
        </div>

        <div class="card-actions">
          <button class="btn btn-secondary btn-sm" onclick="openDepositModal(${g.id})">
            <span>+ Deposit</span>
          </button>
          <button class="btn btn-primary btn-sm" onclick="openAiAdvisor(${g.id})">
            <span>✨ AI Advisor</span>
          </button>
        </div>
      </div>
    `;
  }).join("");
}

// Create Goal Submit Handler
async function handleCreateGoalSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const payload = {
    name: form.name.value.trim(),
    category: form.category.value,
    target_amount: parseFloat(form.target_amount.value),
    initial_savings: parseFloat(form.initial_savings.value || 0),
    deadline: form.deadline.value,
    email_alerts: form.email_alerts.checked,
    user_email: form.user_email.value.trim(),
    purpose: form.purpose.value.trim(),
    priority: form.priority.value
  };

  try {
    await api.createGoal(payload);
    showToast("Savings Goal successfully created!", "success");
    closeModal("createGoalModal");
    form.reset();
    await loadDashboard();
  } catch (err) {
    showToast("Failed to create goal: " + err.message, "error");
  }
}

// Deposit Modal
function openDepositModal(goalId) {
  const goal = allGoals.find(g => g.id === goalId);
  if (!goal) return;
  activeGoalForDeposit = goal;

  document.getElementById("depositGoalName").innerText = goal.name;
  document.getElementById("depositGoalTarget").innerText = `Target: $${goal.target_amount.toLocaleString()} (Remaining: $${goal.remaining_amount.toLocaleString()})`;
  document.getElementById("depositAmount").value = "";
  document.getElementById("depositNote").value = "";

  openModal("depositModal");
}

async function handleDepositSubmit(e) {
  e.preventDefault();
  if (!activeGoalForDeposit) return;

  const amount = parseFloat(document.getElementById("depositAmount").value);
  const note = document.getElementById("depositNote").value;

  try {
    await api.addDeposit(activeGoalForDeposit.id, { amount, note });
    showToast(`Added deposit of $${amount.toLocaleString()} to ${activeGoalForDeposit.name}!`, "success");
    closeModal("depositModal");
    await loadDashboard();
  } catch (err) {
    showToast("Deposit error: " + err.message, "error");
  }
}

// Delete Goal Handler
async function handleDeleteGoal(goalId) {
  const goal = allGoals.find(g => g.id === goalId);
  if (!confirm(`Are you sure you want to delete "${goal ? goal.name : 'this goal'}"?`)) return;

  try {
    await api.deleteGoal(goalId);
    showToast("Goal successfully deleted", "info");
    await loadDashboard();
  } catch (err) {
    showToast("Failed to delete goal: " + err.message, "error");
  }
}

// AI Advisor Modal & Groq Engine Execution
async function openAiAdvisor(goalId) {
  const goal = allGoals.find(g => g.id === goalId);
  if (!goal) return;

  openModal("aiModal");
  document.getElementById("aiGoalTitle").innerText = `AI Insights: ${goal.name}`;
  document.getElementById("aiModalBody").innerHTML = `
    <div style="text-align: center; padding: 2.5rem 0;">
      <div class="pulse-dot" style="margin: 0 auto 1rem; width: 14px; height: 14px;"></div>
      <p style="color: var(--text-secondary); font-size: 0.95rem;">Analyzing financial pacing & querying Groq LLaMA 3.3-70B Engine...</p>
    </div>
  `;

  try {
    const aiData = await api.getAIRecommendation(goalId);

    document.getElementById("aiModalBody").innerHTML = `
      <div class="ai-score-ring-wrap">
        <div class="score-circle">
          ${aiData.feasibility_score}<span>%</span>
        </div>
        <div class="score-details">
          <h4>Pacing Feasibility Score: ${aiData.feasibility_score}/100</h4>
          <p>Required Velocity: <b>$${aiData.daily_saving_target.toLocaleString()}/day</b> ($${aiData.weekly_saving_target.toLocaleString()}/week)</p>
          <span style="font-size: 0.72rem; color: var(--accent-primary);">Source: ${escapeHtml(aiData.source_model || 'Groq LLaMA 3.3-70B')}</span>
        </div>
      </div>

      <div class="ai-recommendation-box">
        ${escapeHtml(aiData.recommendation)}
      </div>

      <h5 style="margin-bottom: 0.65rem; font-size: 0.88rem; font-weight: 700; color: var(--text-primary);">Strategic Action Plan:</h5>
      <ul class="ai-strategies-list">
        ${aiData.strategies.map(s => `<li>${escapeHtml(s)}</li>`).join("")}
      </ul>

      <div class="ai-quote-box">
        "${escapeHtml(aiData.motivational_quote)}"
      </div>
    `;
  } catch (err) {
    document.getElementById("aiModalBody").innerHTML = `
      <div style="color: var(--rose); padding: 1.5rem; text-align: center;">
        Failed to load AI guidance: ${escapeHtml(err.message)}
      </div>
    `;
  }
}

// Run Daily Audit Handler
async function handleRunAudit() {
  const btn = document.getElementById("triggerAuditBtn");
  if (btn) btn.disabled = true;

  try {
    showToast("Running automated financial audit across all goals...", "info");
    const result = await api.triggerAudit();
    showToast(`Audit complete: ${result.audited_count} goals audited, ${result.alerts_created} alerts processed!`, "success");
    await loadDashboard();
  } catch (err) {
    showToast("Audit execution error: " + err.message, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

// Modal Helpers
function openModal(id) {
  document.getElementById(id)?.classList.add("active");
}

function closeModal(id) {
  document.getElementById(id)?.classList.remove("active");
}

// Toast Notifications
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = "toast";
  
  let icon = "ℹ️";
  if (type === "success") icon = "✅";
  if (type === "error") icon = "⚠️";

  toast.innerHTML = `<span>${icon}</span><span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

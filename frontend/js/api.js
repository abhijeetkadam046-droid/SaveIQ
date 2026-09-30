/**
 * SaveIQ API Client
 * Handles communication with the FastAPI backend
 */

const API_BASE = "/api";

const api = {
  // Goals
  async getGoals(category = "All", status = "All") {
    const params = new URLSearchParams();
    if (category && category !== "All") params.append("category", category);
    if (status && status !== "All") params.append("status", status);
    
    const res = await fetch(`${API_BASE}/goals?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to load goals");
    return await res.json();
  },

  async createGoal(goalData) {
    const res = await fetch(`${API_BASE}/goals`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(goalData)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create goal");
    }
    return await res.json();
  },

  async deleteGoal(goalId) {
    const res = await fetch(`${API_BASE}/goals/${goalId}`, {
      method: "DELETE"
    });
    if (!res.ok) throw new Error("Failed to delete goal");
    return await res.json();
  },

  async addDeposit(goalId, depositData) {
    const res = await fetch(`${API_BASE}/goals/${goalId}/deposit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(depositData)
    });
    if (!res.ok) throw new Error("Failed to record deposit");
    return await res.json();
  },

  // Dashboard Summary
  async getDashboardSummary() {
    const res = await fetch(`${API_BASE}/dashboard/summary`);
    if (!res.ok) throw new Error("Failed to load dashboard summary");
    return await res.json();
  },

  // AI Recommendation (Groq LLaMA 3.3-70B)
  async getAIRecommendation(goalId, prompt = "") {
    const res = await fetch(`${API_BASE}/ai/recommendation/${goalId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal_id: goalId, prompt })
    });
    if (!res.ok) throw new Error("Failed to retrieve AI advice");
    return await res.json();
  },

  // Automated Deadline Audit
  async triggerAudit() {
    const res = await fetch(`${API_BASE}/audit/run`, {
      method: "POST"
    });
    if (!res.ok) throw new Error("Failed to execute audit");
    return await res.json();
  }
};

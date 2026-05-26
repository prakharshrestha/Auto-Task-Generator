const API_BASE = "/api/";

export const api = {
  // Tasks
  getTasks: async (limit = 50) => {
    const res = await fetch(`${API_BASE}/tasks/?limit=${limit}`);
    if (!res.ok) throw new Error("Failed to fetch tasks");
    return res.json();
  },
  
  createTask: async (taskData) => {
    const res = await fetch(`${API_BASE}/tasks/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(taskData)
    });
    if (!res.ok) throw new Error("Failed to create task");
    return res.json();
  },

  updateTask: async (taskId, updates) => {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates)
    });
    if (!res.ok) throw new Error("Failed to update task");
    return res.json();
  },

  deleteTask: async (taskId) => {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
      method: "DELETE"
    });
    if (!res.ok) throw new Error("Failed to delete task");
    return res.json();
  },

  // Agent / Planning
  getStats: async () => {
    const res = await fetch(`${API_BASE}/tasks/stats/agent`);
    if (!res.ok) throw new Error("Failed to fetch stats");
    return res.json();
  },

  generatePlan: async (taskId) => {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/reason`, {
      method: "POST"
    });
    if (!res.ok) throw new Error("Failed to generate plan");
    return res.json();
  },

  // Email Extraction
  extractFromRecentEmails: async (limit = 10) => {
    const res = await fetch(`${API_BASE}/gmail/recent-plans?limit=${limit}&mode=extract`);
    if (!res.ok) {
      if (res.status === 401) {
        throw new Error("Gmail authentication required");
      }
      throw new Error("Failed to extract emails");
    }
    return res.json();
  },
  getRawRecentEmails: async (limit = 10) => {
    const res = await fetch(`${API_BASE}/gmail/recent-plans?limit=${limit}&mode=raw`);
    if (!res.ok) {
      if (res.status === 401) {
        throw new Error("Gmail authentication required");
      }
      throw new Error("Failed to fetch emails");
    }
    return res.json();
  },
  extractTasksForEmail: async (subject, body, sender) => {
    const res = await fetch(`${API_BASE}/tasks/extract`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email_subject: subject, email_body: body, sender: sender })
    });
    if (!res.ok) throw new Error("Failed to extract tasks");
    return res.json();
  }
};

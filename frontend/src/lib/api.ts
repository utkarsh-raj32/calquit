const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

export type UserContext = {
  user_id: string;
  role: "customer" | "support_agent" | "ops_manager";
  account_id?: string;
  name: string;
  email: string;
};

export type ActionStatus = "pending_confirmation" | "executed" | "rejected";

export type PendingAction = {
  action_id: string;
  action_type: string;
  status: ActionStatus;
  created_by: string;
  created_at: string;
  [key: string]: any; // action specific details
};

// Simple singleton for auth token
let currentToken: string | null = null;
let currentUser: UserContext | null = null;

if (typeof window !== "undefined") {
  currentToken = localStorage.getItem("pp_token");
  const userStr = localStorage.getItem("pp_user");
  if (userStr) {
    try {
      currentUser = JSON.parse(userStr);
    } catch (e) {}
  }
}

export const auth = {
  getToken: () => {
    if (currentToken) return currentToken;
    if (typeof window !== "undefined") {
      currentToken = localStorage.getItem("pp_token");
    }
    return currentToken;
  },
  getUser: () => {
    if (currentUser) return currentUser;
    if (typeof window !== "undefined") {
      const userStr = localStorage.getItem("pp_user");
      if (userStr) {
        try {
          currentUser = JSON.parse(userStr);
        } catch (e) {}
      }
    }
    return currentUser;
  },
  
  login: async (username: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username }),
    });
    
    if (!res.ok) throw new Error("Login failed");
    
    const data = await res.json();
    currentToken = data.token;
    currentUser = data.user;
    
    if (typeof window !== "undefined") {
      localStorage.setItem("pp_token", currentToken as string);
      localStorage.setItem("pp_user", JSON.stringify(currentUser));
    }
    
    return currentUser;
  },
  
  logout: () => {
    currentToken = null;
    currentUser = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("pp_token");
      localStorage.removeItem("pp_user");
    }
  },
  
  getMockUsers: async () => {
    const res = await fetch(`${API_BASE}/auth/users`);
    if (!res.ok) throw new Error("Failed to fetch users");
    const data = await res.json();
    return data.users;
  }
};

export const api = {
  getHeaders: () => {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    const token = auth.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  },
  
  // Actions API
  getPendingActions: async (): Promise<PendingAction[]> => {
    const res = await fetch(`${API_BASE}/actions/pending`, {
      headers: api.getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch pending actions");
    const data = await res.json();
    return data.actions;
  },
  
  confirmAction: async (actionId: string) => {
    const res = await fetch(`${API_BASE}/actions/${actionId}/confirm`, {
      method: "POST",
      headers: api.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to confirm action");
    }
    return res.json();
  },
  
  rejectAction: async (actionId: string) => {
    const res = await fetch(`${API_BASE}/actions/${actionId}/reject`, {
      method: "POST",
      headers: api.getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to reject action");
    return res.json();
  },
  
  // Dashboard API
  getDashboardInsights: async () => {
    const res = await fetch(`${API_BASE}/dashboard/insights`, {
      headers: api.getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch dashboard data");
    return res.json();
  },

  // Chat stream URL getter
  getChatStreamUrl: () => `${API_BASE}/chat/stream`,
};

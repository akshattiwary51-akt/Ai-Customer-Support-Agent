const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type ApiOrder = {
  id: number;
  order_number: string;
  status: string;
  total_cents: number;
  currency: string;
  tracking_number: string | null;
};

export type ApiChatResponse = {
  conversation_id: number;
  assistant_message: {
    id: number;
    role: string;
    content: string;
    citations: Array<{ document_name: string; excerpt: string; score: number }>;
    created_at: string;
  };
  intent: {
    intent: string;
    confidence: number;
    suggested_action: string;
    escalation_required: boolean;
  };
  tool_results: Array<{ tool_name: string; success: boolean; result?: Record<string, unknown> }>;
};

export type AnalyticsOverview = {
  total_conversations: number;
  resolved_by_ai: number;
  human_escalation_rate: number;
  ticket_backlog: number;
  priority_distribution: Record<string, number>;
  tool_success_rate: number | null;
  rag_citation_count: number;
};

export type ApiTicket = {
  id: number;
  subject: string;
  description: string;
  priority: string;
  category: string;
  status: string;
  escalation_reason: string | null;
};

export type OrchestrationStep = {
  order: number;
  layer: string;
  name: string;
  status: "complete" | "active" | "skipped" | "retry" | "failed";
  detail: string;
  outputs: Record<string, unknown>;
};

export type OrchestrationGraphNode = {
  id: string;
  label: string;
  layer: string;
  status: "complete" | "active" | "skipped" | "retry" | "failed";
  detail: string;
  metadata: Record<string, unknown>;
};

export type OrchestrationGraphEdge = {
  source: string;
  target: string;
  label?: string | null;
  edge_type: "solid" | "dashed";
};

export type OrchestrationResponse = {
  request: string;
  route: string;
  retries: number;
  quality_score: number;
  final_status: "good" | "bad" | "retry" | "failed";
  final_response: string;
  steps: OrchestrationStep[];
  graph_nodes: OrchestrationGraphNode[];
  graph_edges: OrchestrationGraphEdge[];
};

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail ?? "Request failed");
  }
  return response.json() as Promise<T>;
}

export async function login(email = "customer@example.com", password = "Password123!") {
  return request<{ access_token: string }>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function getOrders(token: string) {
  return request<ApiOrder[]>("/api/v1/orders", {}, token);
}

export async function sendChat(message: string, token: string, conversationId?: number) {
  return request<ApiChatResponse>(
    "/api/v1/chat",
    {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId }),
    },
    token,
  );
}

export async function getAnalytics(token: string) {
  return request<AnalyticsOverview>("/api/v1/analytics/overview", {}, token);
}

export async function createTicket(
  token: string,
  payload: {
    subject: string;
    description: string;
    priority?: "LOW" | "NORMAL" | "HIGH" | "URGENT";
    category?: string;
    escalation_reason?: string;
    conversation_id?: number;
  },
) {
  return request<ApiTicket>(
    "/api/v1/tickets",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export async function createFeedback(
  token: string,
  payload: { message_id: number; rating: -1 | 1; comment?: string },
) {
  return request<{ status: string; feedback_id: number }>(
    "/api/v1/feedback",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export async function runOrchestration(message: string, token: string) {
  return request<OrchestrationResponse>(
    "/api/v1/orchestration/run",
    {
      method: "POST",
      body: JSON.stringify({ message }),
    },
    token,
  );
}

export { API_BASE_URL };

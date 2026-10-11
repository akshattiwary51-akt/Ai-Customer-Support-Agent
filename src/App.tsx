import { FormEvent, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowUpRight,
  Bot,
  Check,
  ChevronDown,
  Clock3,
  Copy,
  FileSearch,
  Gauge,
  Headphones,
  History,
  Inbox,
  LifeBuoy,
  MessageSquare,
  PanelRightOpen,
  Search,
  Send,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  UserRoundCheck,
  Wand2,
  Zap,
} from "lucide-react";
import {
  API_BASE_URL,
  type AnalyticsOverview,
  type ApiChatResponse,
  type ApiOrder,
  type OrchestrationGraphNode,
  type OrchestrationResponse,
  type OrchestrationStep,
  createFeedback,
  createTicket,
  getAnalytics,
  getOrders,
  login,
  runOrchestration,
  sendChat,
} from "./api";
import {
  automations,
  knowledgeArticles,
  queues,
  resolutionMetrics,
  tickets,
  type Ticket,
  type TicketPriority,
} from "./data";

const priorityOrder: Record<TicketPriority, number> = {
  Urgent: 0,
  High: 1,
  Normal: 2,
};

const defaultFlow: OrchestrationStep[] = [
  {
    order: 1,
    layer: "User",
    name: "Incoming request",
    status: "skipped",
    detail: 'Example: "Why was I charged twice?"',
    outputs: {},
  },
  {
    order: 2,
    layer: "LangGraph",
    name: "State",
    status: "skipped",
    detail: "Intent, retry count, confirmation, and conversation state.",
    outputs: {},
  },
  {
    order: 3,
    layer: "LangGraph",
    name: "Orchestrator",
    status: "skipped",
    detail: "Controls routing, retry, and what runs next.",
    outputs: {},
  },
  {
    order: 4,
    layer: "LangGraph",
    name: "Billing / Technical / General Node",
    status: "skipped",
    detail: "One route is selected while unrelated nodes are skipped.",
    outputs: {},
  },
  {
    order: 5,
    layer: "LangChain",
    name: "Building blocks",
    status: "skipped",
    detail: "Prompts, chains, retrievers, tools, and model provider adapters.",
    outputs: {},
  },
  {
    order: 6,
    layer: "LangChain",
    name: "Retriever / Vector DB",
    status: "skipped",
    detail: "RAG search over indexed company knowledge.",
    outputs: {},
  },
  {
    order: 7,
    layer: "LangChain",
    name: "LLM / Tools",
    status: "skipped",
    detail: "Reasoning plus authorized API/database actions.",
    outputs: {},
  },
  {
    order: 8,
    layer: "Evaluator",
    name: "Quality gate",
    status: "skipped",
    detail: "LLM-as-judge style check for grounded, safe, complete answer.",
    outputs: {},
  },
  {
    order: 9,
    layer: "Response",
    name: "Good response or retry",
    status: "skipped",
    detail: "Good answers are returned; weak answers loop back for retry.",
    outputs: {},
  },
];

const defaultGraphNodes: OrchestrationGraphNode[] = [
  {
    id: "user",
    label: "USER",
    layer: "User",
    status: "skipped",
    detail: 'Ask a support question such as "Why was I charged twice?"',
    metadata: {},
  },
  {
    id: "state",
    label: "STATE",
    layer: "LangGraph",
    status: "skipped",
    detail: "Intent, retry count, confirmation, and routing state.",
    metadata: { retries: 0 },
  },
  {
    id: "orchestrator",
    label: "LangGraph Orchestrator",
    layer: "LangGraph",
    status: "skipped",
    detail: "State, routing, retry, and control decide what runs next.",
    metadata: {},
  },
  {
    id: "billing",
    label: "Billing Node",
    layer: "LangGraph",
    status: "skipped",
    detail: "Refunds, invoices, duplicate charges, and cancellations.",
    metadata: {},
  },
  {
    id: "technical",
    label: "Technical Node",
    layer: "LangGraph",
    status: "skipped",
    detail: "Bugs, errors, and troubleshooting.",
    metadata: {},
  },
  {
    id: "general",
    label: "General Node",
    layer: "LangGraph",
    status: "skipped",
    detail: "FAQs, how-to questions, and policies.",
    metadata: {},
  },
  {
    id: "blocks",
    label: "LangChain Building Blocks",
    layer: "LangChain",
    status: "skipped",
    detail: "Prompts, chains, retrievers, and tools define how work is done.",
    metadata: {},
  },
  {
    id: "retriever",
    label: "Retriever",
    layer: "LangChain",
    status: "skipped",
    detail: "RAG search over company knowledge.",
    metadata: {},
  },
  {
    id: "llm",
    label: "LLM",
    layer: "LangChain",
    status: "skipped",
    detail: "Reasoning through an OpenAI/Gemini-compatible provider slot.",
    metadata: {},
  },
  {
    id: "tools",
    label: "Tools",
    layer: "LangChain",
    status: "skipped",
    detail: "Authorized actions against business functions and APIs.",
    metadata: {},
  },
  {
    id: "vector-db",
    label: "Vector DB",
    layer: "LangChain",
    status: "skipped",
    detail: "Embeddings and vector retrieval adapter.",
    metadata: {},
  },
  {
    id: "provider",
    label: "OpenAI / Gemini",
    layer: "LangChain",
    status: "skipped",
    detail: "Foundation model adapter.",
    metadata: {},
  },
  {
    id: "api-functions",
    label: "APIs + Functions",
    layer: "LangChain",
    status: "skipped",
    detail: "Database-backed tools and deterministic business functions.",
    metadata: {},
  },
  {
    id: "evaluator",
    label: "Evaluator",
    layer: "Evaluator",
    status: "skipped",
    detail: "Quality gate checks grounding, policy safety, and completeness.",
    metadata: {},
  },
  {
    id: "good",
    label: "Good",
    layer: "Decision",
    status: "skipped",
    detail: "Quality gate passed.",
    metadata: {},
  },
  {
    id: "bad",
    label: "Bad",
    layer: "Decision",
    status: "skipped",
    detail: "Quality gate failed or needs retry.",
    metadata: {},
  },
  {
    id: "response",
    label: "Response",
    layer: "Response",
    status: "skipped",
    detail: "Customer-safe final answer.",
    metadata: {},
  },
  {
    id: "retry",
    label: "Retry",
    layer: "LangGraph",
    status: "skipped",
    detail: "Loops back to the orchestrator with updated state.",
    metadata: {},
  },
];

function priorityClass(priority: TicketPriority) {
  return `priority priority-${priority.toLowerCase()}`;
}

function getStatusTone(status: Ticket["status"]) {
  if (status === "Needs agent") return "danger";
  if (status === "Ready to send") return "success";
  if (status === "Waiting on customer") return "muted";
  return "accent";
}

function App() {
  const [selectedTicketId, setSelectedTicketId] = useState(tickets[0].id);
  const [searchTerm, setSearchTerm] = useState("");
  const [priorityFilter, setPriorityFilter] = useState<"All" | TicketPriority>("All");
  const [tone, setTone] = useState<"Balanced" | "Empathetic" | "Concise">("Balanced");
  const [apiToken, setApiToken] = useState("");
  const [orders, setOrders] = useState<ApiOrder[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [chatInput, setChatInput] = useState("Where is order ORD-1001?");
  const [chatResult, setChatResult] = useState<ApiChatResponse | null>(null);
  const [conversationId, setConversationId] = useState<number | undefined>();
  const [apiState, setApiState] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [apiError, setApiError] = useState("");
  const [activeNav, setActiveNav] = useState("Inbox");
  const [actionNotice, setActionNotice] = useState("Ready for triage.");
  const [draftOverride, setDraftOverride] = useState("");
  const [orchestration, setOrchestration] = useState<OrchestrationResponse | null>(null);
  const [selectedGraphNodeId, setSelectedGraphNodeId] = useState("orchestrator");
  const isBusy = apiState === "loading";
  const flowSteps = orchestration?.steps ?? defaultFlow;
  const graphNodes = orchestration?.graph_nodes ?? defaultGraphNodes;
  const graphEdges = orchestration?.graph_edges ?? [];
  const nodeById = useMemo(() => new Map(graphNodes.map((node) => [node.id, node])), [graphNodes]);
  const selectedGraphNode = nodeById.get(selectedGraphNodeId) ?? graphNodes[0];
  const hasRetryEdge = graphEdges.some(
    (edge) => edge.edge_type === "dashed" && edge.source === "retry" && edge.target === "orchestrator",
  );

  const filteredTickets = useMemo(() => {
    return tickets
      .filter((ticket) => {
        const query = searchTerm.trim().toLowerCase();
        const matchesQuery =
          query.length === 0 ||
          `${ticket.customer} ${ticket.company} ${ticket.subject} ${ticket.tags.join(" ")}`
            .toLowerCase()
            .includes(query);
        const matchesPriority = priorityFilter === "All" || ticket.priority === priorityFilter;
        return matchesQuery && matchesPriority;
      })
      .sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);
  }, [priorityFilter, searchTerm]);

  const selectedTicket =
    tickets.find((ticket) => ticket.id === selectedTicketId) ?? filteredTickets[0] ?? tickets[0];

  const responsePreview = useMemo(() => {
    if (draftOverride) return draftOverride;
    const tonePrefix = {
      Balanced: "Hi, thanks for the detail here.",
      Empathetic: "I can see why this is frustrating, and I am sorry for the extra work this caused.",
      Concise: "Thanks for reporting this.",
    }[tone];

    return `${tonePrefix} ${selectedTicket.suggestedAnswer}`;
  }, [draftOverride, selectedTicket, tone]);

  const recommendedArticle = knowledgeArticles.find((article) =>
    selectedTicket.tags.some((tag) => article.topic.toLowerCase() === tag.toLowerCase()),
  );

  async function connectDemoBackend() {
    setApiState("loading");
    setApiError("");
    setActionNotice("Logging in as demo customer and loading orders...");
    try {
      const auth = await login();
      setApiToken(auth.access_token);
      const loadedOrders = await getOrders(auth.access_token);
      setOrders(loadedOrders);
      setApiError("");
      setActionNotice(
        loadedOrders.length
          ? `Demo customer connected. Loaded ${loadedOrders.length} orders.`
          : "Demo customer connected, but no orders were found.",
      );
      setApiState("ready");
      return auth.access_token;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to connect to backend";
      setApiState("error");
      setApiError(message);
      setActionNotice(`Login demo failed: ${message}`);
      return "";
    }
  }

  async function submitLiveChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const activeToken = apiToken || (await connectDemoBackend());
    if (!activeToken) return;
    setApiState("loading");
    setApiError("");
    try {
      const result = await sendChat(chatInput, activeToken, conversationId);
      setConversationId(result.conversation_id);
      setChatResult(result);
      setApiError("");
      setActionNotice(`Backend answered with intent: ${result.intent.intent}.`);
      setApiState("ready");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Chat request failed";
      setApiState("error");
      setApiError(message);
      setActionNotice(`Chat request failed: ${message}`);
    }
  }

  async function loadAgentAnalytics() {
    setApiState("loading");
    setApiError("");
    setActionNotice("Logging in as support agent and loading analytics...");
    try {
      const auth = await login("agent@example.com");
      const overview = await getAnalytics(auth.access_token);
      setAnalytics(overview);
      setApiError("");
      setActiveNav("Analytics");
      setActionNotice(
        `Analytics loaded: ${overview.total_conversations} conversations, ${overview.ticket_backlog} tickets in backlog.`,
      );
      setApiState("ready");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Analytics request failed";
      setApiState("error");
      setApiError(message);
      setActionNotice(`Load analytics failed: ${message}`);
    }
  }

  async function runSelectedTriage() {
    const activeToken = apiToken || (await connectDemoBackend());
    if (!activeToken) return;
    setApiState("loading");
    setActionNotice(`Running ordered orchestration for ${selectedTicket.id}...`);
    try {
      const trace = await runOrchestration(
        `${selectedTicket.subject}. ${selectedTicket.summary}`,
        activeToken,
      );
      const result = await sendChat(
        `${selectedTicket.subject}. ${selectedTicket.summary}`,
        activeToken,
        conversationId,
      );
      setOrchestration(trace);
      setConversationId(result.conversation_id);
      setChatResult(result);
      setChatInput(`${selectedTicket.subject}. ${selectedTicket.summary}`);
      setActionNotice(
        `Flow complete: ${trace.route}, quality ${Math.round(trace.quality_score * 100)}%, ${trace.final_status}.`,
      );
      setApiState("ready");
    } catch (error) {
      setApiState("error");
      setApiError(error instanceof Error ? error.message : "Triage failed");
    }
  }

  async function runCurrentRequestThroughFlow() {
    const activeToken = apiToken || (await connectDemoBackend());
    if (!activeToken) return;
    setApiState("loading");
    setApiError("");
    setActionNotice("Running request through LangGraph/LangChain flow...");
    try {
      const trace = await runOrchestration(chatInput, activeToken);
      setOrchestration(trace);
      setActionNotice(
        `Ordered flow finished: ${trace.route}, ${trace.steps.length} steps, ${trace.retries} retries.`,
      );
      setApiState("ready");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Orchestration failed";
      setApiState("error");
      setApiError(message);
      setActionNotice(`Ordered flow failed: ${message}`);
    }
  }

  async function openCrmRecord() {
    const activeToken = apiToken || (await connectDemoBackend());
    if (!activeToken) return;
    try {
      const loadedOrders = await getOrders(activeToken);
      setOrders(loadedOrders);
      setActiveNav("CRM");
      setActionNotice(
        loadedOrders[0]
          ? `CRM loaded ${loadedOrders.length} order records. Latest: ${loadedOrders[0].order_number}.`
          : "CRM loaded, but no customer orders were found.",
      );
    } catch (error) {
      setApiState("error");
      setApiError(error instanceof Error ? error.message : "CRM load failed");
    }
  }

  function improveDraft() {
    const improved = `${responsePreview} I will keep the case open until the next confirmed update and will not take any account action without explicit confirmation.`;
    setDraftOverride(improved);
    setActionNotice("Draft improved with confirmation guardrail and clearer follow-up.");
  }

  async function assignHuman() {
    const activeToken = apiToken || (await connectDemoBackend());
    if (!activeToken) return;
    setApiState("loading");
    try {
      const ticket = await createTicket(activeToken, {
        subject: selectedTicket.subject,
        description: `${selectedTicket.summary}\n\nDraft context: ${responsePreview}`,
        priority: selectedTicket.priority === "Urgent" ? "URGENT" : selectedTicket.priority === "High" ? "HIGH" : "NORMAL",
        category: selectedTicket.tags[0] ?? "General",
        escalation_reason: "Assigned from support console",
        conversation_id: conversationId,
      });
      setActionNotice(`Human handoff created ticket #${ticket.id} (${ticket.status}).`);
      setApiState("ready");
    } catch (error) {
      setApiState("error");
      setApiError(error instanceof Error ? error.message : "Human assignment failed");
    }
  }

  async function sendReply() {
    const activeToken = apiToken || (await connectDemoBackend());
    if (!activeToken) return;
    setApiState("loading");
    try {
      const result = await sendChat(
        `Record this approved customer reply for ${selectedTicket.id}: ${responsePreview}`,
        activeToken,
        conversationId,
      );
      setConversationId(result.conversation_id);
      setChatResult(result);
      setActionNotice(`Reply sent through backend conversation #${result.conversation_id}.`);
      setApiState("ready");
    } catch (error) {
      setApiState("error");
      setApiError(error instanceof Error ? error.message : "Send reply failed");
    }
  }

  async function copyDraft() {
    try {
      await navigator.clipboard.writeText(responsePreview);
      setActionNotice("Draft copied to clipboard.");
    } catch {
      setActionNotice("Copy failed in this browser session.");
    }
  }

  async function submitFeedback(rating: -1 | 1) {
    const activeToken = apiToken || (await connectDemoBackend());
    if (!activeToken || !chatResult) return;
    try {
      const feedback = await createFeedback(activeToken, {
        message_id: chatResult.assistant_message.id,
        rating,
        comment: rating === 1 ? "Useful support response" : "Needs improvement",
      });
      setActionNotice(`Feedback recorded as #${feedback.feedback_id}.`);
    } catch (error) {
      setApiState("error");
      setApiError(error instanceof Error ? error.message : "Feedback failed");
    }
  }

  function toggleFilters() {
    const nextFilter = priorityFilter === "Urgent" ? "All" : "Urgent";
    setPriorityFilter(nextFilter);
    setActionNotice(nextFilter === "All" ? "Priority filters cleared." : "Filtered to urgent cases.");
  }

  function renderGraphNode(id: string, className = "") {
    const node = nodeById.get(id);
    if (!node) return null;
    return (
      <button
        type="button"
        className={`graph-node ${node.status} ${className}`}
        onClick={() => setSelectedGraphNodeId(id)}
      >
        <span>{node.layer}</span>
        <strong>{node.label}</strong>
        <em>{node.detail}</em>
      </button>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand-block">
          <div className="brand-mark">
            <Headphones size={22} aria-hidden="true" />
          </div>
          <div>
            <p className="eyebrow">ResolveAI</p>
            <h1>Support Console</h1>
          </div>
        </div>

        <nav className="nav-stack">
          {[
            { label: "Inbox", icon: Inbox },
            { label: "Autopilot", icon: Bot },
            { label: "Knowledge", icon: FileSearch },
            { label: "Analytics", icon: Gauge },
            { label: "Audit log", icon: History },
          ].map((item) => (
            <button
              type="button"
              className={`nav-item ${activeNav === item.label ? "active" : ""}`}
              key={item.label}
              onClick={() => {
                setActiveNav(item.label);
                setActionNotice(`${item.label} view selected.`);
              }}
            >
              <item.icon size={18} aria-hidden="true" />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-panel">
          <div className="panel-header">
            <ShieldCheck size={18} aria-hidden="true" />
            <span>Policy guard</span>
          </div>
          <p>All AI replies are checked for refund authority, privacy scope, and citation quality.</p>
          <div className="guard-meter" aria-label="Policy guard score">
            <span style={{ width: "92%" }} />
          </div>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Production queue</p>
            <h2>AI customer support agent</h2>
          </div>
          <div className="topbar-actions">
            <button
              type="button"
              className="icon-button"
              aria-label="Adjust filters"
              title="Adjust filters"
              onClick={toggleFilters}
            >
              <SlidersHorizontal size={19} aria-hidden="true" />
            </button>
            <button className="primary-action" onClick={runSelectedTriage} type="button" disabled={isBusy}>
              <Zap size={18} aria-hidden="true" />
              {isBusy ? "Working..." : "Run triage"}
            </button>
          </div>
        </header>

        <section className="metric-strip" aria-label="Resolution metrics">
          {resolutionMetrics.map((metric) => (
            <article className="metric-tile" key={metric.label}>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <em>{metric.delta}</em>
            </article>
          ))}
        </section>

        <section className="live-backend" aria-label="Live backend workflow">
          <div className="live-copy">
            <p className="eyebrow">Backend connected workflow</p>
            <h3>Run a real seeded customer journey</h3>
            <p>
              Uses {API_BASE_URL} with demo credentials, server-side auth, ownership checks, tool
              logs, conversations, citations, and analytics.
            </p>
          </div>
          <div className="live-actions">
            <button
              className="secondary-action"
              onClick={connectDemoBackend}
              type="button"
              disabled={isBusy}
            >
              <ShieldCheck size={17} aria-hidden="true" />
              {isBusy ? "Connecting..." : "Login demo customer"}
            </button>
            <button
              className="secondary-action"
              onClick={loadAgentAnalytics}
              type="button"
              disabled={isBusy}
            >
              <Gauge size={17} aria-hidden="true" />
              {isBusy ? "Loading..." : "Load analytics"}
            </button>
            <button className="secondary-action" onClick={copyDraft} type="button">
              <Copy size={17} aria-hidden="true" />
              Copy draft
            </button>
            <button
              className="secondary-action"
              onClick={runCurrentRequestThroughFlow}
              type="button"
              disabled={isBusy}
            >
              <Bot size={17} aria-hidden="true" />
              Run ordered flow
            </button>
          </div>
          <form className="live-form" onSubmit={submitLiveChat}>
            <input
              value={chatInput}
              onChange={(event) => setChatInput(event.target.value)}
              placeholder="Ask about ORD-1001, refunds, returns, or human escalation"
            />
            <button className="primary-action" type="submit">
              <Send size={17} aria-hidden="true" />
              Send to backend
            </button>
          </form>
          {apiState === "error" ? <p className="api-error">{apiError}</p> : null}
          <p className="action-notice">{actionNotice}</p>
          <div className="live-results">
            <article>
              <span>Orders loaded</span>
              <strong>{orders.length}</strong>
              <p>{orders[0] ? `${orders[0].order_number}: ${orders[0].status}` : "Connect backend first"}</p>
            </article>
            <article>
              <span>Latest intent</span>
              <strong>{chatResult?.intent.intent ?? "None"}</strong>
              <p>{chatResult?.assistant_message.content ?? "Send a message through the API"}</p>
              <div className="feedback-actions">
                <button
                  type="button"
                  aria-label="Mark response helpful"
                  disabled={!chatResult}
                  onClick={() => submitFeedback(1)}
                  title="Mark response helpful"
                >
                  <ThumbsUp size={16} aria-hidden="true" />
                </button>
                <button
                  type="button"
                  aria-label="Mark response needs work"
                  disabled={!chatResult}
                  onClick={() => submitFeedback(-1)}
                  title="Mark response needs work"
                >
                  <ThumbsDown size={16} aria-hidden="true" />
                </button>
              </div>
            </article>
            <article>
              <span>Agent analytics</span>
              <strong>{analytics ? `${analytics.ticket_backlog} backlog` : "Not loaded"}</strong>
              <p>
                {analytics
                  ? `${analytics.total_conversations} conversations, ${Math.round(analytics.human_escalation_rate * 100)}% escalation, ${analytics.rag_citation_count} citations`
                  : "Load analytics with the seeded support-agent role"}
              </p>
              {analytics ? (
                <dl className="analytics-mini">
                  <div>
                    <dt>AI resolved</dt>
                    <dd>{analytics.resolved_by_ai}</dd>
                  </div>
                  <div>
                    <dt>Tool success</dt>
                    <dd>
                      {analytics.tool_success_rate === null
                        ? "n/a"
                        : `${Math.round(analytics.tool_success_rate * 100)}%`}
                    </dd>
                  </div>
                </dl>
              ) : null}
            </article>
          </div>
        </section>

        <section className="orchestration-flow" aria-label="LangGraph and LangChain ordered flow">
          <div className="flow-heading">
            <div>
              <p className="eyebrow">Requested architecture order</p>
              <h3>Customer Support Agent Flow</h3>
            </div>
            <div className="flow-summary">
              <span>{orchestration?.route ?? "No route yet"}</span>
              <strong>
                {orchestration ? `${Math.round(orchestration.quality_score * 100)}% quality` : "Ready"}
              </strong>
            </div>
          </div>
          <div className="agent-diagram">
            <aside className="diagram-label langgraph-label">
              <strong>LANGGRAPH</strong>
              <span>controls the flow</span>
            </aside>
            <aside className="diagram-label langchain-label">
              <strong>LANGCHAIN</strong>
              <span>provides the blocks</span>
            </aside>
            <div className="diagram-main">
              <div className="diagram-row user-row">{renderGraphNode("user", "compact")}</div>
              <div className="diagram-arrow" />
              <div className="orchestrator-row">
                {renderGraphNode("state", "state-node")}
                {renderGraphNode("orchestrator", "orchestrator-node")}
              </div>
              <div className="diagram-split" />
              <div className="node-row">
                {renderGraphNode("billing")}
                {renderGraphNode("technical")}
                {renderGraphNode("general")}
              </div>
              <div className="diagram-arrow" />
              <div className="diagram-row">{renderGraphNode("blocks", "wide-node")}</div>
              <div className="diagram-split" />
              <div className="node-row">
                {renderGraphNode("retriever")}
                {renderGraphNode("llm")}
                {renderGraphNode("tools")}
              </div>
              <div className="node-row subdued-row">
                {renderGraphNode("vector-db")}
                {renderGraphNode("provider")}
                {renderGraphNode("api-functions")}
              </div>
              <div className="diagram-arrow" />
              <div className="diagram-row">{renderGraphNode("evaluator", "evaluator-node")}</div>
              <div className="decision-row">
                {renderGraphNode("good", "decision-node")}
                {renderGraphNode("bad", "decision-node")}
              </div>
              <div className="decision-row">
                {renderGraphNode("response", "decision-node")}
                {renderGraphNode("retry", "decision-node")}
              </div>
              <div className={`retry-rail ${hasRetryEdge ? "active" : ""}`}>
                Retry loops back to orchestrator
              </div>
            </div>
            <aside className="node-inspector">
              <p className="eyebrow">Selected block</p>
              <h4>{selectedGraphNode.label}</h4>
              <span className={`node-status ${selectedGraphNode.status}`}>
                {selectedGraphNode.status}
              </span>
              <p>{selectedGraphNode.detail}</p>
              <pre>{JSON.stringify(selectedGraphNode.metadata, null, 2)}</pre>
            </aside>
          </div>
          <div className="flow-lanes compact-trace">
            {flowSteps.map((step) => (
              <button
                className={`flow-step ${step.status}`}
                key={`${step.order}-${step.name}`}
                type="button"
                onClick={() => setActionNotice(`${step.order}. ${step.name}: ${step.detail}`)}
              >
                <span className="flow-order">{step.order}</span>
                <div>
                  <p>{step.layer}</p>
                  <h4>{step.name}</h4>
                  <span>{step.detail}</span>
                </div>
              </button>
            ))}
          </div>
          <div className="flow-response">
            <span>Final output</span>
            <p>
              {orchestration?.final_response ??
                "Run an order lookup, refund, policy, or escalation request to see the evaluator choose response or retry."}
            </p>
          </div>
        </section>

        <section className="operations-grid">
          <section className="inbox-panel" aria-label="Customer inbox">
            <div className="toolbar">
              <label className="search-box">
                <Search size={17} aria-hidden="true" />
                <input
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                  placeholder="Search customers, topics, tags"
                />
              </label>
              <div className="segmented" role="tablist" aria-label="Priority filter">
                {(["All", "Urgent", "High", "Normal"] as const).map((priority) => (
                    <button
                      type="button"
                      key={priority}
                    className={priorityFilter === priority ? "selected" : ""}
                    onClick={() => setPriorityFilter(priority)}
                  >
                    {priority}
                  </button>
                ))}
              </div>
            </div>

            <div className="ticket-list">
              {filteredTickets.map((ticket) => (
                <button
                  key={ticket.id}
                  className={`ticket-row ${ticket.id === selectedTicket.id ? "selected" : ""}`}
                  onClick={() => setSelectedTicketId(ticket.id)}
                >
                  <span className="ticket-main">
                    <span className="ticket-title-line">
                      <strong>{ticket.subject}</strong>
                      <span className={priorityClass(ticket.priority)}>{ticket.priority}</span>
                    </span>
                    <span className="ticket-meta">
                      {ticket.customer} · {ticket.company} · {ticket.channel}
                    </span>
                    <span className="ticket-summary">{ticket.summary}</span>
                  </span>
                  <span className="ticket-side">
                    <span className={`status-pill ${getStatusTone(ticket.status)}`}>{ticket.status}</span>
                    <span className="sla">
                      <Clock3 size={14} aria-hidden="true" />
                      {ticket.sla}
                    </span>
                  </span>
                </button>
              ))}
            </div>
          </section>

          <section className="case-panel" aria-label="Selected case">
            <div className="case-header">
              <div>
                <p className="eyebrow">{selectedTicket.id}</p>
                <h3>{selectedTicket.subject}</h3>
                <p>{selectedTicket.customer} at {selectedTicket.company}</p>
              </div>
              <button className="secondary-action" onClick={openCrmRecord} type="button">
                <PanelRightOpen size={17} aria-hidden="true" />
                Open CRM
              </button>
            </div>

            <div className="case-facts" aria-label="Case facts">
              <div>
                <span>Sentiment</span>
                <strong>{selectedTicket.sentiment}</strong>
              </div>
              <div>
                <span>Confidence</span>
                <strong>{selectedTicket.confidence}%</strong>
              </div>
              <div>
                <span>Owner</span>
                <strong>{selectedTicket.assignedTo}</strong>
              </div>
              <div>
                <span>Account value</span>
                <strong>{selectedTicket.value}</strong>
              </div>
            </div>

            <div className="conversation-log">
              {selectedTicket.timeline.map((event) => (
                <article className="timeline-item" key={`${event.at}-${event.actor}`}>
                  <div className="timeline-dot" />
                  <div>
                    <div className="timeline-meta">
                      <strong>{event.actor}</strong>
                      <span>{event.at}</span>
                    </div>
                    <p>{event.body}</p>
                  </div>
                </article>
              ))}
            </div>

            <div className="composer">
              <div className="composer-header">
                <div>
                  <p className="eyebrow">AI response draft</p>
                  <h4>Grounded answer</h4>
                </div>
                <div className="tone-control" aria-label="Response tone">
                  {(["Balanced", "Empathetic", "Concise"] as const).map((option) => (
                    <button
                      type="button"
                      key={option}
                      className={tone === option ? "selected" : ""}
                      onClick={() => setTone(option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>
              <p className="draft-copy">{responsePreview}</p>
              <div className="composer-actions">
                <button className="secondary-action" onClick={improveDraft} type="button">
                  <Wand2 size={17} aria-hidden="true" />
                  Improve draft
                </button>
                <button className="secondary-action" onClick={assignHuman} type="button" disabled={isBusy}>
                  <UserRoundCheck size={17} aria-hidden="true" />
                  Assign human
                </button>
                <button className="primary-action" onClick={sendReply} type="button" disabled={isBusy}>
                  <Send size={17} aria-hidden="true" />
                  Send reply
                </button>
              </div>
            </div>
          </section>

          <aside className="insights-panel" aria-label="AI insights">
            <section className="insight-section">
              <div className="section-title">
                <Sparkles size={18} aria-hidden="true" />
                <h3>Agent reasoning</h3>
              </div>
              <div className="reasoning-stack">
                <div className="reasoning-item">
                  <Check size={16} aria-hidden="true" />
                  <span>Intent classified as {selectedTicket.tags[0].toLowerCase()} support.</span>
                </div>
                <div className="reasoning-item">
                  <AlertTriangle size={16} aria-hidden="true" />
                  <span>Escalation threshold is {selectedTicket.priority.toLowerCase()} priority.</span>
                </div>
                <div className="reasoning-item">
                  <MessageSquare size={16} aria-hidden="true" />
                  <span>Reply cites verified account and policy signals.</span>
                </div>
              </div>
            </section>

            <section className="insight-section">
              <div className="section-title">
                <FileSearch size={18} aria-hidden="true" />
                <h3>Knowledge match</h3>
              </div>
              {recommendedArticle ? (
                <article className="knowledge-match">
                  <recommendedArticle.icon size={22} aria-hidden="true" />
                  <div>
                    <strong>{recommendedArticle.title}</strong>
                    <span>{recommendedArticle.updated}</span>
                    <p>{recommendedArticle.excerpt}</p>
                    <em>{recommendedArticle.confidence}% match</em>
                  </div>
                </article>
              ) : null}
            </section>

            <section className="insight-section">
              <div className="section-title">
                <LifeBuoy size={18} aria-hidden="true" />
                <h3>Queues</h3>
              </div>
              <div className="queue-list">
                {queues.map((queue) => (
                  <div className="queue-row" key={queue.label}>
                    <queue.icon size={18} aria-hidden="true" />
                    <span>{queue.label}</span>
                    <strong>{queue.count}</strong>
                    <em>{queue.health}</em>
                  </div>
                ))}
              </div>
            </section>
          </aside>
        </section>

        <section className="automation-band" aria-label="Automation performance">
          {automations.map((automation) => (
            <article className="automation-card" key={automation.title}>
              <div className="automation-icon">
                <automation.icon size={20} aria-hidden="true" />
              </div>
              <div>
                <h3>{automation.title}</h3>
                <p>{automation.detail}</p>
                <strong>{automation.metric}</strong>
                <span>{automation.unit}</span>
              </div>
              <ArrowUpRight size={18} aria-hidden="true" />
            </article>
          ))}
        </section>
      </section>

      <button
        className="mobile-filter"
        aria-label="Open queue options"
        title="Open queue options"
        onClick={toggleFilters}
        type="button"
      >
        <ChevronDown size={20} aria-hidden="true" />
      </button>
    </main>
  );
}

export default App;

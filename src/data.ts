import type { LucideIcon } from "lucide-react";
import {
  Banknote,
  Bot,
  Cable,
  MessageSquareWarning,
  PackageCheck,
  ShieldCheck,
  Sparkles,
  Truck,
} from "lucide-react";

export type TicketStatus = "AI drafting" | "Waiting on customer" | "Needs agent" | "Ready to send";
export type TicketPriority = "Urgent" | "High" | "Normal";
export type TicketChannel = "Email" | "Chat" | "WhatsApp" | "Voice";

export type TimelineEvent = {
  at: string;
  actor: string;
  body: string;
};

export type Ticket = {
  id: string;
  customer: string;
  company: string;
  subject: string;
  summary: string;
  status: TicketStatus;
  priority: TicketPriority;
  channel: TicketChannel;
  sentiment: "Positive" | "Neutral" | "Frustrated" | "At risk";
  confidence: number;
  sla: string;
  assignedTo: string;
  value: string;
  tags: string[];
  timeline: TimelineEvent[];
  suggestedAnswer: string;
};

export type KnowledgeArticle = {
  id: string;
  title: string;
  topic: string;
  confidence: number;
  updated: string;
  excerpt: string;
  icon: LucideIcon;
};

export const tickets: Ticket[] = [
  {
    id: "CX-1048",
    customer: "Nora Patel",
    company: "Aster Home",
    subject: "Subscription renewed after cancellation",
    summary:
      "Customer cancelled on September 30 but was charged on October 8. She wants a refund and confirmation that the workspace is closed.",
    status: "AI drafting",
    priority: "Urgent",
    channel: "Email",
    sentiment: "At risk",
    confidence: 92,
    sla: "34 min",
    assignedTo: "Priya S.",
    value: "$14.8k ARR",
    tags: ["Billing", "Cancellation", "Refund"],
    timeline: [
      {
        at: "10:14",
        actor: "Customer",
        body: "I cancelled before renewal and still got charged. I need this fixed today.",
      },
      {
        at: "10:16",
        actor: "AI Agent",
        body: "Verified cancellation event and matched it to a post-cancellation renewal charge.",
      },
      {
        at: "10:19",
        actor: "Policy Engine",
        body: "Eligible for full refund under renewal grace policy. Human approval recommended.",
      },
    ],
    suggestedAnswer:
      "You are right to flag this. I found your cancellation request from September 30 and the renewal charge from October 8 should not have gone through. I can issue a full refund to the original payment method and close the workspace so there are no further renewals. Refunds usually appear within 5-7 business days.",
  },
  {
    id: "CX-1049",
    customer: "Marcus Ellison",
    company: "Northline Studio",
    subject: "Webhook failures after API key rotation",
    summary:
      "Integration stopped delivering order updates after a secret rotation. Logs show 401 responses from the customer's endpoint.",
    status: "Needs agent",
    priority: "High",
    channel: "Chat",
    sentiment: "Frustrated",
    confidence: 81,
    sla: "1 hr 12 min",
    assignedTo: "Dev Queue",
    value: "$42.0k ARR",
    tags: ["API", "Webhook", "Enterprise"],
    timeline: [
      {
        at: "09:42",
        actor: "Customer",
        body: "The dashboard says events are sent, but nothing lands in our ERP.",
      },
      {
        at: "09:46",
        actor: "AI Agent",
        body: "Detected failed delivery attempts and compared signatures against the active secret.",
      },
      {
        at: "09:50",
        actor: "Routing",
        body: "Escalated because this customer has enterprise support and production integration risk.",
      },
    ],
    suggestedAnswer:
      "I checked the delivery log and the events are leaving our platform, but your endpoint is returning 401 after the key rotation. The most likely fix is updating the receiving service with the new signing secret, then replaying the failed events from the webhook log. I can stay with you while we test one replay before sending the backlog.",
  },
  {
    id: "CX-1050",
    customer: "Ava Chen",
    company: "BrightCart",
    subject: "Package marked delivered but not received",
    summary:
      "Customer says tracking shows delivered yesterday, but the package is missing. Carrier photo appears to show a neighboring entrance.",
    status: "Ready to send",
    priority: "Normal",
    channel: "WhatsApp",
    sentiment: "Neutral",
    confidence: 88,
    sla: "3 hr 04 min",
    assignedTo: "AI Autopilot",
    value: "$540 LTV",
    tags: ["Shipping", "Carrier", "Replacement"],
    timeline: [
      {
        at: "08:28",
        actor: "Customer",
        body: "It says delivered but I do not have it. The photo is not my door.",
      },
      {
        at: "08:29",
        actor: "AI Agent",
        body: "Matched tracking photo against saved address notes and identified likely carrier misdelivery.",
      },
    ],
    suggestedAnswer:
      "Thanks for sending that. The delivery photo does not look like the entrance on your saved address, so I am opening a carrier trace and sending a replacement today. If the original package arrives, you can keep it or return it with the prepaid label we will email.",
  },
  {
    id: "CX-1051",
    customer: "Daniel Ortiz",
    company: "Cobalt Finance",
    subject: "SSO login loop for new employees",
    summary:
      "Newly provisioned users are bounced between identity provider and app. Existing users can sign in successfully.",
    status: "Waiting on customer",
    priority: "High",
    channel: "Voice",
    sentiment: "Positive",
    confidence: 76,
    sla: "2 hr 21 min",
    assignedTo: "Lena T.",
    value: "$96.3k ARR",
    tags: ["SSO", "Identity", "Admin"],
    timeline: [
      {
        at: "11:01",
        actor: "Customer",
        body: "We onboarded 18 people and all new accounts are stuck in a login loop.",
      },
      {
        at: "11:09",
        actor: "Agent",
        body: "Asked admin to confirm the new group has the same SAML attributes as the existing group.",
      },
    ],
    suggestedAnswer:
      "The pattern points to a missing SAML attribute on the new employee group because existing users can still sign in. Could you confirm whether the new group sends email, first_name, last_name, and role attributes? Once we have that, I can validate the mapping and unlock the group.",
  },
];

export const knowledgeArticles: KnowledgeArticle[] = [
  {
    id: "KB-212",
    title: "Renewal refund grace policy",
    topic: "Billing",
    confidence: 96,
    updated: "Updated 2 days ago",
    excerpt: "Full refunds are approved when cancellation happened before renewal and charge capture occurred afterward.",
    icon: Banknote,
  },
  {
    id: "KB-118",
    title: "Webhook signing secret rotation",
    topic: "API",
    confidence: 91,
    updated: "Updated Sep 18",
    excerpt: "After rotating a signing secret, receiving services must accept the new signature before event replay.",
    icon: Cable,
  },
  {
    id: "KB-304",
    title: "Carrier misdelivery playbook",
    topic: "Shipping",
    confidence: 88,
    updated: "Updated Sep 30",
    excerpt: "Use replacement-first workflow when carrier evidence conflicts with customer address metadata.",
    icon: Truck,
  },
  {
    id: "KB-527",
    title: "Enterprise SSO attribute mapping",
    topic: "Identity",
    confidence: 84,
    updated: "Updated Aug 12",
    excerpt: "New groups must expose required SAML attributes before app access is granted.",
    icon: ShieldCheck,
  },
];

export const automations = [
  {
    title: "Autopilot triage",
    detail: "Classifies intent, risk, channel, and SLA before routing.",
    metric: "1.8k",
    unit: "tickets today",
    icon: Bot,
  },
  {
    title: "Policy guardrails",
    detail: "Blocks unsafe refunds, privacy leaks, and off-policy commitments.",
    metric: "99.2%",
    unit: "compliance pass",
    icon: ShieldCheck,
  },
  {
    title: "Resolution quality",
    detail: "Scores tone, completeness, citations, and next-best action.",
    metric: "4.8",
    unit: "CSAT forecast",
    icon: Sparkles,
  },
  {
    title: "Exception handling",
    detail: "Routes ambiguous or high-value cases to trained specialists.",
    metric: "7.4%",
    unit: "human handoff",
    icon: MessageSquareWarning,
  },
];

export const resolutionMetrics = [
  { label: "Automated resolution", value: "68%", delta: "+12%" },
  { label: "Median first response", value: "38s", delta: "-24s" },
  { label: "SLA breach risk", value: "3.1%", delta: "-1.7%" },
  { label: "Deflection savings", value: "$42k", delta: "+18%" },
];

export const queues = [
  { label: "Billing", count: 42, health: "Stable", icon: Banknote },
  { label: "Technical", count: 28, health: "Elevated", icon: Cable },
  { label: "Shipping", count: 64, health: "Stable", icon: PackageCheck },
  { label: "Risk", count: 9, health: "Watch", icon: ShieldCheck },
];

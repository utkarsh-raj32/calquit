# Product Note

## Addressed Client Problems

We chose to implement **both** additional client problems to provide a comprehensive, production-ready solution.

1. **Problem 1: Proactive Issue Detection**
   - **Solution**: We built the **Operations Dashboard** (`/dashboard`). It actively scans open tickets and orders to surface SLA breaches, SLA at-risk tickets, and groups recurring issues (e.g., the bulk upload failure pattern) automatically.
   - **Why it matters**: Support isn't just about answering tickets faster; it's about identifying systemic issues so product teams can fix them before they generate *more* tickets.

2. **Problem 2: Trust and Reliability**
   - **Solution**: We implemented a **Source Reliability Engine**. The backend tags documents with authoritative tiers. The LangGraph agent is explicitly instructed on how to resolve conflicts (Agreement > SOP > Historical).
   - **Why it matters**: If an agent confidently enforces a cancellation fee on an Enterprise customer who has a fee-waiver in their contract, that customer will churn. Correctness is paramount in B2B logistics.

## Future Development (Think Beyond)
If continuing work on ParcelPilot, I would prioritize:
1. **Automated Triage & Routing**: Use the LLM to automatically categorize incoming tickets, assign severity, and route them to the correct human queue before an agent even opens them.
2. **"Drafting" Mode for Internal Agents**: Instead of the AI answering the customer directly on complex queries, the AI drafts a response and attaches internal citations for human review.
3. **Carrier API Integrations**: Tools that allow the agent to directly query carrier tracking APIs (e.g., SwiftShip) rather than relying purely on internal DB state.

## What Was Intentionally Left Out
- **Database Persistence**: We used in-memory Pandas dataframes and ChromaDB rather than a persistent Postgres DB. For a real launch, state changes (like escalations) would commit to a real database.
- **WebSocket Chat**: We used Server-Sent Events (SSE) for streaming. While excellent for one-way token streaming, true bidirectional real-time chat (with typing indicators from humans) would require WebSockets.

## Success Metric
**Primary Metric**: Resolution Rate Without Escalation.
- **Why**: The goal of the AI is to handle standard queries fully autonomously. If a user asks a question, gets an answer, and does not subsequently click "Create Ticket" or "Escalate to Human" within 24 hours, the AI successfully resolved the issue.

# Architecture Note

## Agent Design
The system uses a **LangGraph-based state machine** driven by the Gemini 2.0 Flash model. 
- **Multi-step Reasoning**: LangGraph enables cyclic execution, allowing the agent to call a tool, parse the result, and call subsequent tools before synthesizing a final answer to the user.
- **Context Segregation**: The agent dynamically injects different system prompts based on the user's role. The customer prompt is constrained and protective of data, while the internal prompt is highly analytical and highlights source conflicts.

## Tool Design
The agent uses three primary tool classes:
1. **Document Search (RAG)**: Uses ChromaDB with Gemini embeddings to retrieve relevant chunks of markdown policies and agreements.
2. **Data Lookup & Calculation**: Python functions over Pandas DataFrames. Instead of making the LLM write SQL or do math, the backend handles complex business logic (e.g., calculating SLAs, cancellation fees) deterministically.
3. **State-Changing Actions**: All mutative actions (escalate, cancel, credit) push a "pending" record to the server and stream a structured JSON block to the frontend. The frontend intercepts this and renders an action confirmation modal. The action only executes when the user clicks "Confirm".

## Document and Structured-Data Handling
- **Data Access Layer**: Access control is enforced in the tool/data layer, *not* in the LLM prompt. If a customer tries to query `lookup_order("ORD-4001")` (which belongs to a different account), the data layer simply returns `null/Not Found`.
- **Hybrid Retrieval**: The agent combines semantic search (documents) with structured deterministic queries (Excel data).

## Source Reliability and Conflict Handling (Trust Engine)
To solve the "Trust" problem, documents are indexed with a `reliability_tier` (1 = Signed Agreement, 5 = Deprecated Policy).
- When the LLM retrieves documents, the context includes these reliability labels explicitly.
- The system prompt instructs the agent to enforce **Source Precedence**: Agreement > Current SOP > General Docs > Historical Tickets.
- If the agent detects that a historical ticket contradicts a higher-tier document, it explicitly flags the historical resolution as potentially incorrect.

## Major Technical Trade-offs
1. **In-Memory vs Database**: We used Pandas and ChromaDB locally rather than standing up Postgres and Pinecone to optimize for evaluation simplicity and self-containment.
2. **Mock Authentication**: Used simple JWTs mapped to hardcoded users rather than integrating OAuth, keeping the focus on the AI implementation rather than auth plumbing.
3. **Tool-based Calculation vs LLM Math**: We chose to offload fee calculations and SLA time-math to deterministic Python functions (tools) because LLMs are notoriously unreliable at date math and exact business logic.

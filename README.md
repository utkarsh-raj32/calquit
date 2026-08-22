# 🚀 ParcelPilot AI — Autonomous Support & Operations System

> **A production-ready, dual-context AI agent system built for logistics support, featuring RAG Source-Precedence, Human-in-the-Loop Action Confirmation, and Proactive Operations Insights.**

Built with **FastAPI**, **LangGraph**, **Google Gemini**, **ChromaDB**, **Next.js 15**, and **Tailwind CSS**.

---

## 📑 Table of Contents
- [✨ Core Capabilities](#-core-capabilities)
- [🛠️ Tech Stack](#️-tech-stack)
- [🚀 Quick Start (Local Setup)](#-quick-start-local-setup)
- [🧪 Evaluation & Demo Walkthrough (What to Ask)](#-evaluation--demo-walkthrough-what-to-ask)
  - [Scenario 1: Customer Agreement Precedence (Fee Waiver)](#scenario-1-customer-agreement-precedence-fee-waiver)
  - [Scenario 2: Custom Service Credit Calculation](#scenario-2-custom-service-credit-calculation)
  - [Scenario 3: Role-Based Knowledge Isolation (Security Test)](#scenario-3-role-based-knowledge-isolation-security-test)
  - [Scenario 4: Human-in-the-Loop Action Confirmation](#scenario-4-human-in-the-loop-action-confirmation)
  - [Scenario 5: Proactive Operations & Outage Dashboard](#scenario-5-proactive-operations--outage-dashboard)
- [🏛️ Architecture & Product Notes](#️-architecture--product-notes)

---

## ✨ Core Capabilities

1. **Dual-Context Persona Architecture**:
   - **Customer View**: Strict data boundary isolated to their account, deterministic business calculations, and policy guidance.
   - **Internal Staff View**: Cross-account visibility, access to internal operations guides, source conflict flags, and sensitive actions.
2. **Trust & Reliability Engine (RAG with Source Precedence)**:
   - Enforces hierarchical document authority: `Signed Agreement (Tier 1) > Active SOP (Tier 2) > General Policy (Tier 3) > Deprecated/Historical (Tier 4/5)`.
   - Prevents AI hallucinations and contractual violations.
3. **Human-in-the-Loop Action Confirmation**:
   - High-impact mutations (e.g. ticket escalations, refund dispatches) trigger a real-time pending action queue with approval modals before execution.
4. **Proactive Operations Insights**:
   - Real-time SLA breach detection tailored by customer tier and automatic grouping of correlated incidents (e.g. Bulk Upload outages).

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **AI Agent Orchestration** | LangGraph, LangChain Core |
| **LLM & Embeddings** | Google Gemini (`gemini-3.6-flash`, `gemini-embedding-001`) |
| **Vector Store** | ChromaDB (In-Memory with Document Metadata Tiers) |
| **Backend API** | FastAPI, Pydantic, Pandas, Server-Sent Events (SSE) |
| **Frontend UI** | Next.js 15 (App Router, Turbopack), Tailwind CSS, Lucide Icons |

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- **Node.js** (v18 or higher)
- **Python** (v3.10 or higher)
- **Google Gemini API Key** ([Get one here](https://aistudio.google.com/app/apikey))

---

### 2. Backend Setup
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate a Python virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
# Copy .env.example to .env and add your Gemini API Key:
cp .env.example .env
```

Ensure `backend/.env` contains:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

Start the backend server:
```bash
uvicorn app.main:app --reload --port 8000
```
*Backend runs at `http://localhost:8000` (Swagger docs at `http://localhost:8000/docs`).*

---

### 3. Frontend Setup
In a new terminal window:
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start the Next.js development server
npm run dev
```
*Frontend runs at `http://localhost:3000`.*

---

## 🧪 Evaluation & Demo Walkthrough (What to Ask)

Open `http://localhost:3000` in your browser. You will see the persona switcher. Follow these 5 test scenarios to evaluate all assignment requirements:

---

### Scenario 1: Customer Agreement Precedence (Fee Waiver)
* **Persona**: Log in as **Vikram Singh (Northstar Logistics - Customer)**
* **Prompt to paste**:
  ```text
  I want to cancel order ORD-1001. Will I be charged a cancellation fee?
  ```
* **Expected Behavior**:
  - The AI executes `calculate_cancellation_fee(order_id="ORD-1001")`.
  - While standard SOP v4 charges INR 250 for cancellations > 30 minutes, the AI identifies **Northstar's Enterprise Agreement (Tier 1)** which grants a 100% fee waiver for any BOOKED shipment prior to pickup.
  - The AI correctly informs Vikram that **0 fee** will be charged.

---

### Scenario 2: Custom Service Credit Calculation
* **Persona**: Log in as **Ananya Roy (LumenWorks - Customer)**
* **Prompt to paste**:
  ```text
  My order ORD-1002 was picked up late due to carrier fault. Can I get a service credit?
  ```
* **Expected Behavior**:
  - The AI executes `calculate_service_credit(order_id="ORD-1002")`.
  - Checks carrier fault (True) and calculates pickup delay.
  - Standard SOP v4 caps credit at 10% / max INR 500. However, the AI identifies **LumenWorks' custom Service Agreement** which mandates a fixed **INR 300** credit for delays $\ge 4$ hours.
  - The AI correctly calculates and quotes **INR 300**.

---

### Scenario 3: Role-Based Knowledge Isolation (Security Test)
* **Step A (Customer)**: Log in as **Vikram Singh (Customer)** and ask:
  ```text
  Are there any known issues with the Bulk Upload feature today?
  ```
  - **Result**: The agent searches documents and correctly states there are no public issues reported.
* **Step B (Staff)**: Log out, log in as **Maya Desai (Internal Support Agent)** and ask the exact same prompt:
  ```text
  Are there any known issues with the Bulk Upload feature today?
  ```
  - **Result**: The AI accesses the restricted **Product Operations Guide & Known Issues** (Tier 2 Internal) and details the current Bulk Upload bug along with the internal engineering workaround.

---

### Scenario 4: Human-in-the-Loop Action Confirmation
* **Persona**: Log in as **Maya Desai (Internal Support Agent)**
* **Prompt to paste**:
  ```text
  Can you look up ticket TKT-501? The customer is experiencing an outage and is furious. Please escalate this ticket immediately.
  ```
* **Expected Behavior**:
  1. The AI looks up ticket `TKT-501`.
  2. The AI calls `escalate_ticket(ticket_id="TKT-501")`.
  3. Because escalation is a sensitive action, the system **pauses execution** and triggers a real-time **Action Required** toast in the top-right corner.
  4. Click **"Confirm"** on the toast to authorize the action.

---

### Scenario 5: Proactive Operations & Outage Dashboard
* **Persona**: Log in as any Internal Staff member (**Maya Desai** or **Rohit Kumar**).
* **Action**: Click **"Ops Dashboard"** in the sidebar (or visit `http://localhost:3000/dashboard`).
* **Expected Behavior**:
  - **SLA Breach Monitoring**: Displays tickets categorized as *Breached*, *At Risk*, or *Healthy* based on custom SLA targets (e.g. Northstar Enterprise P1 SLA of 15 min).
  - **Automated Incident Correlation**: Automatically detects and groups recurring tickets relating to the "Bulk Upload Outage" with severity indicators.

---

## 🏛️ Architecture & Product Notes

For deep-dive documentation on design choices, data flow, and trade-offs, refer to:
* 📄 [`ARCHITECTURE.md`](ARCHITECTURE.md) — Technical details on LangGraph state, ChromaDB tier filtering, tool safety, and data flow.
* 📄 [`PRODUCT.md`](PRODUCT.md) — Product rationale, client problem breakdown, future development roadmap, and core success metrics.

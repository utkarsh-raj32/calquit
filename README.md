# ParcelPilot AI Support System

A dual-context AI support agent built for ParcelPilot, handling both customer queries and internal operations workflows.

## Prerequisites
- Node.js (v18+)
- Python 3.10+
- A Google Gemini API Key

## Setup & Run Locally

### 1. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
# GEMINI_API_KEY=your_key_here

# Run the backend
uvicorn app.main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install

# Run the frontend
npm run dev
```

### 3. Usage
- Open `http://localhost:3000` in your browser.
- Select a persona (e.g., Northstar Logistics for the customer view, or Rohit Sharma for the internal agent).
- Test queries like:
  - *"Can I cancel ORD-1001? Is there a fee?"*
  - *"ORD-2002 was missed by the carrier. Can I get a service credit?"*
- Switch to the Ops Dashboard to see proactive SLA alerts and detected issue patterns.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for details on the agent and tool design.

## Product Note

See [PRODUCT.md](PRODUCT.md) for details on the product decisions and additional client problems solved.

# Open Design & Backend Integration Guide

This guide explains how to use **Open Design** (`nexu-io/open-design`) to generate modern frontend interfaces and connect them to a backend server (such as your FastAPI application).

---

## 1. What is Open Design?

[Open Design](https://github.com/nexu-io/open-design) is an open-source, local-first AI workspace. Think of it as a local version of Claude's Artifacts or Design Mode, but integrated directly with your own AI coding agents (like Cursor, Claude Code, or Gemini).
- It generates raw design assets, web prototypes, dashboards, and pages on your local disk.
- The output is standard web code (typically React, Vite, Tailwind, or plain HTML/CSS/JS).

---

## 2. Setting Up & Running Open Design

To run Open Design locally:

### Prerequisites
* **Node.js**: Version 24 (Node 22 is not supported).
* **pnpm**: Version 10+ (enable via `corepack enable pnpm`).
* An AI agent CLI (like Claude Code, Cursor CLI, etc.) in your system `PATH` (optional but recommended for agentic capabilities).

### Installation
Run these commands in a separate terminal directory (outside your current project):
```bash
# 1. Clone the repository
git clone https://github.com/nexu-io/open-design.git
cd open-design

# 2. Install dependencies
pnpm install

# 3. Start the dev server / local daemon
pnpm tools-dev
```
Once started, open the web UI at the URL printed in the terminal (usually `http://127.0.0.1:17573`).

---

## 3. How to Build Frontends with Open Design

When you use Open Design's UI or prompt system:
1. It creates project folders inside `.od/projects/` on your disk.
2. The generated code uses standard components (e.g., using Tailwind CSS, React, Lucide icons, and Recharts).
3. **Copying to Your Project**: Once you are happy with a generated page or component (e.g., a dashboard or trading chart page), copy the code or file into your main project workspace (e.g., into `dashboard/src/pages/` or `dashboard/src/components/`).

---

## 4. How to Integrate the Frontend with Your Backend

Open Design outputs static frontends using **mock data** (hardcoded arrays or state variables). To connect it to your backend, follow these steps:

### Step A: Configure CORS in your FastAPI Backend
For your React/Vite app (running on `http://localhost:5173`) to query your FastAPI server (running on `http://localhost:8000`), you must enable CORS in FastAPI:

```python
# In your FastAPI main.py / app entry point:
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow your local React app port
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Step B: Replace Mock Data with API Fetching in React
Open Design will generate code that looks like this:

#### ❌ BEFORE (Open Design Generated Mock Data)
```jsx
import React from 'react';

const mockTrades = [
  { id: 1, symbol: "RELIANCE", action: "BUY", price: 2450 },
  { id: 2, symbol: "TCS", action: "SELL", price: 3400 }
];

export default function TradeDashboard() {
  return (
    <div>
      {mockTrades.map(trade => (
        <p key={trade.id}>{trade.symbol}: {trade.action} @ {trade.price}</p>
      ))}
    </div>
  );
}
```

####  AFTER (Connected to FastAPI Backend)
```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios'; // or use native fetch()

export default function TradeDashboard() {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch data from FastAPI endpoint
    axios.get('http://localhost:8000/api/v1/trades')
      .then(response => {
        setTrades(response.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching trades:", err);
        setError("Failed to load trades.");
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading trades...</div>;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div>
      {trades.map(trade => (
        <p key={trade.id}>{trade.symbol}: {trade.action} @ {trade.price}</p>
      ))}
    </div>
  );
}
```

---

### Step C: Configure Vite Proxy (Optional, Recommended)
Instead of hardcoding `http://localhost:8000` in every API call, configure a proxy in `vite.config.js`. This prevents CORS issues and simplifies deployments.

Modify `dashboard/vite.config.js`:
```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});
```

Now, in your React components, you can fetch simply from `/api/v1/trades`:
```javascript
axios.get('/api/v1/trades')
```

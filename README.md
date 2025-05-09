"""
# AI Expense Tracker

Repo for Build with Windsurf Bangalore Hackathon - AI expense tracker
"""
## Setup

Follow these steps to create and activate the Conda environment, and install dependencies:

```bash
# Create the Conda environment and install Python
conda env create -f environment.yml
# Activate the environment
conda activate build-with-windsurf-hackathon-ai-expense-tracker
``` 

Once activated, the required dependencies (from `requirements.txt`) are installed automatically.

Next, set up your environment variables:

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY in the new file
# Optionally, adjust OPENAI_MODEL (default gpt-4.1-nano) to manage cost/quality
```
---
## Frontend (Next.js)

A modern React/Tailwind frontend has been scaffolded in `frontend/` using Next.js 13.

Setup & Run:
```bash
# Start FastAPI backend (port 8000):
uvicorn app.main:app --reload

# In another terminal, navigate to the frontend and install:
cd frontend
npm install
# (Optional) initialize shadcn-ui components:
# npm install shadcn && npx shadcn init
npm run dev
```

Visit http://localhost:3000 to interact with the chat-style UI. Ensure the backend is reachable at `NEXT_PUBLIC_API_URL` (default http://localhost:8000).

To start the development server:
```bash
uvicorn app.main:app --reload

## API Endpoints

Once the server is running, you can interact with these endpoints:

### Create Expense
POST /api/expenses
Request Body (application/json):
```json
{ "text": "Bought coffee for $4 at Starbucks on 2025-04-20" }
```
Response: JSON of the created expense, e.g.: 
```json
{
  "id": 1,
  "timestamp": "2025-04-20T00:00:00",
  "amount": 4.0,
  "category": "beverage",
  "description": "coffee at Starbucks",
  "raw_nl": "Bought coffee for $4 at Starbucks on 2025-04-20"
}
```

### List Expenses
GET /api/expenses
Optional Query Parameters:
- `start_date` (YYYY-MM-DD)
- `end_date` (YYYY-MM-DD)
- `category` (string)

Example:
```bash
curl "http://localhost:8000/api/expenses?start_date=2025-04-01&end_date=2025-04-30&category=food"
```

### Ask AI for Insights or Queries
POST /api/ask
Request Body (application/json):
```json
{ "text": "How much did I spend on groceries last month?" }
```
Response: Varies based on AI decision. Example:
```json
{
  "action": "summarize_expenses",
  "summary": { "total": 125.5, "breakdown": [...] }
}
```
```

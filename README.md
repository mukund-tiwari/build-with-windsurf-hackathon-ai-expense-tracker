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
# Optionally, adjust OPENAI_MODEL (default gpt-3.5-turbo) to manage cost/quality
```

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

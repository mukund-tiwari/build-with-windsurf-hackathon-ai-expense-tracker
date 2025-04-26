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
# Optionally, adjust OPENAI_MODEL (default gpt-3.5-turbo-0613) to manage cost/quality
```

To start the development server:
```bash
uvicorn app.main:app --reload
```

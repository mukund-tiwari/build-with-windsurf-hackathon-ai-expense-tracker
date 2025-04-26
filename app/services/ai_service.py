import json
import openai

from app.config import OPENAI_API_KEY, OPENAI_MODEL

# Load OpenAI API key
openai.api_key = OPENAI_API_KEY

# Define function schemas for OpenAI function-calling
parse_expense_fn = {
    "name": "parse_expense",
    "description": "Parse a natural language expense entry into structured fields.",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Date of the expense in ISO format (YYYY-MM-DD)."
            },
            "amount": {
                "type": "number",
                "description": "Monetary amount of the expense."
            },
            "description": {
                "type": "string",
                "description": "A brief description of the expense."
            },
            "category": {
                "type": "string",
                "description": "Category of the expense, e.g., food, transportation."
            }
        },
        "required": ["date", "amount", "description"]
    }
}

query_expenses_fn = {
    "name": "query_expenses",
    "description": "Query stored expenses using optional filters.",
    "parameters": {
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "Start date for filtering (ISO format YYYY-MM-DD)."
            },
            "end_date": {
                "type": "string",
                "description": "End date for filtering (ISO format YYYY-MM-DD)."
            },
            "category": {
                "type": "string",
                "description": "Category name to filter by."
            }
        }
    }
}

summarize_expenses_fn = {
    "name": "summarize_expenses",
    "description": "Summarize expenses over a period, optionally by granularity.",
    "parameters": {
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "Start date for summary (ISO format YYYY-MM-DD)."
            },
            "end_date": {
                "type": "string",
                "description": "End date for summary (ISO format YYYY-MM-DD)."
            },
            "granularity": {
                "type": "string",
                "enum": ["daily", "weekly", "monthly"],
                "description": "Time granularity for the summary."
            }
        }
    }
}

# Aggregate the available functions
FUNCTION_DEFINITIONS = [
    parse_expense_fn,
    query_expenses_fn,
    summarize_expenses_fn,
]

def call_openai(user_input: str) -> dict:
    """
    Call OpenAI ChatCompletion with function-calling enabled.
    Returns the assistant message (may include a function_call).
    """
    # System prompt guiding the assistant
    system_prompt = (
        "You are an AI assistant for an expense tracker. "
        "Decide whether to call one of the available functions to parse, query, or summarize expenses."
    )
    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        functions=FUNCTION_DEFINITIONS,
        function_call="auto",
    )
    # Return the assistant's message (with potential function_call)
    return response["choices"][0]["message"]

def parse_expense(nl_text: str) -> dict:
    """
    Parse a natural-language expense entry into structured fields via OpenAI.
    Returns a dict with keys: date, amount, description, category (if provided).
    """
    message = call_openai(nl_text)
    if message.get("function_call", {}).get("name") == "parse_expense":
        args = json.loads(message["function_call"]["arguments"])
        return args
    raise RuntimeError(f"Unexpected response from LLM: {message}")

def query_expenses(nl_text: str) -> dict:
    """
    Convert a natural-language query into structured filters for querying expenses.
    Returns a dict with optional keys: start_date, end_date, category.
    """
    message = call_openai(nl_text)
    if message.get("function_call", {}).get("name") == "query_expenses":
        return json.loads(message["function_call"]["arguments"])
    raise RuntimeError(f"Unexpected response from LLM: {message}")

def summarize_expenses(nl_text: str) -> dict:
    """
    Convert a natural-language request into summary parameters.
    Returns a dict with optional keys: start_date, end_date, granularity.
    """
    message = call_openai(nl_text)
    if message.get("function_call", {}).get("name") == "summarize_expenses":
        return json.loads(message["function_call"]["arguments"])
    raise RuntimeError(f"Unexpected response from LLM: {message}")
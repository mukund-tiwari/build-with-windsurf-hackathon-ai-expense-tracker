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
# Aggregate the available functions
FUNCTION_DEFINITIONS = [
    parse_expense_fn,
    query_expenses_fn,
    summarize_expenses_fn,
    # Retrieve the most recent expense record
    {
        "name": "get_last_expense",
        "description": "Get the most recent expense record, including participants if any.",
        "parameters": {"type": "object", "properties": {}}
    },
    # Compute equal share for a participant
    {
        "name": "split_expense",
        "description": "Compute the equal share for a participant in a given expense.",
        "parameters": {
            "type": "object",
            "properties": {
                "expense_id": {"type": "integer", "description": "ID of the expense to split."},
                "participant": {"type": "string", "description": "Participant name or 'me' for yourself."}
            },
            "required": ["expense_id"]
        }
    },
    # Retrieve the expense with the highest amount
    {
        "name": "get_most_expensive_expense",
        "description": "Get the expense record with the highest amount.",
        "parameters": {"type": "object", "properties": {}}
    },
    # Execute an arbitrary read-only SQL SELECT query on the expenses table
    {
        "name": "run_sql",
        "description": "Run a read-only SQL SELECT query against the expenses table.",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A SQL SELECT statement on the expense table."
                }
            },
            "required": ["sql"]
        }
    },
]

def call_openai(user_input: str) -> dict:
    """
    Call OpenAI ChatCompletion with function-calling enabled.
    Returns the assistant message (may include a function_call).
    """
    # System prompt guiding the assistant: explicit instructions for when to call each function
    system_prompt = (
        "You are an AI assistant for an expense tracker. "
        "When the user provides details of a new expense (mentions amount, date, description, category), always call the parse_expense function. "
        "When the user asks about stored expenses, use query_expenses. "
        "When the user wants an overall summary, use summarize_expenses. "
        "When the user requests the most recent entry explicitly, use get_last_expense. "
        "When splitting a bill among participants, use split_expense. "
        "When the user asks for the most expensive or highest expense ever, use get_most_expensive_expense. "
        "For other insights (e.g., second-highest expense, total spending, average), generate an appropriate SQL SELECT query and call run_sql."
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
SEMANTIC_TAGGING_PROMPT = """
You are an enterprise semantic governance engine.

Your task is to classify document chunks
using ONLY the allowed semantic tags.

IMPORTANT RULES:
- ONLY use tags from the allowed tags list
- DO NOT invent new tags
- DO NOT explain anything
- Return ONLY a JSON array
- If no tag matches, return []

Available Roles:
{roles}

Allowed Tags:
{tags}

Example Output:
["salary", "employee_data"]

Chunk:
{content}
"""
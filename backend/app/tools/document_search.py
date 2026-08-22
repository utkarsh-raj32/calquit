"""Tool 1: Document Search/Retrieval.

Searches ParcelPilot policy documents, agreements, SOPs, and product
documentation using RAG with access control.
"""

from langchain_core.tools import tool
from typing import Optional

from app.data.vectorstore import search_documents
from app.auth.models import UserContext

# The user context will be bound at runtime via tool injection
_current_user: Optional[UserContext] = None


def set_user_context(user: UserContext):
    global _current_user
    _current_user = user


@tool
def document_search(query: str, doc_type: Optional[str] = None) -> str:
    """Search ParcelPilot policy documents, customer agreements, SOPs, and product documentation.

    Use this tool when you need to find information about:
    - Support policies (severity levels, response times, escalation rules)
    - Cancellation and service credit rules
    - Customer-specific agreement terms
    - Product features, known issues, and operational guides

    Args:
        query: The search query describing what information you need.
        doc_type: Optional filter - one of 'policy', 'sop', 'agreement', 'ops_guide'.

    Returns:
        Relevant document excerpts with source attribution and reliability info.
    """
    if _current_user is None:
        return "Error: No user context set. Cannot perform search."

    results = search_documents(query, _current_user, top_k=5, doc_type=doc_type)

    if not results:
        return "No relevant documents found for this query."

    output_parts = []
    for i, r in enumerate(results, 1):
        reliability_label = {
            1: "HIGHEST (Signed Customer Agreement)",
            2: "HIGH (Current Policy/SOP)",
            3: "MEDIUM (Current Product Docs)",
            4: "LOW (Historical Context)",
            5: "DEPRECATED (Do Not Use for Current Requests)",
        }.get(r["reliability_tier"], "UNKNOWN")

        output_parts.append(
            f"--- Source {i} ---\n"
            f"Document: {r['source']}\n"
            f"Type: {r['doc_type']} | Status: {r['status']} | Effective: {r['effective_date']}\n"
            f"Reliability: {reliability_label}\n"
            f"Relevance: {r['relevance_score']}\n"
            f"Content:\n{r['content']}\n"
        )

    return "\n".join(output_parts)

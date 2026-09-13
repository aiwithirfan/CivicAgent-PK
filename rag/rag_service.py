from typing import Any

from .groq_service import generate_structured_response
from .prompts import build_rag_prompt
from .retriever import retrieve_policies


def retrieve_context(
    complaint: str,
    top_k: int = 3,
) -> dict[str, Any]:
    """
    Retrieve relevant civic policies for a complaint.
    """

    results = retrieve_policies(
        complaint=complaint,
        top_k=top_k,
    )

    policies = []

    for result in results:
        policies.append(
            {
                "id": result["id"],
                "title": result["metadata"]["title"],
                "category": result["metadata"]["category"],
                "authority": result["metadata"]["authority"],
                "source_type": result["metadata"]["source_type"],
                "source": result["metadata"]["source"],
                "text": result["document"],
                "distance": result["distance"],
            }
        )

    return {
        "complaint": complaint,
        "retrieved_policies": policies,
        "count": len(policies),
    }


def process_complaint(
    complaint: str,
    top_k: int = 3,
) -> dict[str, Any]:
    """
    Complete RAG pipeline:

    Complaint
        ↓
    ChromaDB retrieval
        ↓
    Policy context
        ↓
    Groq/Llama
        ↓
    Structured response
    """

    if not complaint.strip():
        raise ValueError("Complaint cannot be empty.")

    # 1. Retrieve relevant policies.
    context = retrieve_context(
        complaint=complaint,
        top_k=top_k,
    )

    # 2. Build grounded LLM prompt.
    # Pass the retrieved policies directly because
    # build_rag_prompt expects top-level policy fields.
    rag_prompt = build_rag_prompt(
        complaint=complaint,
        retrieved_policies=context["retrieved_policies"],
    )

    # 3. Generate structured response.
    response = generate_structured_response(
        user_prompt=rag_prompt,
    )

    # 4. Validate grounding value.
    grounding = response.get(
        "grounding",
        "insufficient",
    )

    if grounding not in {
        "supported",
        "partially_supported",
        "insufficient",
    }:
        grounding = "insufficient"

    response["grounding"] = grounding

    # 5. Return both retrieval information and AI analysis.
    return {
        "complaint": complaint,
        "retrieved_policies": context["retrieved_policies"],
        "analysis": response,
    }
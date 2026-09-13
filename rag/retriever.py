from typing import Any

from .chroma_service import get_policy_collection


def retrieve_policies(
    complaint: str,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    Retrieve the most relevant civic policies for a complaint.
    """

    if not complaint.strip():
        raise ValueError("Complaint cannot be empty.")

    collection = get_policy_collection()

    results = collection.query(
        query_texts=[complaint.strip()],
        n_results=top_k,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]

    retrieved = []

    for index in range(len(documents)):
        retrieved.append(
            {
                "id": ids[index],
                "document": documents[index],
                "metadata": metadatas[index],
                "distance": distances[index],
            }
        )

    return retrieved
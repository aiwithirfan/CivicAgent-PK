import chromadb


CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "civic_policies"


def get_chroma_client():
    """
    Create or connect to the persistent ChromaDB database.
    """
    return chromadb.PersistentClient(path=CHROMA_PATH)


def get_policy_collection():
    """
    Create the civic policy collection if it does not exist.
    """
    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    return collection
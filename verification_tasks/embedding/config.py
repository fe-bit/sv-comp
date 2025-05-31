from chromadb import PersistentClient


def get_collection():
    client = PersistentClient(path="./chroma_db")
    return client.get_or_create_collection(name="code_chunks", embedding_function=None)
from chromadb import PersistentClient, Client


def get_collection():
    client = PersistentClient(path="./chroma_db")
    return client.get_or_create_collection(name="code_chunks", embedding_function=None)

def get_train_collection():
    # client = PersistentClient(path="./chroma_db_train")
    client = Client()
    return client.get_or_create_collection(name="code_chunks", embedding_function=None)

def get_test_collection():
    # client = PersistentClient(path="./chroma_db_test")
    client = Client()
    return client.get_or_create_collection(name="code_chunks", embedding_function=None)
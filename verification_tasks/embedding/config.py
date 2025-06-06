from chromadb import PersistentClient, Client
from typing import Literal

PERSISTENT_COLLECTION_NAMES = Literal["code_chunks", "code_chunks_nvembed"]


def get_collection(collection_name: PERSISTENT_COLLECTION_NAMES="code_chunks"):
    client = PersistentClient(path="./chroma/chroma_db")
    return client.get_or_create_collection(name=collection_name, embedding_function=None)


def get_gemini_collection():
    client = PersistentClient(path="./chroma/chroma_db_gemini")
    return client.get_or_create_collection(name="code_chunks_gemini", embedding_function=None)

def get_nvembed_collection():
    client = PersistentClient(path="./chroma/chroma_db_nvembed")
    return client.get_or_create_collection(name="code_chunks_nvembed", embedding_function=None)

def get_codet5p_embedder_collection():
    client = PersistentClient(path="./chroma/chroma_db_codet5p")
    return client.get_or_create_collection(name="code_chunks", embedding_function=None)

def get_train_collection(in_memory=False):
    if in_memory:
        client = Client()
    else:
        client = PersistentClient(path="./chroma/chroma_db_train")
    return client.get_or_create_collection(name="code_chunks_train", embedding_function=None)

def get_test_collection(in_memory=False):
    if in_memory:
        client = Client()
    else:
        client = PersistentClient(path="./chroma/chroma_db_test")
    return client.get_or_create_collection(name="code_chunks_test", embedding_function=None)

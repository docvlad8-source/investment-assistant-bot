import os
from chromadb import PersistentClient
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
client = PersistentClient(path="./vector_store")
collection = client.get_or_create_collection("finance", embedding_function=embedding_fn)

def load_knowledge():
    if collection.count() == 0:
        docs, metas, ids = [], [], []
        doc_id = 0
        for filename in os.listdir("knowledge"):
            with open(f"knowledge/{filename}", "r", encoding="utf-8") as f:
                text = f.read()
                chunks = [text[i:i+600] for i in range(0, len(text), 600)]
                for chunk in chunks:
                    docs.append(chunk)
                    metas.append({"source": filename})
                    ids.append(str(doc_id))
                    doc_id += 1
        collection.add(documents=docs, metadatas=metas, ids=ids)

def retrieve_context(query: str, n=3):
    results = collection.query(query_texts=[query], n_results=n)
    return "\n".join(results["documents"][0])
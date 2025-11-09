from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from backend.config import settings
import pickle
import os


class RAGTool:
    def __init__(self):
        self.index_path = settings.rag_index_path
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model_name)
        self.vectorstore = self._load_vectorstore()

    def _load_vectorstore(self):
        if os.path.exists(self.index_path):
            with open(self.index_path, "rb") as f:
                return pickle.load(f)
        else:
            return FAISS(embedding_function=self.embeddings)

    def add_text(self, text: str):
        self.vectorstore.add_texts([text])
        with open(self.index_path, "wb") as f:
            pickle.dump(self.vectorstore, f)

    def query(self, query_text: str, k: int = 3):
        results = self.vectorstore.similarity_search(query_text, k=k)
        return [r.page_content for r in results]

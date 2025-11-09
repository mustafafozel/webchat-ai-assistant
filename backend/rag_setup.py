import math

class SimpleRAG:
    def __init__(self):
        self.docs = []

    def add_document(self, text: str):
        self.docs.append(text)

    def cosine_sim(self, a, b):
        a, b = a.lower(), b.lower()
        common = len(set(a.split()) & set(b.split()))
        return common / math.sqrt(len(a.split()) * len(b.split()))

    def search(self, query: str):
        if not self.docs:
            return None
        sims = [self.cosine_sim(query, d) for d in self.docs]
        return self.docs[sims.index(max(sims))] if sims else None


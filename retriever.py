import cohere
from pinecone import Pinecone

class Retriever:
    def __init__(self, pinecone_key,cohere_key, index_name="pyxon-task-v2"):

        self.pi = Pinecone(api_key=pinecone_key)
        self.vector_index = self.pi.Index(index_name)

        self.co = cohere.Client(api_key=cohere_key)
        self.embedder = "embed-multilingual-v3.0"

    
    def get_embeddings(self, text):

        try:
            response = self.co.embed(
                texts=[text],
                model=self.embedder,
                input_type="search_query"
            )
            return response.embeddings[0]
        except Exception as e:
            print(f"error getting embeddings: {e}")

    def search(self, query, k=5):

        query= self.get_embeddings(query)

        results = self.vector_index.query(
            vector=query,
            top_k=k,
            include_metadata=True)

        retrieved=[] 
        for match in results.matches:
            retrieved.append({
                "score": match.score,
                "text": match.metadata.get("text", ""),
                "doc_name": match.metadata.get("doc_name", "")
            })
            
        return retrieved
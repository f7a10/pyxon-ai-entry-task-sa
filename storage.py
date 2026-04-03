import sqlite3
import uuid
import time
import cohere
from pinecone import Pinecone, ServerlessSpec


class DualStorage:
    def __init__(self, cohere_key, pinecone_key, index_name="pyxon-task-v2"):
        self.co= cohere.Client(cohere_key)
        self.embedder = "embed-multilingual-v3.0"
        self.dimension = 1024

        self.pinecone = Pinecone(api_key=pinecone_key)
        self.index = index_name

        self.connection = sqlite3.connect('data.db', check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.creat()

        if self.index not in [index.name for index in self.pinecone.list_indexes()]:
            self.pinecone.create_index(
                name=self.index,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            time.sleep(10)

        self.vector_store = self.pinecone.Index(self.index)

    def creat(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_name TEXT,
                chunk_text TEXT,
                chunk_index INTEGER
            )
        ''')
        self.connection.commit()
        
    def store_chunk(self, document_name, chunks):

        vectors = []
        cohere_batch=90 

        for i in range(0, len(chunks), cohere_batch):
            batch = chunks[i:i+cohere_batch]

            try:
                response=self.co.embed(
                    texts=batch,
                    model=self.embedder,
                    input_type="search_document"
                )
                emdeddings=response.embeddings

            except Exception as e:
                print(f"Error embedding chunks: {e}")
                
            for a , (chunk, embedding) in enumerate(zip(batch, emdeddings)):
                index=i+a
                chunk_id=str(uuid.uuid4())

                self.cursor.execute(
                    "INSERT INTO document_chunks (id, document_name, chunk_text, chunk_index) VALUES (?, ?, ?, ?)",
                    (chunk_id, document_name, chunk, index)
                )

                vectors.append(
                    (chunk_id, embedding, {"doc_name": document_name, "chunk_index": index, "text": chunk})
                )

        self.connection.commit()

        pinecone_batch=100

        for i in range(0, len(vectors), pinecone_batch):
            batch = vectors[i:i+pinecone_batch]
            if batch:
                self.vector_store.upsert(vectors=batch)
import streamlit as st
import tempfile
import os
import time
import cohere

from start import DocumentReader
from chunker import DocumentChunker
from storage import DualStorage
from retriever import Retriever

# Configuration and Secrets
st.set_page_config(page_title="Pyxon AI | RAG Assistant", layout="wide")

COHERE_KEY = st.secrets.get("COHERE_KEY")
PINECONE_KEY = st.secrets.get("PINECONE_KEY")

@st.cache_resource
def init_system():
    parser = DocumentReader()
    chunker = DocumentChunker()
    # تم تمرير المفاتيح بترتيب ملف storage.py
    storage = DualStorage(cohere_key=COHERE_KEY, pinecone_key=PINECONE_KEY)
    # تم تمرير المفاتيح بترتيب ملف retriever.py (باينكون أولاً)
    retriever = Retriever(pinecone_key=PINECONE_KEY, cohere_key=COHERE_KEY)
    co_client = cohere.Client(COHERE_KEY)
    return parser, chunker, storage, retriever, co_client

try:
    parser, chunker, storage, retriever, co_client = init_system()
except Exception as e:
    st.error(f"Cloud connection failed: {e}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar: Document Management
with st.sidebar:
    st.title("Admin Panel")
    st.markdown("Manage reference documents for the RAG system.")
    
    uploaded_file = st.file_uploader("Upload Document", type=["pdf", "docx", "txt"])
    
    if uploaded_file and st.button("Process Document", use_container_width=True):
        with st.spinner("Parsing and chunking document..."):
            os.makedirs("temp_uploads", exist_ok=True)
            save_path = os.path.join("temp_uploads", uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                # استدعاء دالة read من ملف start.py
                text = parser.read(save_path)
                if not text or not text.strip():
                    st.error("No text could be extracted. Please ensure it is not a scanned image.")
                else:
                    # استدعاء دالة chunk من ملف chunker.py
                    chunks = chunker.chunk(text)
                    
                    # استدعاء دالة store_chunk من ملف storage.py
                    storage.store_chunk(document_name=uploaded_file.name, chunks=chunks)
                    
                    with st.spinner("Indexing vectors in Pinecone (approx. 15s)..."):
                        time.sleep(15)
                        
                    st.success("Document successfully indexed and ready for queries.")
            except Exception as e:
                st.error(f"Processing error: {e}")
            finally:
                if os.path.exists(save_path):
                    os.remove(save_path)
                    
    st.divider()
    
    if st.button("Purge Database", type="primary", use_container_width=True):
        with st.spinner("Deleting vectors and local records..."):
            try:
                # استخدام المسميات الجديدة vector_store و connection
                storage.vector_store.delete(delete_all=True)
                storage.cursor.execute("DELETE FROM document_chunks")
                storage.connection.commit()
                st.success("Database purged successfully.")
            except Exception:
                st.info("Database is already empty.")

    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main UI: Chat Interface
st.title("Pyxon AI Assistant")
st.markdown("Ask questions regarding the uploaded documents. The AI will retrieve the most relevant context and generate an accurate response.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("View Retrieved Sources"):
                for i, src in enumerate(message["sources"], 1):
                    st.caption(f"Source {i} ({src['doc_name']}) - Similarity: {src['score']:.2f}")
                    st.write(src['text'])
                    st.divider()

if prompt := st.chat_input("Type your question here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving context and generating response..."):
            # استدعاء دالة search مع معامل k
            results = retriever.search(query=prompt, k=3)
            
            if not results:
                msg = "I could not find any relevant information in the uploaded documents to answer your question."
                st.info(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg, "sources": []})
            else:
                context_texts = "\n\n---\n\n".join([res['text'] for res in results])
                
                system_prompt = f"""You are a professional AI assistant. Answer the user's question based ONLY on the provided context. If the answer is not in the context, state clearly that you do not have sufficient information. Reply in the same language as the user's question.

Retrieved Context:
{context_texts}

User Question: {prompt}"""

                try:
                    response = co_client.chat(
                        message=system_prompt,
                        model="command-a-03-2025",
                        temperature=0.3
                    )
                    
                    answer = response.text
                    st.markdown(answer)
                    
                    with st.expander("View Retrieved Sources"):
                        for i, src in enumerate(results, 1):
                            st.caption(f"Source {i} ({src['doc_name']}) - Similarity: {src['score']:.2f}")
                            st.write(src['text'])
                            st.divider()
                            
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "sources": results
                    })
                    
                except Exception as e:
                    st.error("An error occurred while generating the response. Please try again.")
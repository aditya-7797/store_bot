"""RAG-based Operations Copilot

Handles operational procedures, SOP questions, and training documentation.
Uses RAG to reference SOP_INVENTORY_RECONCILIATION.md and ONBOARDING_GUIDE.md
to answer operational questions about inventory management, reconciliation,
stock handling, and customer segmentation.
"""

from langchain_openai import OpenAIEmbeddings
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
import os
from pathlib import Path
from typing import Optional

# Initialize LLM
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.3  # Slightly higher for more natural conversational responses
)

# Initialize embeddings - prefer the langchain-huggingface wrapper
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
except Exception:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    except Exception:
        # Fallback to simple embeddings if HuggingFace unavailable
        from langchain_community.embeddings import FakeEmbeddings
        embeddings = FakeEmbeddings(model_name="fake")

# Global vector store (lazy loaded)
_vector_store = None
_docs_loaded = False


def _load_documents():
    """Load and index SOP and Onboarding documents"""
    global _vector_store, _docs_loaded
    
    if _docs_loaded:
        return _vector_store
    
    docs_dir = Path(__file__).parent.parent / "docs"
    documents = []
    
    # Load SOP_INVENTORY_RECONCILIATION.md
    sop_path = docs_dir / "SOP_INVENTORY_RECONCILIATION.md"
    if sop_path.exists():
        with open(sop_path, 'r', encoding='utf-8') as f:
            sop_content = f.read()
            documents.append(Document(
                page_content=sop_content,
                metadata={"source": "SOP_INVENTORY_RECONCILIATION", "type": "sop"}
            ))
    
    # Load ONBOARDING_GUIDE.md
    onboarding_path = docs_dir / "ONBOARDING_GUIDE.md"
    if onboarding_path.exists():
        with open(onboarding_path, 'r', encoding='utf-8') as f:
            onboarding_content = f.read()
            documents.append(Document(
                page_content=onboarding_content,
                metadata={"source": "ONBOARDING_GUIDE", "type": "onboarding"}
            ))
    
    if not documents:
        print("Warning: No documentation files loaded for RAG")
        return None
    
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "]
    )
    
    chunks = []
    for doc in documents:
        split_docs = text_splitter.split_documents([doc])
        chunks.extend(split_docs)
    
    # Create vector store
    try:
        _vector_store = FAISS.from_documents(chunks, embeddings)
        _docs_loaded = True
        print(f"✓ RAG vector store initialized with {len(chunks)} chunks from documentation")
    except Exception as e:
        print(f"Error creating vector store: {e}")
        _vector_store = None
    
    return _vector_store


def _retrieve_context(query: str, k: int = 4) -> str:
    """Retrieve relevant context from vector store"""
    vector_store = _load_documents()
    
    if vector_store is None:
        return ""
    
    try:
        # Search for relevant documents
        results = vector_store.similarity_search(query, k=k)
        
        context = ""
        for i, doc in enumerate(results):
            source = doc.metadata.get("source", "Unknown")
            context += f"\n[From {source}]:\n{doc.page_content}\n"
        
        return context
    except Exception as e:
        print(f"Error retrieving context: {e}")
        return ""


# RAG Prompt Template
rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an Operations Copilot assistant specialized in inventory management, 
stock reconciliation, and daily operational procedures. You have access to the company's SOP 
and Onboarding documentation.

Your role is to:
1. Answer questions about inventory operations, stock management, and reconciliation
2. Reference specific sections from SOPs and guidelines when answering
3. Provide clear, actionable steps for operational tasks
4. Explain company policies and procedures for stock handling
5. Help with RFM customer segmentation understanding
6. Provide guardrails and best practices for inventory updates

When answering:
- Always cite which document/section you're referencing
- Provide step-by-step instructions when relevant
- Mention any guardrails or important warnings
- If the answer is in the documentation, stick closely to it
- Be specific about timelines and responsibilities

Here is the relevant documentation context:

{context}

If the documentation doesn't contain the answer, clearly state that and provide general best practices.
"""),
    ("user", "{query}")
])

rag_chain = rag_prompt | llm


def rag_copilot(state: dict) -> dict:
    """Process operational/SOP questions using RAG"""
    query = state["query"]
    
    # Retrieve relevant context from documentation
    context = _retrieve_context(query, k=4)
    
    # Generate response using RAG
    try:
        result = rag_chain.invoke({
            "query": query,
            "context": context or "(No relevant documentation found in vector store)"
        })
        response = result.content.strip()
    except Exception as e:
        response = f"Error processing query: {str(e)}"
    
    state["response"] = response
    return state


def get_operations_topics() -> list:
    """Return list of operations topics this copilot can handle"""
    return [
        "inventory reconciliation",
        "stock reconciliation",
        "negative stock",
        "adding stock",
        "removing stock",
        "RFM segmentation",
        "customer prioritization",
        "stock guardrails",
        "inventory update process",
        "daily reconciliation",
        "weekly reconciliation",
        "stock procedures",
        "operational procedures",
        "onboarding",
        "system access",
    ]

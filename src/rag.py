"""
RAG Pipeline for Site Feasibility Agent
Builds vector store from toy document and provides retrieval functionality.
"""

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from pathlib import Path
from typing import List, Optional
import warnings
warnings.filterwarnings("ignore")


class SiteFeasibilityRAG:
    """RAG pipeline for site feasibility queries."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the RAG pipeline.
        
        Args:
            data_dir: Directory containing the toy document (defaults to ../data)
        """
        # Set up paths
        if data_dir is None:
            data_dir = Path(__file__).resolve().parent.parent / "data"
        else:
            data_dir = Path(data_dir)
            
        self.doc_path = data_dir / "toy_grid_doc.txt"
        
        # Initialize embeddings model
        print("Loading embedding model...")
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
        except Exception as e:
            print(f"Warning: Could not load HuggingFace embeddings: {e}")
            print("Using mock embeddings for demonstration")
            self.embeddings = MockEmbeddings()
        
        # Build vector store
        self.vector_store = self._build_vector_store()
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
    def _build_vector_store(self) -> Chroma:
        """Build the Chroma vector store from the toy document."""
        print("Building vector store...")
        
        # Read the toy document
        if not self.doc_path.exists():
            raise FileNotFoundError(f"Toy document not found at {self.doc_path}")
            
        text = self.doc_path.read_text()
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " "]
        )
        
        chunks = text_splitter.split_text(text)
        
        # Create documents with metadata
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "source": "California ISO Interconnection Queue Summary 2023",
                    "chunk_id": i
                }
            )
            for i, chunk in enumerate(chunks)
        ]
        
        # Build vector store in memory
        try:
            vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name="site_feasibility"
            )
        except Exception as e:
            print(f"Warning: Could not create Chroma vector store: {e}")
            print("Creating mock vector store")
            vector_store = MockVectorStore(documents)
        
        print(f"Vector store built with {len(documents)} document chunks")
        return vector_store
        
    def retrieve_relevant_docs(self, query: str) -> List[Document]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query string
            
        Returns:
            List of relevant documents
        """
        return self.retriever.get_relevant_documents(query)
        
    def get_context_for_query(self, query: str) -> str:
        """
        Get concatenated context from relevant documents.
        
        Args:
            query: Search query string
            
        Returns:
            Concatenated context string
        """
        docs = self.retrieve_relevant_docs(query)
        
        if not docs:
            return "No relevant information found in knowledge base."
            
        context_parts = []
        for doc in docs:
            source = doc.metadata.get("source", "Unknown source")
            content = doc.page_content.strip()
            context_parts.append(f"[Source: {source}]\n{content}")
            
        return "\n\n".join(context_parts)


class MockEmbeddings:
    """Mock embeddings for when sentence-transformers is not available."""
    
    def embed_documents(self, texts):
        """Return mock embeddings for documents."""
        return [[0.1, 0.2, 0.3] for _ in texts]
    
    def embed_query(self, text):
        """Return mock embedding for query."""
        return [0.1, 0.2, 0.3]


class MockVectorStore:
    """Mock vector store for when Chroma is not available."""
    
    def __init__(self, documents):
        self.documents = documents
    
    def as_retriever(self, search_type="similarity", search_kwargs=None):
        return MockRetriever(self.documents)


class MockRetriever:
    """Mock retriever that returns first few documents."""
    
    def __init__(self, documents):
        self.documents = documents
    
    def get_relevant_documents(self, query):
        # Return first 2 documents as "relevant"
        return self.documents[:2]


# Global instance for easy import
print("Initializing RAG pipeline...")
try:
    RAG_PIPELINE = SiteFeasibilityRAG()
    print("RAG pipeline initialized successfully")
except Exception as e:
    print(f"Warning: Could not initialize RAG pipeline: {e}")
    RAG_PIPELINE = None


def get_rag_context(query: str) -> str:
    """
    Convenience function to get RAG context for a query.
    
    Args:
        query: Search query string
        
    Returns:
        Context string from relevant documents
    """
    if RAG_PIPELINE is None:
        return "RAG pipeline not available."
        
    return RAG_PIPELINE.get_context_for_query(query)


if __name__ == "__main__":
    # Test the RAG pipeline
    print("\n" + "="*50)
    print("Testing RAG Pipeline")
    print("="*50)
    
    if RAG_PIPELINE is None:
        print("RAG pipeline not initialized. Exiting.")
        exit(1)
        
    # Test queries
    test_queries = [
        "solar projects in California",
        "transmission costs and upgrades", 
        "interconnection queue and renewable energy",
        "LCOE and financial projections",
        "grid stability and renewable penetration"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        context = get_rag_context(query)
        print(context[:300] + "..." if len(context) > 300 else context)
        print() 
import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pathlib import Path
from typing import List, Optional

from utils.config import get_config
from utils.logging_config import get_logger

logger = get_logger(__name__)
config = get_config()
rag_config = config.get('rag', {})
project_root = Path(__file__).resolve().parent.parent.parent

class MockEmbeddings:
    """Mock embeddings for when sentence-transformers is not available."""
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        logger.info(f"MockEmbeddings: embedding {len(texts)} documents.")
        return [[0.1] * 768 for _ in texts] # Return a list of 768-dim vectors

    def embed_query(self, text: str) -> List[float]:
        logger.info(f"MockEmbeddings: embedding query: '{text[:50]}...'")
        return [0.1] * 768 # Return a 768-dim vector

class MockVectorStore:
    """Mock vector store for when Chroma is not available."""
    def __init__(self, documents: List[Document]):
        self.documents = documents
        logger.info(f"MockVectorStore initialized with {len(documents)} documents.")

    def as_retriever(self, search_type="similarity", search_kwargs=None):
        logger.info(f"MockVectorStore.as_retriever called with search_kwargs: {search_kwargs}")
        return MockRetriever(self.documents, search_kwargs.get("k", 2) if search_kwargs else 2)

class MockRetriever:
    """Mock retriever that returns first few documents."""
    def __init__(self, documents: List[Document], k: int = 2):
        self.documents = documents
        self.k = k
        logger.info(f"MockRetriever initialized, will return {self.k} documents.")

    def get_relevant_documents(self, query: str) -> List[Document]:
        logger.info(f"MockRetriever: getting relevant documents for query: '{query[:50]}...'")
        return self.documents[:self.k]

class SiteFeasibilityRAG:
    """RAG pipeline for site feasibility queries."""
    
    _instance = None # Singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SiteFeasibilityRAG, cls).__new__(cls)
            # __init__ will be called only once
            cls._instance._initialized = False 
        return cls._instance

    def __init__(self, data_dir_name: str = "data"):
        """
        Initialize the RAG pipeline. Singleton ensures this runs once.
        Args:
            data_dir_name: Name of the directory containing the toy document, relative to project root.
        """
        if self._initialized:
            return
        self._initialized = True

        self.data_dir = project_root / data_dir_name
        self.doc_path = self.data_dir / "toy_grid_doc.txt" # Make this configurable if more docs are added
        
        logger.info(f"Initializing RAG pipeline. Document path: {self.doc_path}")

        self.embeddings = self._load_embeddings()
        self.vector_store = self._build_vector_store()
        
        if self.vector_store:
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": rag_config.get('top_k_results', 3)}
            )
            logger.info(f"RAG retriever initialized. k={rag_config.get('top_k_results', 3)}")
        else:
            self.retriever = None # Or a MockRetriever if preferred on critical failure
            logger.error("Vector store is None, RAG retriever cannot be initialized.")
        
        logger.info("RAG pipeline initialization complete.")

    def _load_embeddings(self):
        """Load HuggingFace embeddings or mock embeddings."""
        model_name = rag_config.get('embedding_model', "sentence-transformers/all-MiniLM-L6-v2")
        logger.info(f"Loading embedding model: {model_name}")
        try:
            return HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'} # Keep on CPU for broader compatibility
            )
        except Exception as e:
            logger.warning(f"Could not load HuggingFace embeddings '{model_name}': {e}. Using mock embeddings.")
            return MockEmbeddings()
    
    def _build_vector_store(self) -> Optional[Chroma]:
        """Build the Chroma vector store from the toy document."""
        logger.info(f"Building vector store from document: {self.doc_path}")
        
        if not self.doc_path.exists():
            logger.error(f"Toy document not found at {self.doc_path}. Cannot build vector store.")
            return None
            
        try:
            text = self.doc_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error reading document {self.doc_path}: {e}")
            return None
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=rag_config.get('chunk_size', 500),
            chunk_overlap=rag_config.get('chunk_overlap', 50),
            separators=["\n\n", "\n", ". ", " "]
        )
        chunks = text_splitter.split_text(text)
        
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "source": self.doc_path.name,
                    "chunk_id": i
                }
            )
            for i, chunk in enumerate(chunks)
        ]
        
        if not documents:
            logger.warning("No document chunks were created. Vector store will be empty.")
            # Fallback to mock if this is critical, or handle as error
            return MockVectorStore([]) # Or None, depending on desired robustness

        collection_name = rag_config.get('vector_db_collection', "site_feasibility")
        logger.info(f"Creating Chroma vector store with collection: {collection_name}")
        try:
            vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=collection_name,
                # persist_directory="./chroma_db" # Optional: for persistence
            )
            logger.info(f"Vector store built successfully with {len(documents)} document chunks.")
            return vector_store
        except Exception as e:
            logger.warning(f"Could not create Chroma vector store: {e}. Using mock vector store.")
            return MockVectorStore(documents)
        
    def retrieve_relevant_docs(self, query: str) -> List[Document]:
        """
        Retrieve relevant documents for a query.
        Args:
            query: Search query string
        Returns:
            List of relevant documents
        """
        if not self.retriever:
            logger.error("RAG retriever is not available. Cannot retrieve documents.")
            return []
        
        logger.debug(f"Retrieving relevant documents for query: '{query[:50]}...'")
        try:
            docs = self.retriever.get_relevant_documents(query)
            logger.info(f"Retrieved {len(docs)} documents for query.")
            return docs
        except Exception as e:
            logger.error(f"Error during document retrieval: {e}", exc_info=True)
            return []
        
    def get_context_for_query(self, query: str) -> str:
        """
        Get concatenated context from relevant documents.
        Args:
            query: Search query string
        Returns:
            Concatenated context string or an error/empty message.
        """
        docs = self.retrieve_relevant_docs(query)
        
        if not docs:
            logger.info("No relevant information found in knowledge base for the query.")
            return "No relevant information found in the knowledge base."
            
        context_parts = []
        for doc in docs:
            source = doc.metadata.get("source", "Unknown source")
            content = doc.page_content.strip()
            context_parts.append(f"[Source: {source}]\n{content}")
            
        full_context = "\n\n".join(context_parts)
        logger.debug(f"Generated context of length {len(full_context)} for query.")
        return full_context

# Global RAG pipeline instance (singleton)
RAG_PIPELINE_INSTANCE = None

def get_rag_pipeline() -> SiteFeasibilityRAG:
    global RAG_PIPELINE_INSTANCE
    if RAG_PIPELINE_INSTANCE is None:
        logger.info("Initializing global RAG_PIPELINE_INSTANCE.")
        try:
            RAG_PIPELINE_INSTANCE = SiteFeasibilityRAG()
        except Exception as e:
            logger.critical(f"Failed to initialize SiteFeasibilityRAG singleton: {e}", exc_info=True)
            # Depending on desired behavior, could raise error or return a mock/dummy RAG
            # For now, if it fails, get_rag_context will handle it returning a message.
            pass # RAG_PIPELINE_INSTANCE will remain None
    return RAG_PIPELINE_INSTANCE

def get_rag_context(query: str) -> str:
    """
    Convenience function to get RAG context for a query using the singleton pipeline.
    Args:
        query: Search query string
    Returns:
        Context string from relevant documents or an error message.
    """
    pipeline = get_rag_pipeline()
    if pipeline is None:
        logger.error("RAG pipeline is not available (failed to initialize). Cannot get context.")
        return "The knowledge base (RAG pipeline) is currently unavailable."
    
    return pipeline.get_context_for_query(query)

if __name__ == '__main__':
    from src.utils.logging_config import setup_logging
    setup_logging() # Ensure logging is set up

    logger.info("--- Testing RAG Pipeline ---")
    
    # Initialize directly for testing or use the getter
    # test_rag_pipeline = SiteFeasibilityRAG()
    test_rag_pipeline = get_rag_pipeline()

    if test_rag_pipeline and test_rag_pipeline.retriever:
        test_queries = [
            "solar projects in California",
            "What are CAISO interconnection studies about?",
            "renewable energy goals"
        ]
        
        for q_idx, test_query in enumerate(test_queries):
            print(f"\n--- RAG Test Query {q_idx+1} ---")
            logger.info(f"Test Query: {test_query}")
            context = get_rag_context(test_query)
            print(f"Retrieved Context (first 500 chars):\n{context[:500]}{'...' if len(context) > 500 else ''}")
            print("-" * 50)
    else:
        logger.error("RAG pipeline or retriever failed to initialize for testing.")

    # Test mock embeddings/retriever if main ones fail
    print("\n--- Testing Mock Components (if used) ---")
    mock_emb = MockEmbeddings()
    embedded_doc = mock_emb.embed_documents(["test doc"])
    print(f"Mock embedded doc vector (first 10 dims): {embedded_doc[0][:10]}...")
    embedded_query = mock_emb.embed_query("test query")
    print(f"Mock embedded query vector (first 10 dims): {embedded_query[:10]}...")

    mock_docs = [Document(page_content=f"Mock doc {i}") for i in range(5)]
    mock_retriever_instance = MockRetriever(mock_docs, k=3)
    retrieved = mock_retriever_instance.get_relevant_documents("any query")
    print(f"Mock retriever got {len(retrieved)} docs: {[d.page_content for d in retrieved]}") 
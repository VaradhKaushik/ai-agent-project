import os
import yaml
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from pathlib import Path

# Define root path and other key paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DOCS_DIR = PROJECT_ROOT / "data" / "source_docs"
CHROMA_DB_DIR = PROJECT_ROOT / "data" / "chroma"
METADATA_FILE = PROJECT_ROOT / "data" / "doc_metadata.yaml"

def load_metadata():
    """Loads document metadata from the YAML file."""
    with open(METADATA_FILE, 'r') as f:
        return yaml.safe_load(f)

def ingest_documents():
    """
    Ingests PDF documents from the source_docs directory, processes them,
    and stores them in a Chroma vector database.
    """
    # Load document metadata
    metadata_map = load_metadata()
    
    all_docs_for_chroma = []
    
    # Iterate over PDF files in the source_docs directory
    for pdf_file in SOURCE_DOCS_DIR.glob("*.pdf"):
        file_name = pdf_file.name
        print(f"Processing {file_name}...")

        # Load PDF content
        loader = UnstructuredPDFLoader(str(pdf_file))
        raw_documents = loader.load()

        # Split documents into manageable chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100
        )
        split_documents = text_splitter.split_documents(raw_documents)

        # Add metadata to each chunk
        doc_metadata = metadata_map.get(file_name, {})
        for i, doc_chunk in enumerate(split_documents):
            doc_chunk.metadata.update(doc_metadata)
            doc_chunk.metadata["source_document"] = file_name # Add original filename
            doc_chunk.metadata["chunk_index"] = i # Add chunk index
        
        all_docs_for_chroma.extend(split_documents)
        print(f"Created {len(split_documents)} chunks for {file_name}.")

    if not all_docs_for_chroma:
        print("No documents found or processed. Exiting.")
        return

    # Initialize OpenAI embeddings
    # Ensure OPENAI_API_KEY environment variable is set
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    # Create and persist Chroma vector store
    # Chroma will create the directory if it doesn't exist
    db = Chroma.from_documents(
        documents=all_docs_for_chroma,
        embedding=embeddings,
        persist_directory=str(CHROMA_DB_DIR)
    )
    
    print(f"Ingested {len(all_docs_for_chroma)} chunks into Chroma at {CHROMA_DB_DIR}")

if __name__ == "__main__":
    # This allows the script to be run with 'python -m scripts.ingest_docs'
    ingest_documents() 
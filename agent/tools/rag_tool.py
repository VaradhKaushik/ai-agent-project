from langchain_openai import OpenAI
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from pathlib import Path

# Define path to the persisted Chroma database
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHROMA_DB_DIR = PROJECT_ROOT / "data" / "chroma"

# Initialize OpenAI embeddings (ensure OPENAI_API_KEY is set in your environment)
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

# Load the persisted Chroma vector store
# This assumes the database has already been created by the ingest_docs.py script
db = Chroma(
    persist_directory=str(CHROMA_DB_DIR),
    embedding_function=embeddings,
)

# Create the RetrievalQA chain
# This chain will retrieve relevant documents and then use an LLM to answer the query
rag_chain = RetrievalQA.from_chain_type(
    llm=OpenAI(), # Uses a default OpenAI model for question answering
    chain_type="stuff", # "stuff" chain type simply stuffs all retrieved docs into the prompt
    retriever=db.as_retriever(search_kwargs={"k": 4}), # Retrieve top 4 relevant chunks
)

def ask_rag(query: str) -> str:
    """Return a cited answer pulled from the two NREL PDFs."""
    # The RetrievalQA chain handles both retrieval and answer generation
    return rag_chain.run(query) 
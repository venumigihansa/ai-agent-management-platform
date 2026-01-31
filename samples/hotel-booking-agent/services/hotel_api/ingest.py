import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

PDF_ROOT = Path("resources/policy_pdfs")

# Embeddings
embeddings = OpenAIEmbeddings(
    model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
)

# Text splitter (equivalent to your DocumentChunker)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

# Pinecone Vector Store
vectorstore = PineconeVectorStore(
    index_name=os.getenv("PINECONE_INDEX_NAME", "hotel-policies"),
    embedding=embeddings,
    pinecone_api_key=os.getenv("PINECONE_API_KEY"),
    pinecone_host=os.getenv("PINECONE_SERVICE_URL"),
)

def ingest_policy_folder(folder: Path):
    pdf_path = folder / "policies.pdf"
    metadata_path = folder / "metadata.json"

    if not pdf_path.exists() or not metadata_path.exists():
        print(f"Skipping {folder.name}: missing files")
        return

    # Load PDF
    docs = PyPDFLoader(str(pdf_path)).load()

    # Load metadata
    metadata = eval(metadata_path.read_text())

    # Attach metadata to each page
    for d in docs:
        d.metadata.update(metadata)
        d.metadata["source"] = folder.name

    # Chunk
    chunks = splitter.split_documents(docs)

    # Ingest
    vectorstore.add_documents(chunks)`1 11්‍ර
    4`
    print(f"✓ Ingested {folder.name}")

def ingest_all():
    for hotel_dir in PDF_ROOT.iterdir():
        if hotel_dir.is_dir():
            ingest_policy_folder(hotel_dir)

if __name__ == "__main__":
    ingest_all()

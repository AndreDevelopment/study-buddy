import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables from .env
load_dotenv()

NOTES_DIR = "./notes"
# Define where your local vector database will live
PERSIST_DIRECTORY = "./chroma_db"

def load_and_split_notes():
    # 1. Check if the directory exists
    if not os.path.exists(NOTES_DIR):
        print(f"Error: The directory '{NOTES_DIR}' does not exist.")
        print("Please create it and add a few markdown (.md) or text (.txt) files.")
        return []

    print(f"Loading documents from {NOTES_DIR}...")

    # 2. Load all markdown files recursively from the notes folder
    loader = DirectoryLoader(
        NOTES_DIR,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    
    documents = loader.load()
    print(f"Successfully loaded {len(documents)} document(s).")

    # 3. Configure the text splitter
    # chunk_size: Maximum characters per chunk
    # chunk_overlap: Characters shared between consecutive chunks to preserve context
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )

    # 4. Split documents into chunks
    chunks = text_splitter.split_documents(documents)
    print(f"Split documents into {len(chunks)} total chunks.")

    return chunks

# Replace your previous embedding initialization with this:
def store_chunks_in_vector_db(chunks):
    if not chunks:
        return
        
    print("Initializing local embedding model (this will download on first run)...")
    
    # "all-mpnet-base-v2" is a popular, high-quality, free model
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        encode_kwargs={"normalize_embeddings": True}
    )

    print(f"Storing chunks in ChromaDB at '{PERSIST_DIRECTORY}'...")
    
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )
    
    print("Vector database successfully created locally!")
    return vector_store

if __name__ == "__main__":
    # Test the loading and splitting process
    chunks = load_and_split_notes()
    
    if chunks:
        print("\n--- Example of the First Chunk ---")
        print(f"Source file: {chunks[0].metadata.get('source', 'Unknown')}")
        print(chunks[0].page_content[:300] + "...\n")
        store_chunks_in_vector_db(chunks)
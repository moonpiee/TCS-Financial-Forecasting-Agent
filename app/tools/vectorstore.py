import os
import logging
from typing import Optional
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFDirectoryLoader

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

CHROMA_PATH = "./chroma_db"
REPORTS_PATH = "docs/Reports"
TRANSCRIPTS_PATH = "docs/Transcripts"

def create_or_load_vector_store():
    try:
        embeddings = HuggingFaceBgeEmbeddings(model_name="all-MiniLM-L6-v2")

        if os.path.exists(CHROMA_PATH):
            logging.info("Existing ChromaDB found. Loading...")
            return Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

        logging.info("ChromaDB not found. Creating a new one...")

        if not os.path.isdir(REPORTS_PATH):
            raise FileNotFoundError(f"Reports folder missing at path: {REPORTS_PATH}")
        if not os.path.isdir(TRANSCRIPTS_PATH):
            raise FileNotFoundError(f"Transcripts folder missing at path: {TRANSCRIPTS_PATH}")

        loader_reports = PyPDFDirectoryLoader(REPORTS_PATH)
        loader_transcripts = PyPDFDirectoryLoader(TRANSCRIPTS_PATH)

        documents_reports = loader_reports.load()
        documents_transcripts = loader_transcripts.load()

        if not documents_reports and not documents_transcripts:
            raise ValueError("No PDF documents found in both Reports and Transcripts folders.")

        for doc in documents_reports:
            doc.metadata["type"] = "report"
        for doc in documents_transcripts:
            doc.metadata["type"] = "transcript"

        all_documents = documents_reports + documents_transcripts
        logging.info(f"Loaded {len(all_documents)} documents from Reports and Transcripts.")

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=500)
        split_docs = splitter.split_documents(all_documents)
        logging.info(f"Split documents into {len(split_docs)} chunks.")

        vectorstore = Chroma.from_documents(
            split_docs,
            embedding_function=embeddings,
            persist_directory=CHROMA_PATH
        )
        vectorstore.persist()
        logging.info("ChromaDB creation complete and persisted.")
        return vectorstore

    except Exception as e:
        logging.error(f"create_or_load_vector_store failed: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    vs = create_or_load_vector_store()
    if vs:
        logging.info("Vector store ready to use!")
    else:
        logging.error("Failed to initialize vector store.")
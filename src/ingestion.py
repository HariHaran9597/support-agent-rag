import os
import pandas as pd
from langchain_community.document_loaders import DataFrameLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 1. SETUP
DATA_PATH = "./data/tickets.csv"
DB_PATH = "./vector_db"

def ingest_data():
    print("🚀 Starting data ingestion...")

    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: {DATA_PATH} not found!")
        return

    df = pd.read_csv(DATA_PATH)
    print(f"📊 Loaded {len(df)} tickets from CSV.")

    df['combined_text'] = "Issue: " + df['issue_description'] + " | Resolution: " + df['resolution']
    
    loader = DataFrameLoader(df, page_content_column="combined_text")
    docs = loader.load()

    # --- THE FIX IS HERE ---
    for doc in docs:
        doc.metadata['feedback_score'] = 0
        # FORCE TICKET_ID TO BE A STRING
        doc.metadata['ticket_id'] = str(doc.metadata['ticket_id'])
    
    print(f"📝 Prepared {len(docs)} documents for embedding.")

    print("🧠 Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("💾 Creating Vector Database in ChromaDB...")
    # Delete old DB if it exists to avoid duplicates/conflicts
    if os.path.exists(DB_PATH):
        import shutil
        shutil.rmtree(DB_PATH)
        print("   (Deleted old database data)")

    vector_db = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=DB_PATH,
        collection_name="support_tickets"
    )

    print("✅ Ingestion Complete! Database saved to ./vector_db")

if __name__ == "__main__":
    ingest_data()
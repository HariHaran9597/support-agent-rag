from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from src.analytics import log_feedback  # <--- Import the analytics logger

# 1. SETUP
DB_PATH = "./vector_db"
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embedding_function,
    collection_name="support_tickets"
)

def submit_feedback(ticket_id, feedback_type, query_text):
    """
    Updates the feedback_score for a specific ticket and logs it to analytics.
    
    Args:
        ticket_id (str): The ID of the ticket to update.
        feedback_type (int): 1 for Thumbs Up, -1 for Thumbs Down.
        query_text (str): The user's query (needed for analytics tracking).
    """
    print(f"🔄 Processing feedback for Ticket #{ticket_id}...")
    
    # 2. FIND THE DOCUMENT
    results = vector_db.get(where={"ticket_id": str(ticket_id)})
    
    if not results['ids']:
        print(f"❌ Ticket {ticket_id} not found!")
        return False

    # Get the internal ID (UUID) used by Chroma
    doc_id = results['ids'][0]
    current_metadata = results['metadatas'][0]
    
    # 3. UPDATE SCORE
    current_score = current_metadata.get('feedback_score', 0)
    new_score = current_score + feedback_type
    
    print(f"   Current Score: {current_score} -> New Score: {new_score}")
    
    # Update metadata object locally
    current_metadata['feedback_score'] = new_score
    
    # 4. SAVE CHANGES TO VECTOR DB
    # We access the raw Chroma client to update ONLY metadata without needing the text
    collection = vector_db._client.get_collection("support_tickets")
    collection.update(
        ids=[doc_id],
        metadatas=[current_metadata]
    )
    
    # 5. LOG TO ANALYTICS DB
    # This records the interaction so it shows up in your Dashboard tab
    log_feedback(query_text, str(ticket_id), feedback_type)
    
    print("✅ Database & Analytics updated successfully!")
    return True

if __name__ == "__main__":
    # Test it with a dummy query
    submit_feedback("107", 1, "test query for error 503")
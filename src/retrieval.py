from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import chromadb

DB_PATH = "./vector_db"
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def retrieve_tickets(query, top_k=3, use_hybrid=True):
    """
    Searches for tickets.
    Args:
        use_hybrid (bool): If True, uses Feedback Scores. If False, uses pure Vector Search (Baseline).
    """
    print(f"🔎 Searching for: '{query}' (Hybrid: {use_hybrid})")
    
    vector_db = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embedding_function,
        collection_name="support_tickets"
    )
    
    # 1. RAW VECTOR SEARCH
    results = vector_db.similarity_search_with_score(query, k=5)
    
    reranked_results = []
    
    for doc, score in results:
        # Calculate Base Similarity
        similarity = 1 / (1 + score)
        
        # 2. APPLY A/B LOGIC
        if use_hybrid:
            # Treatment: Apply Feedback Boost
            feedback = doc.metadata.get('feedback_score', 0)
            final_score = (similarity * 0.7) + (feedback * 0.05)
        else:
            # Control: Pure Vector Search (ignore feedback)
            final_score = similarity
            
        reranked_results.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": final_score,
            "raw_similarity": similarity
        })

    # Sort by score
    reranked_results.sort(key=lambda x: x["score"], reverse=True)
    
    # 3. CONFIDENCE GUARDRAIL
    # If the top result is too weak, return None
    top_result = reranked_results[0]
    
    # Threshold: 0.25 is a reasonable baseline for 'MiniLM' (it varies by model)
    # If score < 0.25, it's likely garbage.
    if top_result['score'] < 0.25:
        print(f"⚠️ Low confidence match: {top_result['score']:.2f}")
        return [] # Return empty list to signal failure

    return reranked_results[:top_k]
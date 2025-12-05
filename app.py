import streamlit as st
import pandas as pd
from src.retrieval import retrieve_tickets
from src.llm_chain import generate_response
from src.feedback import submit_feedback
from src.ingestion import ingest_data
from src.analytics import log_search, get_metrics # Import analytics
import os

# Check DB on startup
if not os.path.exists("./vector_db"):
    st.warning("⚠️ Database not found. Building it now...")
    ingest_data()

st.set_page_config(page_title="Support Agent AI", layout="wide")

st.title("🤖 AI Support Agent Assistant")

# TABS FOR UI
tab1, tab2 = st.tabs(["💬 Agent Assist", "📊 Analytics Dashboard"])

# --- TAB 1: THE CHATBOT ---
with tab1:
    # SIDEBAR CONTROLS
    with st.sidebar:
        st.header("Debug Controls")
        use_hybrid = st.checkbox("Enable Hybrid Search (Feedback Loop)", value=True)
        st.caption("Uncheck to test 'Baseline' (Pure Vector Search) vs 'Hybrid'.")
        
        st.divider()
        st.header("New Ticket")
        issue_input = st.text_area("Customer Complaint:", height=150, 
            value="I keep getting error 503 when loading the dashboard.")
        
        if st.button("Find Solution"):
            st.session_state['query'] = issue_input
            st.session_state['run_search'] = True

    # MAIN CHAT LOGIC
    if 'run_search' in st.session_state and st.session_state['run_search']:
        query = st.session_state['query']
        
        with st.spinner("🔍 Searching knowledge base..."):
            # Pass the hybrid flag to the retrieval function
            retrieved_docs = retrieve_tickets(query, use_hybrid=use_hybrid)
        
        # GUARDRAIL CHECK
        if not retrieved_docs:
            st.error("❌ No relevant past tickets found. Confidence score too low.")
            st.warning("Try adding more details to the complaint.")
        else:
            # Log the search attempt
            top_ticket_id = retrieved_docs[0]['metadata']['ticket_id']
            score = retrieved_docs[0]['score']
            log_search(query, top_ticket_id, score)

            with st.spinner("📝 Drafting response..."):
                ai_response = generate_response(query, retrieved_docs)
            
            # Display
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("✅ Drafted Response")
                st.info(ai_response)
                
                st.markdown("### Was this helpful?")
                c1, c2, c3 = st.columns([1,1,3])
                with c1:
                    if st.button("👍 Yes"):
                        submit_feedback(top_ticket_id, 1, query) # Pass query
                        st.toast("Feedback recorded! System improved.")
                with c2:
                    if st.button("👎 No"):
                        submit_feedback(top_ticket_id, -1, query)
                        st.toast("Feedback recorded! System corrected.")

            with col2:
                st.subheader("📚 Source Context")
                if use_hybrid:
                    st.success("⚡ Hybrid Search Active (Ranking boosted by feedback)")
                else:
                    st.warning("⚠️ Baseline Mode (Pure Vector Search)")
                    
                for doc in retrieved_docs:
                    with st.expander(f"Ticket #{doc['metadata']['ticket_id']} (Score: {doc['score']:.2f})"):
                        st.write(f"**Issue:** {doc['content']}")
                        st.caption(f"Feedback Score: {doc['metadata']['feedback_score']}")

# --- TAB 2: THE ANALYTICS ---
with tab2:
    st.header("📈 System Performance Metrics")
    
    # Load data from SQLite
    df = get_metrics()
    
    if not df.empty:
        # KPI Metrics
        total_queries = len(df)
        positive_feedback = len(df[df['feedback'] == 1])
        accuracy = (positive_feedback / total_queries) * 100 if total_queries > 0 else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Queries", total_queries)
        m2.metric("Positive Feedback", positive_feedback)
        m3.metric("Retrieval Accuracy", f"{accuracy:.1f}%")
        
        st.divider()
        
        # Charts
        st.subheader("Feedback Trend")
        # Simple count of feedback types
        feedback_counts = df['feedback'].value_counts()
        st.bar_chart(feedback_counts)
        
        st.subheader("Raw Data Logs")
        st.dataframe(df.sort_values(by="timestamp", ascending=False))
    else:
        st.info("No data yet. Run some searches in the 'Agent Assist' tab!")
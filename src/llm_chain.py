import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# 1. SETUP: Load the API Key
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("❌ GROQ_API_KEY not found in .env file!")

# 2. INITIALIZE LLM: We use Llama-3-8b because it's fast and free on Groq
llm = ChatGroq(
    groq_api_key=api_key,
    model_name="moonshotai/kimi-k2-instruct-0905", 
    temperature=0.3  # Low temperature = more factual, less creative
)

def generate_response(query, context_tickets):
    """
    Generates a draft response using the LLM and the retrieved context.
    """
    
    # 3. FORMAT CONTEXT: Turn the list of tickets into a single string
    context_text = ""
    for i, ticket in enumerate(context_tickets):
        context_text += f"\n--- PAST TICKET #{i+1} ---\n"
        context_text += f"Issue: {ticket['content']}\n"
        context_text += f"Metadata: {ticket['metadata']}\n"

    # 4. CREATE PROMPT
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior customer support agent. 
        Your goal is to draft a helpful, professional response to a new customer issue.
        
        Use the following SIMILAR PAST SOLVED TICKETS to guide your answer.
        If the past tickets suggest a solution, recommend it.
        Be concise and polite."""),
        
        ("human", """
        CONTEXT (Past Solutions):
        {context}
        
        NEW CUSTOMER ISSUE:
        {query}
        
        Draft Response:""")
    ])

    # 5. RUN CHAIN
    chain = prompt | llm
    response = chain.invoke({
        "context": context_text,
        "query": query
    })
    
    return response.content

# --- TEST BLOCK ---
if __name__ == "__main__":
    # Fake context to test the LLM without running the full search
    fake_context = [
        {"content": "Issue: Payment 404 error | Resolution: Clear browser cache", "metadata": {"id": 102}},
        {"content": "Issue: Payment declined | Resolution: Check bank balance", "metadata": {"id": 109}}
    ]
    
    print("⏳ Generatng response...")
    answer = generate_response("I got an error 404 when paying", fake_context)
    print("\n--------- AI RESPONSE ---------")
    print(answer)
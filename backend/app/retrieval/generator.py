import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def generate_answer(query, chunks, chat_history=None):
    # Wahi same model jo humne final kiya hai
    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name=os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
    )
    
    context = "\n".join([c.content for c in chunks]) if hasattr(chunks[0], 'content') else str(chunks)
    
    prompt = f"Context: {context}\n\nUser Question: {query}"
    response = llm.invoke(prompt)
    return response.content
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

# 1. Path check karo
CHROMA_PATH = "chroma_db"

if not os.path.exists(CHROMA_PATH):
    print(f"❌ ERROR: '{CHROMA_PATH}' folder nahi mila. Pehle kuch ingest karo!")
else:
    # 2. Database Load karo
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    # 3. Saara data nikal ke categories check karo
    data = vector_db.get()
    metadatas = data['metadatas']
    
    if not metadatas:
        print("📭 Database khali hai Boss!")
    else:
        categories = set([m.get('category') for m in metadatas if m.get('category')])
        print("\n--- 📂 DATABASE MEIN YE CATEGORIES HAIN ---")
        for cat in categories:
            print(f"👉 '{cat}'")
        print("-------------------------------------------\n")
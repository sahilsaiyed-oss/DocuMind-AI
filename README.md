# 🧠 DocuMind AI – Multi-Domain RAG Knowledge Assistant

DocuMind AI is an advanced AI-powered knowledge assistant built using Retrieval-Augmented Generation (RAG).  
It allows users to query multiple document domains (medical, HR policies, company data) and receive accurate, context-aware answers with source references.

---

# 🚨 Problem

Organizations and individuals deal with large volumes of documents such as:

- Medical guidelines
- Company policies
- Legal documents
- Internal knowledge bases

Finding specific information manually is:
- ⏱️ Time-consuming  
- ❌ Error-prone  
- 📉 Inefficient  

---

# 💡 Solution

DocuMind AI solves this by:

- Ingesting multiple documents
- Converting them into vector embeddings
- Performing semantic search
- Generating accurate answers using LLM

👉 Result:
- ⚡ Instant answers  
- 🎯 Context-aware responses  
- 📄 Source-backed outputs  

---

# 🚀 Features

- 🔍 Semantic Search (ChromaDB)
- 📄 Multi-File Ingestion (PDF, URL, TXT)
- 🧠 AI Answer Generation (Groq LLaMA)
- 📂 Folder-Based Filtering  
  Example: `"diabetes_pro"`
- 💬 Natural Language Chat Interface
- 📊 Analytics Dashboard
- ⚡ Fast Response System
- 🔗 Source-based Answers

---

# 🏗️ Tech Stack

## Backend
- FastAPI
- LangChain
- ChromaDB
- HuggingFace Embeddings
- Groq API

## Frontend
- React / Lovable UI
- Fetch API

---

# 📁 Project Structure

```
backend/
  ├── app/
  ├── chroma_db/
  ├── main.py
  ├── requirements.txt

frontend/
  ├── src/
  ├── public/
  ├── package.json
```

---

# ⚙️ Setup Instructions

## 1️⃣ Clone Repo

```
git clone https://github.com/sahilsaiyed-oss/DocuMind-AI.git
cd DocuMind-AI
```

---

## 2️⃣ Backend Setup

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:

```
GROQ_API_KEY=your_api_key_here
```

Run backend:

```
uvicorn main:app --reload --port 8000
```

---

## 3️⃣ Frontend Setup

```
cd frontend
npm install
npm run dev
```

---

## 🌐 Access

- Frontend → http://localhost:8080  
- Backend Docs → http://localhost:8000/docs  

---

# 🧪 Example Query

```
What are the diagnostic values for diabetes? "diabetes_pro"
```

---

# 🧠 How It Works

1. Documents are ingested  
2. Text is chunked  
3. Converted into embeddings  
4. Stored in ChromaDB  
5. User query → semantic search  
6. Relevant chunks → LLM  
7. AI generates answer  

---

# 📊 Use Cases

- 🏥 Medical Data Analysis  
- 🏢 HR Policy Assistant  
- ⚖️ Legal Document Query  
- 📚 Knowledge Base Systems  

---

# ⚠️ Notes

- Do NOT upload `.env`
- API keys must remain private
- `chroma_db` can be regenerated

---

# 👨‍💻 Author

**Sahil Saiyed**  
AI / Backend Developer

---

# ⭐ Future Improvements

- Image & OCR support  
- Voice-based queries  
- Role-based access  
- Cloud deployment  

---

# 💥 Final Thought

This project demonstrates a complete AI system from document ingestion to intelligent answer generation using modern AI stack.
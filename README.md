# Multi-Modal RAG Flask Application

🚀 A cloud-powered Flask web application that implements a **Multi-Modal RAG (Retrieval-Augmented Generation)** system for PDF documents. Upload any PDF and ask questions about its content - including text, images, and tables!

## ✨ Features

- 📄 **Smart PDF Processing**: Upload PDFs and extract structured content (text, images, tables) via Unstructured API
- 🤖 **Multi-Modal Summarization**: 
  - Text/Table summaries using Llama 3.1 (via Groq)
  - Image descriptions using Google Gemini Vision
- 🧠 **Vector Store**: Uses ChromaDB with Google Gemini embeddings for semantic search
- 💬 **Interactive Q&A**: Ask questions and get answers with relevant context (text + images)
- 🖼️ **Image Context**: View the actual images used to answer your questions
- ☁️ **100% Cloud-Based**: No local dependencies - works on any OS with just Python and API keys

## 🛠️ Tech Stack

- **Backend**: Flask 3.1.2
- **PDF Processing**: Unstructured.io Cloud API
- **LLMs**: 
  - Groq (Llama 3.1-8b-instant) for text/table summarization
  - Google Gemini 2.5 Flash for image descriptions and question answering
- **Embeddings**: Google Gemini Embedding (models/gemini-embedding-001)
- **Vector Store**: ChromaDB 1.3.5
- **Framework**: LangChain 0.3.x series
- **Language**: Python 3.9+

## 📋 Prerequisites

### System Requirements

**All Operating Systems (Windows, Linux, macOS):**
- ✅ Python 3.9 or higher (Python 3.12 recommended)
- ✅ Internet connection (for cloud APIs)
- ❌ **No Poppler, Tesseract, or other binaries needed!**

### 🔑 API Keys (Required)

You'll need **THREE** API keys - all have generous free tiers:

1. **Unstructured API Key** 🆕
   - Get from: [https://unstructured.io](https://unstructured.io)
   - Free tier: **15,000 pages/month**
   - Used for: PDF text/image/table extraction

2. **Groq API Key**
   - Get from: [https://console.groq.com](https://console.groq.com)
   - Free tier: **30 requests/minute, 14,400/day**
   - Used for: Text and table summarization

3. **Google API Key**
   - Get from: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
   - Free tier: **1,500 requests/day**
   - Used for: Image descriptions, embeddings, and question answering

## 🚀 Installation

### Step 1: Clone or navigate to the project directory

```bash
cd "c:\Users\Khush\OneDrive\Desktop\Agile Interview"
# Or your project location
```

### Step 2: Create a virtual environment

```bash
python -m venv venv_new
```

### Step 3: Activate the virtual environment

**Windows (PowerShell):**
```powershell
.\venv_new\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv_new\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source venv_new/bin/activate
```

### Step 4: Install Python dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages:
- Flask (web framework)
- LangChain packages (langchain-core, langchain-unstructured, langchain-groq, langchain-google-genai, langchain-chroma)
- ChromaDB (vector store)
- And all dependencies (~116 packages total)

### Step 5: Set up environment variables (Optional for Server Deployment)

**Two Deployment Options:**

#### Option A: Server-Configured Keys (Traditional)
Create a `.env` file in the project root:

```bash
# Copy from example (if available)
cp .env.example .env

# Or create manually
```

Edit `.env` and add your **THREE** API keys:

```env
# Unstructured API (for PDF processing)
UNSTRUCTURED_API_KEY=your_unstructured_api_key_here

# Groq API (for text summarization)
GROQ_API_KEY=your_groq_api_key_here

# Google API (for embeddings and Q&A)
GOOGLE_API_KEY=your_google_api_key_here
```

#### Option B: User-Provided Keys (Multi-User Deployment) 🆕
**Perfect for sharing with friends or public deployment!**

- ❌ **No `.env` file needed** - Skip this step entirely
- 🔑 **Users enter their own API keys** via the web interface
- 🔒 **Keys never stored** - Only used during processing
- 💾 **Saves your quota** - Each user uses their own free tier
- 🧹 **Auto-cleanup** - Uploaded PDFs deleted after processing

When the app detects no server keys are configured, it will automatically show three password fields on the upload page where users can enter their API keys. This is ideal for:
- Sharing with friends without exposing your keys
- Deploying on platforms like Heroku/Railway
- Avoiding API quota exhaustion
- Multi-user environments

### Step 6: Verify installation

```bash
python test_installation.py
```

This will check:
- ✅ Python version
- ✅ All required packages installed
- ✅ .env file exists with valid API keys
- ✅ Project files and directories present
- ✅ Internet connection available
- ✅ API endpoints accessible

## 🏃 Running the Application

### Step 1: Start the Flask server

Make sure your virtual environment is activated, then:

```bash
python app.py
```

**With server keys (.env configured):**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
✓ Unstructured API key found - using cloud processing
```

**Without server keys (user-provided mode):**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
ℹ️ No API keys configured - users will provide their own
```

### Step 2: Open in browser

Navigate to **http://localhost:5000** in your web browser.

**If using user-provided keys:**
You'll see three password input fields for:
1. Unstructured API Key
2. Groq API Key
3. Google API Key

Each field shows where to get the key and free tier limits. Keys are never stored - only used for that session.

### Step 3: Upload and test with a sample PDF

**For your first test, use a small PDF (1-5 pages) with:**
- Some text content
- At least 1-2 images
- Optional: tables

**Steps:**
1. 📂 Click **"Choose PDF file"** button
2. ⬆️ Select your PDF document
3. ⏳ Click **"Upload and Process"** - wait for processing (30-60 seconds)
4. ✅ You'll see a success message with statistics:
   ```
   Processing complete!
   Total chunks: 15
   Text chunks: 10
   Tables: 1
   Images: 2
   ```

### Step 4: Ask questions

**Try these types of questions:**

1. **General questions:**
   - "What is this document about?"
   - "Summarize the main points"
   - "What topics are covered?"

2. **Specific text questions:**
   - "What does it say about [topic]?"
   - "Explain the section about [subject]"

3. **Image-based questions:**
   - "What does the graph show?"
   - "Describe the diagram in the document"
   - "What information is in the chart?"

4. **Table questions:**
   - "What data is in the table?"
   - "Compare the values in the table"

### Step 5: View results

You'll see:
- 💬 **Answer** to your question
- 📝 **Text context** used (relevant chunks)
- 🖼️ **Images** that were referenced (displayed with base64)
- 📊 **Chat history** of your conversation

### Step 6: Test with another PDF

Click **"Reset & Upload New PDF"** to process a different document.

## 🔄 How It Works - Complete Workflow

### Architecture Overview

```
┌─────────────┐
│   User      │
│  Uploads    │
│    PDF      │
└──────┬──────┘
       │
       ▼
┌────────────────────────────────────────────────────────┐
│                    Flask Backend                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │           1. PDF Processing Phase                │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  Unstructured API (Cloud)                  │  │  │
│  │  │  • OCR text extraction                     │  │  │
│  │  │  • Image detection & base64 encoding       │  │  │
│  │  │  • Table structure extraction              │  │  │
│  │  │  Returns: 100+ elements                    │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  │                      ↓                           │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  Smart Chunking Algorithm                  │  │  │
│  │  │  • Combines ~10 text elements per chunk    │  │  │
│  │  │  • Keeps images separate                   │  │  │
│  │  │  • Preserves tables individually           │  │  │
│  │  │  Result: 100+ → 15 chunks                  │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │           2. Summarization Phase                 │  │
│  │  ┌────────────────┐  ┌───────────────────────┐   │  │
│  │  │  Text Chunks   │→ │  Groq API (Llama 3.1) │   │  │
│  │  │  Table Chunks  │  │  Generates summaries  │   │  │
│  │  └────────────────┘  └───────────────────────┘   │  │
│  │                                                  │  │
│  │  ┌────────────────┐  ┌───────────────────────┐   │  │
│  │  │  Image Chunks  │→ │ Google Gemini Vision  │   │  │
│  │  │  (base64 data) │  │ Describes images      │   │  │
│  │  └────────────────┘  └───────────────────────┘   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │           3. Vector Store Creation               │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  Summaries → Google Gemini Embeddings      │  │  │
│  │  │  Stored in ChromaDB                        │  │  │
│  │  │  Original content linked via doc_id        │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────┐
              │  User Asks        │
              │  Question         │
              └─────────┬─────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 Query Phase                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │  1. Embed question (Google Gemini)               │   │
│  │  2. Search ChromaDB (similarity search)          │   │
│  │  3. Retrieve top 3 relevant chunks               │   │
│  │  4. Get original content (text + base64 images)  │   │
│  └──────────────────────────────────────────────────┘   │
│                          ↓                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Send to Google Gemini:                          │   │
│  │  • User question                                 │   │
│  │  • Retrieved text context                        │   │
│  │  • Retrieved images (base64)                     │   │
│  │                                                  │   │
│  │  Get Answer with multimodal understanding        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │  Display:     │
                  │  • Answer     │
                  │  • Context    │
                  │  • Images     │
                  └───────────────┘
```

### Detailed Step-by-Step Process

#### Phase 1: PDF Upload & Cloud Processing

**Step 1.1 - Upload**
- User uploads PDF through web interface
- Flask saves file temporarily to `uploads/` folder
- Generates unique session ID for user

**Step 1.2 - Send to Unstructured API**
```python
loader = UnstructuredLoader(
    file_path=pdf_path,
    partition_via_api=True,  # Cloud processing
    strategy="hi_res",  # High-resolution OCR
    extract_images_in_pdf=True,  # Extract images
    extract_image_block_to_payload=True  # Get base64 in response
)
```

**Step 1.3 - API Processing**
- Unstructured API performs:
  - OCR on all text (including images with text)
  - Image detection and extraction
  - Table structure recognition
  - Element categorization (Title, NarrativeText, Image, Table)
- Returns typically 100+ elements

**Step 1.4 - Smart Chunking**
```python
Problem: 104 elements = 104+ API calls = Rate limit exceeded!
Solution: Smart chunking algorithm

Logic:
- Buffer text elements (combine ~10 into 1 chunk)
- Keep images separate (needed for visual Q&A)
- Keep tables separate (structured data)

Result: 104 elements → ~15 chunks
```

#### Phase 2: Multi-Modal Summarization

**Step 2.1 - Text/Table Summarization (Groq)**
- Each text/table chunk sent to Llama 3.1 via Groq
- Prompt: "Summarize this content concisely"
- Generates 10-15 summaries
- Rate limit: 30/minute (well within limit)

**Step 2.2 - Image Summarization (Google Gemini)**
- Each image (base64) sent to Gemini Vision
- Prompt: "Describe this image in detail, including any charts, graphs, or text"
- Generates 2-5 image descriptions
- Multimodal understanding (sees the actual image)

#### Phase 3: Vector Store Creation

**Step 3.1 - Generate Embeddings**
- All summaries converted to vectors using Google Gemini Embeddings
- Each vector = 768 dimensions
- Captures semantic meaning

**Step 3.2 - Store in ChromaDB**
```
ChromaDB Structure:
├── Collection: "multi_modal_rag"
│   ├── Document 1:
│   │   ├── Embedding: [0.123, -0.456, ...] (summary)
│   │   ├── Metadata: {doc_id: "uuid-1", type: "text"}
│   │   └── Linked to: Original text chunk
│   │
│   ├── Document 2:
│   │   ├── Embedding: [0.789, 0.234, ...] (image description)
│   │   ├── Metadata: {doc_id: "uuid-2", type: "image"}
│   │   └── Linked to: Original base64 image
```

**Step 3.3 - Multi-Vector Retrieval Setup**
- Summaries stored in vector DB (searchable)
- Original content in document store (for context)
- Linked via `doc_id` in metadata

#### Phase 4: Question Answering

**Step 4.1 - User Query**
- User types question: "What does the graph show?"

**Step 4.2 - Embed Question**
- Question converted to vector using same embedding model
- Ensures query and documents in same semantic space

**Step 4.3 - Similarity Search**
```python
ChromaDB.similarity_search(query_vector, k=3)
# Returns top 3 most similar summaries
```

**Step 4.4 - Retrieve Original Content**
- For each matched summary, get `doc_id`
- Lookup original content in document store
- Retrieve:
  - Full text chunks
  - Base64 image data
  - Table HTML

**Step 4.5 - Build Context Prompt**
```python
Prompt = f"""
User Question: {question}

Context (Text):
{retrieved_text_chunks}

Context (Images):
[Base64 image 1]
[Base64 image 2]

Based on the above context, answer the question.
"""
```

**Step 4.6 - Get Answer from Gemini**
- Send prompt + images to Google Gemini
- Model sees both text AND images
- Generates comprehensive answer

**Step 4.7 - Display Results**
- Show answer to user
- Display text context used
- Show images that were referenced
- Save to chat history

### Key Algorithm: Smart Chunking

```python
def smart_chunk(elements):
    chunks = []
    text_buffer = []
    
    for element in elements:
        if element.type in ['Image', 'Table']:
            # Flush text buffer first
            if text_buffer:
                chunks.append(combine(text_buffer))
                text_buffer = []
            # Add image/table as separate chunk
            chunks.append(element)
        else:
            # Accumulate text elements
            text_buffer.append(element)
            if len(text_buffer) >= 10:
                # Flush when buffer full
                chunks.append(combine(text_buffer))
                text_buffer = []
    
    # Flush remaining
    if text_buffer:
        chunks.append(combine(text_buffer))
    
    return chunks

# Result: Reduces API calls by ~85%
# Example: 104 elements → 15 chunks
```

### Why This Approach Works

1. **Cloud Processing** → No local dependencies, works everywhere
2. **Smart Chunking** → Avoids rate limits, reduces costs
3. **Multi-Modal** → Understands both text and images
4. **Semantic Search** → Finds relevant content even with different wording
5. **Original Context** → Retrieves full content for accurate answers

### Performance Characteristics

| Metric | Value |
|--------|-------|
| PDF Processing Time | 30-60 seconds |
| Elements Extracted | 50-150 per document |
| Chunks Created | 10-20 per document |
| API Calls (Processing) | 15-25 calls |
| Query Response Time | 2-5 seconds |
| API Calls (Query) | 2-3 calls |
| Accuracy | High (multimodal context) |

## 📁 Project Structure

```
.
├── app.py                      # Flask application and routes
├── rag_processor.py            # Core RAG processing logic (API-based)
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies (cloud-only)
├── test_installation.py        # Installation verification script
├── .env                        # Environment variables (create from .env.example)
├── .env.example               # Example environment file
├── uploads/                    # Temporary uploaded PDF files (auto-created)
├── templates/
│   └── index.html             # Main HTML template
└── static/
    ├── css/
    │   └── style.css          # Styles
    └── js/
        └── main.js            # Frontend JavaScript
```

## 🔌 API Endpoints

### POST /upload
Upload and process a PDF file.

**Request:**
- Form data with `file` field containing PDF

**Response:**
```json
{
  "success": true,
  "session_id": "uuid",
  "message": "PDF processed successfully",
  "stats": {
    "total_chunks": 10,
    "text_chunks": 8,
    "tables": 1,
    "images": 2
  }
}
```

### POST /ask
Ask a question about the uploaded document.

**Request:**
```json
{
  "question": "What is discussed in this document?"
}
```

**Response:**
```json
{
  "success": true,
  "answer": "The document discusses...",
  "context": {
    "texts": [...],
    "images": ["base64_image_1", "base64_image_2"]
  }
}
```

### POST /reset
Reset the session and clear uploaded documents.

**Response:**
```json
{
  "success": true,
  "message": "Session reset successfully"
}
```

## 💰 API Rate Limits & Costs

### Free Tier Limits:
- **Unstructured API**: 15,000 pages/month
- **Groq API**: 30 requests/minute, 14,400 requests/day
- **Google Gemini**: 1,500 requests/day, 1 million tokens/day

### Typical Document Processing:
- **5-page PDF**: ~10-15 API calls total
  - 1 call to Unstructured API
  - 5-10 calls to Groq (text summaries)
  - 2-5 calls to Gemini (image descriptions + embeddings)
- **Processing time**: 30-60 seconds
- **Cost**: Free within rate limits

## 🔧 Troubleshooting

### Error: "UNSTRUCTURED_API_KEY environment variable is required"
Make sure you've created a `.env` file with your Unstructured API key.

### Error: "GROQ_API_KEY environment variable not set"
Add your Groq API key to the `.env` file.

### Error: "Rate limit reached"
You've exceeded the free tier limits. Options:
- Wait for the rate limit to reset (usually 1 minute for Groq)
- Upgrade to a paid tier
- Use smaller PDFs or fewer images

### PDF processing fails
- Check that all API keys are valid
- Verify you have internet connection
- Check Unstructured API status at [status.unstructured.io](https://status.unstructured.io)

### Images not appearing in answers
- Ensure your PDF actually contains images
- Check that images were extracted (look for "Found X elements with image_base64" in console)
- Verify Google API key has Gemini Pro Vision access

## 🏗️ Architecture Advantages

### Why Cloud-Based?
✅ **No local dependencies** - Works on any OS without installing binaries  
✅ **Better OCR** - Unstructured API uses advanced OCR models  
✅ **Scalable** - No local resource constraints  
✅ **Easier deployment** - Just Python + API keys  
✅ **Maintained** - APIs updated by providers  

### Trade-offs:
⚠ **Requires internet** - Cannot work offline  
⚠ **API costs** - Free tiers have limits  
⚠ **Data privacy** - Documents sent to third-party APIs  
⚠ **Rate limits** - Need to handle throttling  

## 🔒 Security Notes

- **API Keys Security:**
  - When using server keys: Stored in `.env` (never commit this file!)
  - When using user-provided keys: Keys sent via HTTPS (use secure connection in production), never stored on server
- **File Storage:** 
  - PDFs temporarily saved to `uploads/` folder during processing
  - **Auto-deleted immediately after processing completes** (memory-efficient)
  - Reset endpoint cleans up any orphaned files
- **Session Management:** Each user session isolated, no cross-user data leakage
- **Best Practices:**
  - Use HTTPS in production deployment
  - Consider encrypting sensitive documents before upload
  - For user-provided keys, advise users to use API keys with rate limits
  - Monitor API usage to prevent quota exhaustion

## 🚀 Deployment Options

### Local Development
- Use server keys in `.env` for personal use
- Fast iteration without entering keys repeatedly

### Multi-User/Public Deployment
- **Don't include `.env` file** with API keys
- Users provide their own API keys via UI
- Deploy to platforms like:
  - Heroku: `git push heroku main`
  - Railway: Connect GitHub repo
  - DigitalOcean App Platform
  - AWS/Azure/GCP with container
- **Benefits:**
  - No API quota sharing
  - No key exposure risk
  - Each user's free tier applies separately
  - Automatic file cleanup prevents storage issues

## 🚀 Future Enhancements

- [ ] Add support for multiple file formats (DOCX, PPTX, etc.)
- [ ] Implement caching to reduce API calls
- [ ] Add persistent ChromaDB storage
- [ ] Support for larger documents (batch processing)
- [ ] Export Q&A history
- [ ] Multi-document comparison
- [ ] Fine-tune prompts for specific use cases

## 📝 License

This project is for educational purposes.

## 🙏 Credits

- Built with [LangChain](https://langchain.com/)
- PDF processing by [Unstructured.io](https://unstructured.io/)
- LLMs: [Groq](https://groq.com/) and [Google Gemini](https://ai.google.dev/)
- Vector store: [ChromaDB](https://www.trychroma.com/)

## 💬 Support

For issues or questions:
1. Check the troubleshooting section
2. Verify all API keys are valid
3. Check API status pages
4. Review console logs for specific errors

# Multi-Modal RAG Flask Application

This is a Flask web application that implements a Multi-Modal RAG (Retrieval-Augmented Generation) system for PDF documents. It extracts text, images, and tables from PDFs, generates summaries, and allows users to ask questions about the document content.

## Features

- **PDF Processing**: Upload PDF documents and extract structured content (text, images, tables)
- **Multi-Modal Summarization**: 
  - Text/Table summaries using Llama 3.1 (via Groq)
  - Image descriptions using Google Gemini
- **Vector Store**: Uses Chroma DB with Google Gemini embeddings
- **Question Answering**: Interactive Q&A interface with context retrieval
- **Chat History**: Track conversation history with the document

## Tech Stack

- **Backend**: Flask
- **PDF Processing**: Unstructured.io
- **LLMs**: 
  - Groq (Llama 3.1-8b-instant) for text summarization
  - Google Gemini 2.5 Flash for image description and Q&A
- **Embeddings**: Google Gemini Embeddings
- **Vector Store**: ChromaDB
- **Framework**: LangChain

## Prerequisites

### System Requirements

**Windows:**
- Python 3.9 or higher
- Poppler for Windows (for PDF processing)

**Linux:**
```bash
sudo apt-get install poppler-utils tesseract-ocr libmagic-dev
```

**macOS:**
```bash
brew install poppler tesseract libmagic
```

### API Keys

You'll need the following API keys:
1. **Groq API Key** - Get from [https://console.groq.com](https://console.groq.com)
2. **Google API Key** - Get from [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

## Installation

### 1. Clone or navigate to the project directory

```bash
cd "c:\Users\Khush\OneDrive\Desktop\Agile Interview"
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 4. Install Poppler (Windows only)

Download Poppler for Windows from: https://github.com/oschwartz10612/poppler-windows/releases/

Extract and add the `bin` folder to your system PATH.

### 5. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 6. Set up environment variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
SECRET_KEY=your_flask_secret_key_here
FLASK_ENV=development
```

## Running the Application

### 1. Start the Flask server

```bash
python app.py
```

The application will start on `http://localhost:5000`

### 2. Open in browser

Navigate to `http://localhost:5000` in your web browser.

### 3. Using the application

1. **Upload a PDF**: Click "Choose PDF file" and select your document
2. **Wait for processing**: The system will extract and process content (this may take a few minutes)
3. **Ask questions**: Once processed, type your questions in the text area
4. **View answers**: See the answer along with the context used to generate it
5. **Reset**: Click "Reset" to upload a new document

## Project Structure

```
.
├── app.py                      # Flask application and routes
├── rag_processor.py            # Core RAG processing logic
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create from .env.example)
├── .env.example               # Example environment file
├── uploads/                    # Uploaded PDF files (auto-created)
├── templates/
│   └── index.html             # Main HTML template
└── static/
    ├── css/
    │   └── style.css          # Styles
    └── js/
        └── main.js            # Frontend JavaScript
```

## How It Works

1. **PDF Upload & Processing**
   - User uploads a PDF file
   - Unstructured.io extracts text, tables, and images
   - Content is chunked for optimal processing

2. **Summarization**
   - Text chunks: Summarized using Llama 3.1 via Groq
   - Images: Described using Google Gemini vision model
   - Tables: Summarized using Llama 3.1

3. **Vector Storage**
   - Summaries are embedded using Google Gemini embeddings
   - Stored in ChromaDB vector database
   - Original content linked via document IDs

4. **Question Answering**
   - User question is embedded and used to retrieve relevant content
   - Retrieved content (text + images) is sent to Google Gemini
   - Model generates answer based on provided context

## API Endpoints

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
    "images": 1
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
    "images_count": 1
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

## Troubleshooting

### Error: "GROQ_API_KEY environment variable not set"
Make sure you've created a `.env` file with your API keys.

### Error: "Poppler not found"
Install Poppler for your operating system (see Prerequisites section).

### PDF processing is slow
This is normal for large PDFs with many images. The system needs to:
- Extract all content
- Generate summaries for each chunk
- Create embeddings
- Store in vector database

### Out of memory errors
Try reducing the PDF size or splitting it into smaller documents.

## Development

To run in development mode with auto-reload:

```bash
export FLASK_ENV=development  # Linux/macOS
set FLASK_ENV=development     # Windows CMD
$env:FLASK_ENV="development"  # Windows PowerShell

python app.py
```

## Production Deployment

For production deployment:

1. Set `FLASK_ENV=production` in `.env`
2. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```
3. Set up a reverse proxy (nginx/Apache)
4. Use a proper secret key for sessions
5. Consider rate limiting for API endpoints

## License

This project is for educational purposes.

## Credits

- Built with [LangChain](https://langchain.com/)
- PDF processing by [Unstructured.io](https://unstructured.io/)
- LLMs: [Groq](https://groq.com/) and [Google Gemini](https://ai.google.dev/)

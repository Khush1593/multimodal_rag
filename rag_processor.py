"""
RAG Processor Module
Handles PDF processing, summarization, and question answering
"""

import os
import sys
from typing import List, Dict, Any
import uuid
from base64 import b64decode

# Add Poppler to PATH for Windows
POPPLER_PATH = r"C:\Users\Khush\OneDrive\Desktop\Agile Interview\poppler\poppler-24.08.0\Library\bin"
if os.path.exists(POPPLER_PATH):
    os.environ["PATH"] = POPPLER_PATH + os.pathsep + os.environ.get("PATH", "")
    print(f"✓ Poppler path added: {POPPLER_PATH}")

from unstructured.partition.pdf import partition_pdf
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from langchain_core.stores import InMemoryStore
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage


class CustomMultiVectorRetriever:
    """Custom implementation of MultiVectorRetriever"""
    
    def __init__(self, vectorstore, docstore, id_key="doc_id"):
        self.vectorstore = vectorstore
        self.docstore = docstore
        self.id_key = id_key
    
    def invoke(self, query: str, **kwargs) -> List[Document]:
        """Retrieve documents based on query"""
        # Get similar documents from vectorstore
        sub_docs = self.vectorstore.similarity_search(query, k=3)
        
        # Retrieve original documents from docstore
        ids = []
        for d in sub_docs:
            if self.id_key in d.metadata:
                ids.append(d.metadata[self.id_key])
        
        # Get unique original documents
        docs = []
        seen_ids = set()
        for id in ids:
            if id not in seen_ids:
                doc = self.docstore.mget([id])[0]
                if doc:
                    docs.append(doc)
                    seen_ids.add(id)
        
        return docs
    
    def __call__(self, query: str) -> List[Document]:
        """Make the retriever callable"""
        return self.invoke(query)


class RAGProcessor:
    """Main RAG processing class"""
    
    def __init__(self):
        """Initialize the RAG processor"""
        self.chunks = None
        self.texts = []
        self.tables = []
        self.images = []
        self.text_summaries = []
        self.table_summaries = []
        self.image_summaries = []
        self.retriever = None
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize LLM models and embeddings"""
        # Check for required API keys
        if not os.environ.get('GROQ_API_KEY'):
            raise ValueError("GROQ_API_KEY environment variable not set")
        if not os.environ.get('GOOGLE_API_KEY'):
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        # Initialize summarization model (Groq)
        self.summarization_model = ChatGroq(
            temperature=0.5, 
            model="llama-3.1-8b-instant"
        )
        
        # Initialize image description model (Google)
        self.image_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash"
        )
        
        # Initialize QA model (Google)
        self.qa_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash"
        )
        
        # Initialize embeddings (Google)
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001"
        )
    
    def process_pdf(self, file_path: str) -> Dict[str, int]:
        """
        Process PDF file and extract elements
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with processing statistics
        """
        print(f"Processing PDF: {file_path}")
        
        # Extract elements from PDF
        try:
            self.chunks = partition_pdf(
                filename=file_path,
                infer_table_structure=True,
                strategy="hi_res",
                extract_image_block_types=["Image"],
                extract_image_block_to_payload=True,
                chunking_strategy="by_title",
                max_characters=10000,
                combine_text_under_n_chars=2000,
                new_after_n_chars=6000,
            )
        except Exception as e:
            error_msg = str(e).lower()
            if 'tesseract' in error_msg:
                print("\n" + "="*80)
                print("⚠ ERROR: Tesseract OCR is not installed!")
                print("="*80)
                print("\nTo enable full multi-modal processing with images, install Tesseract:")
                print("\nOption 1 - Using Chocolatey (Recommended):")
                print("  choco install tesseract")
                print("\nOption 2 - Manual Installation:")
                print("  1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
                print("  2. Install to: C:\\Program Files\\Tesseract-OCR")
                print("  3. Add to PATH: C:\\Program Files\\Tesseract-OCR")
                print("\nOption 3 - Set environment variable:")
                print("  $env:TESSERACT_CMD = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'")
                print("\n" + "="*80)
                print("Falling back to text-only extraction (no images)...")
                print("="*80 + "\n")
                
                # Fallback to basic strategy without OCR and chunking
                self.chunks = partition_pdf(
                    filename=file_path,
                    strategy="auto",
                )
            else:
                raise
        
        print(f"Extracted {len(self.chunks)} chunks")
        
        # Separate elements
        self._separate_elements()
        
        # Generate summaries
        self._generate_summaries()
        
        # Create vector store
        self._create_vectorstore()
        
        return {
            'total_chunks': len(self.chunks),
            'text_chunks': len(self.texts),
            'tables': len(self.tables),
            'images': len(self.images)
        }
    
    def _separate_elements(self):
        """Separate extracted elements into tables, texts, and images"""
        self.tables = []
        self.texts = []
        
        for chunk in self.chunks:
            if "Table" in str(type(chunk)):
                self.tables.append(chunk)
            if "CompositeElement" in str(type(chunk)):
                self.texts.append(chunk)
        
        # Extract images from CompositeElement objects
        self.images = self._get_images_base64(self.chunks)
        
        print(f"Separated: {len(self.texts)} texts, {len(self.tables)} tables, {len(self.images)} images")
    
    def _get_images_base64(self, chunks) -> List[str]:
        """Extract base64 encoded images from chunks"""
        images_b64 = []
        for chunk in chunks:
            if "CompositeElement" in str(type(chunk)):
                chunk_els = chunk.metadata.orig_elements
                for el in chunk_els:
                    if "Image" in str(type(el)):
                        images_b64.append(el.metadata.image_base64)
        return images_b64
    
    def _generate_summaries(self):
        """Generate summaries for texts, tables, and images"""
        print("Generating summaries...")
        
        # Text and table summaries
        prompt_text = """
You are an assistant tasked with summarizing tables and text.
Give a concise summary of the table or text.

Respond only with the summary, no additionnal comment.
Do not start your message by saying "Here is a summary" or anything like that.
Just give the summary as it is.

Table or text chunk: {element}
"""
        prompt = ChatPromptTemplate.from_template(prompt_text)
        summarize_chain = {"element": lambda x: x} | prompt | self.summarization_model | StrOutputParser()
        
        # Summarize texts
        if self.texts:
            self.text_summaries = summarize_chain.batch(self.texts, {"max_concurrency": 3})
            print(f"Generated {len(self.text_summaries)} text summaries")
        
        # Summarize tables
        if self.tables:
            tables_html = [table.metadata.text_as_html for table in self.tables]
            self.table_summaries = summarize_chain.batch(tables_html, {"max_concurrency": 3})
            print(f"Generated {len(self.table_summaries)} table summaries")
        
        # Image summaries
        if self.images:
            self._generate_image_summaries()
    
    def _generate_image_summaries(self):
        """Generate summaries for images using multimodal model"""
        prompt_template = """Describe the image in detail. For context,
the image is part of a document. Be specific about graphs, charts, diagrams, and any text visible in the image."""
        
        messages = [
            (
                "user",
                [
                    {"type": "text", "text": prompt_template},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/jpeg;base64,{image}"},
                    },
                ],
            )
        ]
        
        prompt = ChatPromptTemplate.from_messages(messages)
        chain = prompt | self.image_model | StrOutputParser()
        
        self.image_summaries = chain.batch(self.images)
        print(f"Generated {len(self.image_summaries)} image summaries")
    
    def _create_vectorstore(self):
        """Create vector store with summaries"""
        print("Creating vector store...")
        
        # Initialize vector store
        vectorstore = Chroma(
            collection_name="multi_modal_rag",
            embedding_function=self.embeddings
        )
        
        store = InMemoryStore()
        id_key = "doc_id"
        
        self.retriever = CustomMultiVectorRetriever(
            vectorstore=vectorstore,
            docstore=store,
            id_key=id_key,
        )
        
        # Add texts
        if self.texts and self.text_summaries:
            doc_ids = [str(uuid.uuid4()) for _ in self.texts]
            summary_texts = [
                Document(page_content=summary, metadata={id_key: doc_ids[i]}) 
                for i, summary in enumerate(self.text_summaries)
            ]
            self.retriever.vectorstore.add_documents(summary_texts)
            self.retriever.docstore.mset(list(zip(doc_ids, self.texts)))
            print(f"Added {len(self.texts)} text documents")
        
        # Add images
        if self.images and self.image_summaries:
            img_ids = [str(uuid.uuid4()) for _ in self.images]
            summary_img = [
                Document(page_content=summary, metadata={id_key: img_ids[i]})
                for i, summary in enumerate(self.image_summaries)
            ]
            self.retriever.vectorstore.add_documents(summary_img)
            self.retriever.docstore.mset(list(zip(img_ids, self.images)))
            print(f"Added {len(self.images)} image documents")
        
        print("Vector store created successfully")
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a question using the RAG pipeline
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with response and context
        """
        if not self.retriever:
            raise ValueError("No document processed. Please process a PDF first.")
        
        def parse_docs(docs):
            """Split base64-encoded images and texts"""
            b64 = []
            text = []
            for doc in docs:
                try:
                    b64decode(doc)
                    b64.append(doc)
                except Exception:
                    text.append(doc)
            return {"images": b64, "texts": text}
        
        def build_prompt(kwargs):
            """Build prompt with context and images"""
            docs_by_type = kwargs["context"]
            user_question = kwargs["question"]
            
            context_text = ""
            if len(docs_by_type["texts"]) > 0:
                for text_element in docs_by_type["texts"]:
                    context_text += text_element.text
            
            prompt_template = f"""
Answer the question based only on the following context, which can include text, tables, and the below image.
Context: {context_text}
Question: {user_question}
"""
            
            prompt_content = [{"type": "text", "text": prompt_template}]
            
            if len(docs_by_type["images"]) > 0:
                for image in docs_by_type["images"]:
                    prompt_content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                        }
                    )
            
            return ChatPromptTemplate.from_messages([
                HumanMessage(content=prompt_content),
            ])
        
        # Create chain with sources
        chain_with_sources = {
            "context": self.retriever | RunnableLambda(parse_docs),
            "question": RunnablePassthrough(),
        } | RunnablePassthrough().assign(
            response=(
                RunnableLambda(build_prompt)
                | self.qa_model
                | StrOutputParser()
            )
        )
        
        # Get answer
        result = chain_with_sources.invoke(question)
        
        return result

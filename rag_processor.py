"""
RAG Processor Module
Handles PDF processing, summarization, and question answering
"""

import os
import sys
import time
import random
from typing import List, Dict, Any
import uuid
from base64 import b64decode
import json
import zlib

from langchain_unstructured import UnstructuredLoader
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
    
    def __init__(self, unstructured_api_key=None, groq_api_key=None, google_api_key=None):
        """Initialize the RAG processor with optional API keys"""
        self.chunks = None
        self.texts = []
        self.tables = []
        self.images = []
        self.text_summaries = []
        self.table_summaries = []
        self.image_summaries = []
        self.retriever = None
        
        # Store API keys (from parameters or environment)
        self.unstructured_api_key = unstructured_api_key or os.environ.get('UNSTRUCTURED_API_KEY')
        self.groq_api_key = groq_api_key or os.environ.get('GROQ_API_KEY')
        self.google_api_key = google_api_key or os.environ.get('GOOGLE_API_KEY')
        
        # Check if Unstructured API key is available
        if not self.unstructured_api_key:
            raise ValueError("UNSTRUCTURED_API_KEY is required for cloud processing")
        
        print("✓ Unstructured API key provided - using cloud processing")
        
        # Initialize models with provided keys
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize LLM models and embeddings with provided API keys"""
        # Check for required API keys
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required")
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required")
        
        # Initialize summarization model (Groq)
        self.summarization_model = ChatGroq(
            temperature=0.5, 
            model="llama-3.1-8b-instant",
            api_key=self.groq_api_key
        )
        
        # Initialize image description model (Google)
        self.image_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.google_api_key
        )
        
        # Initialize QA model (Google)
        self.qa_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.google_api_key
        )
        
        # Initialize embeddings (Google)
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=self.google_api_key
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
        
        # Process with Unstructured API
        print("Using Unstructured API for cloud processing...")
        try:
            # Get images as base64 in payload - chunking is DISABLED to preserve images
            loader = UnstructuredLoader(
                file_path=file_path,
                partition_via_api=True,
                api_key=self.unstructured_api_key,
                strategy="hi_res",
                pdf_infer_table_structure=True,
                extract_images_in_pdf=True,
                extract_image_block_types=["Image", "Table"],
                extract_image_block_to_payload=True,  # Get base64 in response
            )
            langchain_docs = loader.load()
            
            print(f"Received {len(langchain_docs)} elements from API")
            
            # Check for images
            img_count = sum(1 for doc in langchain_docs if doc.metadata.get('image_base64'))
            print(f"★ Found {img_count} elements with image_base64")
            
            # Convert to unstructured elements format
            self.chunks = self._convert_langchain_docs_to_elements(langchain_docs)
            
            # Manually reduce element count for summarization to avoid rate limits
            # Group non-image text elements together
            self.chunks = self._smart_chunk_for_summarization(self.chunks)
            
            print("✓ API processing successful")
        except Exception as e:
            print(f"⚠ API processing failed: {e}")
            raise RuntimeError(f"Failed to process PDF with Unstructured API: {e}")
        
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
    
    def _convert_langchain_docs_to_elements(self, langchain_docs: List[Document]) -> List[Any]:
        """Convert LangChain documents back to element-like objects
        
        Args:
            langchain_docs: List of LangChain Document objects
            
        Returns:
            List of element-like objects compatible with existing processing
        """
        print(f"Converting {len(langchain_docs)} LangChain documents to elements...")
        
        # Create mock element objects that have the attributes we need
        class MockElement:
            def __init__(self, doc: Document):
                self.text = doc.page_content
                category = doc.metadata.get('category', 'UncategorizedText')
                
                # Create metadata object with proper structure
                class MetadataObj:
                    def __init__(self, doc):
                        self.text_as_html = doc.metadata.get('text_as_html', doc.page_content)
                        self.page_number = doc.metadata.get('page_number', 1)
                        self.category = doc.metadata.get('category', 'Text')
                        self.image_base64 = doc.metadata.get('image_base64')
                        
                        # IMPORTANT: Decode orig_elements from base64 + zlib compressed JSON
                        orig_elements_raw = doc.metadata.get('orig_elements', [])
                        if isinstance(orig_elements_raw, str):
                            try:
                                # Decode base64, decompress zlib, parse JSON
                                compressed = b64decode(orig_elements_raw)
                                decompressed = zlib.decompress(compressed)
                                self.orig_elements = json.loads(decompressed)
                            except Exception as e:
                                print(f"Failed to decode orig_elements: {e}")
                                self.orig_elements = []
                        else:
                            self.orig_elements = orig_elements_raw
                
                self.metadata = MetadataObj(doc)
                self._langchain_metadata = doc.metadata
                self._type_str = category
            
            def __repr__(self):
                return f"<{self._type_str}>"
        
        elements = [MockElement(doc) for doc in langchain_docs]
        
        # Debug: print what types we got
        categories = {}
        for elem in elements:
            cat = elem.metadata.category
            categories[cat] = categories.get(cat, 0) + 1
        print(f"Element categories: {categories}")
        
        return elements
    

    def _smart_chunk_for_summarization(self, elements):
        """Combine text elements to reduce API calls while keeping images separate"""
        chunked = []
        text_buffer = []
        
        for elem in elements:
            category = getattr(elem.metadata, 'category', '')
            
            # Keep images and tables separate
            if category in ['Image', 'Table']:
                # Flush text buffer first
                if text_buffer:
                    # Combine buffered text elements
                    combined_text = '\n\n'.join([e.text for e in text_buffer if hasattr(e, 'text')])
                    if combined_text.strip():
                        # Use first element as base, update text
                        first_elem = text_buffer[0]
                        first_elem.text = combined_text
                        chunked.append(first_elem)
                    text_buffer = []
                
                # Add image/table as-is
                chunked.append(elem)
            else:
                # Buffer text elements
                text_buffer.append(elem)
                
                # Flush buffer every 10 text elements to create chunks
                if len(text_buffer) >= 10:
                    combined_text = '\n\n'.join([e.text for e in text_buffer if hasattr(e, 'text')])
                    if combined_text.strip():
                        first_elem = text_buffer[0]
                        first_elem.text = combined_text
                        chunked.append(first_elem)
                    text_buffer = []
        
        # Flush remaining
        if text_buffer:
            combined_text = '\n\n'.join([e.text for e in text_buffer if hasattr(e, 'text')])
            if combined_text.strip():
                first_elem = text_buffer[0]
                first_elem.text = combined_text
                chunked.append(first_elem)
        
        print(f"Smart chunking: {len(elements)} elements → {len(chunked)} chunks")
        return chunked
    

    def _separate_elements(self):
        """Separate extracted elements into tables, texts, and images"""
        self.tables = []
        self.texts = []
        
        for chunk in self.chunks:
            chunk_type = str(type(chunk))
            category = getattr(chunk.metadata, 'category', 'Unknown')
            
            # Check both the type string and the category metadata
            if "Table" in chunk_type or "Table" in category:
                self.tables.append(chunk)
            elif "CompositeElement" in chunk_type or category in ['Text', 'NarrativeText', 'Title', 'UncategorizedText', 'ListItem']:
                self.texts.append(chunk)
            # Treat anything with text content as text element
            elif hasattr(chunk, 'text') and chunk.text and chunk.text.strip():
                self.texts.append(chunk)
        
        # Load images from extracted directory or extract from elements
        self.images = self._load_images()
        
        print(f"Separated: {len(self.texts)} texts, {len(self.tables)} tables, {len(self.images)} images")
    
    def _load_images(self) -> List[str]:
        """Load images from elements (base64 in metadata)"""
        images_b64 = []
        
        # Extract from elements with image_base64 in metadata
        for chunk in self.chunks:
            # Check direct metadata
            if hasattr(chunk, 'metadata'):
                img_data = getattr(chunk.metadata, 'image_base64', None)
                if img_data and self._is_valid_base64_image(img_data):
                    images_b64.append(img_data)
                    print(f"Found image in element metadata (length: {len(img_data)} chars)")
                    continue
            
            # Check LangChain metadata
            if hasattr(chunk, '_langchain_metadata'):
                img_data = chunk._langchain_metadata.get('image_base64')
                if img_data and self._is_valid_base64_image(img_data):
                    images_b64.append(img_data)
                    print(f"Found image in LangChain metadata (length: {len(img_data)} chars)")
        
        print(f"Total images loaded: {len(images_b64)}")
        return images_b64
    
    def _is_valid_base64_image(self, data: str) -> bool:
        """Check if string is valid base64 encoded image data"""
        if not data or len(data) < 100:
            return False
        
        # Check if it looks like base64 (only contains base64 characters)
        import re
        if not re.match(r'^[A-Za-z0-9+/=]+$', data[:100]):
            return False
        
        # Try to decode as base64
        try:
            decoded = b64decode(data)
            # Check for common image file signatures
            # JPEG: FF D8 FF, PNG: 89 50 4E 47, GIF: 47 49 46
            if decoded[:3] in [b'\xff\xd8\xff', b'\x89\x50\x4e'] or decoded[:3] == b'GIF':
                return True
            return False
        except:
            return False
    
    # Groq free-tier-friendly batching parameters.
    # Free tier: ~30 RPM for llama-3.1-8b-instant. Batch=5 with 15s delay → ~20 RPM.
    GROQ_BATCH_SIZE = 5
    GROQ_BATCH_DELAY_SECONDS = 15
    GROQ_MAX_RETRIES = 5

    def _invoke_with_retry(self, chain, payload):
        """Invoke a chain with exponential backoff on rate-limit / transient errors."""
        for attempt in range(self.GROQ_MAX_RETRIES):
            try:
                return chain.invoke(payload)
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limited = (
                    "429" in err_str
                    or "rate limit" in err_str
                    or "too many requests" in err_str
                    or "quota" in err_str
                )
                if attempt == self.GROQ_MAX_RETRIES - 1:
                    raise
                # Exponential backoff with jitter; longer waits for rate limits.
                base_wait = 30 if is_rate_limited else 2
                wait_seconds = base_wait * (2 ** attempt) + random.uniform(0, 2)
                print(f"  ⚠ Request failed ({type(e).__name__}); retrying in {wait_seconds:.1f}s "
                      f"(attempt {attempt + 1}/{self.GROQ_MAX_RETRIES})")
                time.sleep(wait_seconds)

    def _batch_summarize(self, chain, items, label):
        """Run summarization in small batches with a delay between batches to respect Groq rate limits."""
        summaries = []
        total = len(items)
        for batch_start in range(0, total, self.GROQ_BATCH_SIZE):
            batch = items[batch_start:batch_start + self.GROQ_BATCH_SIZE]
            batch_num = batch_start // self.GROQ_BATCH_SIZE + 1
            total_batches = (total + self.GROQ_BATCH_SIZE - 1) // self.GROQ_BATCH_SIZE
            print(f"  Summarizing {label} batch {batch_num}/{total_batches} "
                  f"({len(batch)} items)")
            for item in batch:
                summaries.append(self._invoke_with_retry(chain, item))
            # Pause between batches (but not after the last one) to stay under RPM limit.
            if batch_start + self.GROQ_BATCH_SIZE < total:
                print(f"  ⏸ Pausing {self.GROQ_BATCH_DELAY_SECONDS}s to respect Groq rate limit...")
                time.sleep(self.GROQ_BATCH_DELAY_SECONDS)
        return summaries

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

        # Summarize texts (batched with delays to avoid Groq rate limits)
        if self.texts:
            self.text_summaries = self._batch_summarize(summarize_chain, self.texts, "text")
            print(f"Generated {len(self.text_summaries)} text summaries")

        # Pause before tables so we don't immediately re-burst into Groq.
        if self.texts and self.tables:
            print(f"⏸ Pausing {self.GROQ_BATCH_DELAY_SECONDS}s before processing tables...")
            time.sleep(self.GROQ_BATCH_DELAY_SECONDS)

        # Summarize tables
        if self.tables:
            tables_html = [table.metadata.text_as_html for table in self.tables]
            self.table_summaries = self._batch_summarize(summarize_chain, tables_html, "table")
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

        # Run sequentially with retry to be safe against image-model rate limits.
        self.image_summaries = []
        total = len(self.images)
        for idx, image in enumerate(self.images, start=1):
            print(f"  Summarizing image {idx}/{total}")
            self.image_summaries.append(self._invoke_with_retry(chain, {"image": image}))
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

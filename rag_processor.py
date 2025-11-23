"""
RAG Processor Module
Handles PDF processing, summarization, and question answering
"""

import os
import sys
from typing import List, Dict, Any
import uuid
from base64 import b64decode, b64encode
import json
import zlib

# Add Poppler to PATH for Windows
POPPLER_PATH = r"C:\Users\Khush\OneDrive\Desktop\Agile Interview\poppler\poppler-24.08.0\Library\bin"
if os.path.exists(POPPLER_PATH):
    os.environ["PATH"] = POPPLER_PATH + os.pathsep + os.environ.get("PATH", "")
    print(f"✓ Poppler path added: {POPPLER_PATH}")

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
        
        # Check if Unstructured API key is available
        self.use_api = bool(os.environ.get('UNSTRUCTURED_API_KEY'))
        if self.use_api:
            print("✓ Unstructured API key found - will use cloud processing")
        else:
            print("⚠ No Unstructured API key - will use local processing")
        
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
        
        # Use UnstructuredLoader with API if available
        if self.use_api:
            print("Using Unstructured API for cloud processing...")
            try:
                # Get images as base64 in payload - chunking is DISABLED to preserve images
                loader = UnstructuredLoader(
                    file_path=file_path,
                    partition_via_api=True,
                    api_key=os.environ.get('UNSTRUCTURED_API_KEY'),
                    strategy="hi_res",
                    pdf_infer_table_structure=True,
                    extract_images_in_pdf=True,
                    extract_image_block_types=["Image"],
                    extract_image_block_to_payload=True,  # Get base64 in response
                    # NO chunking - it strips image base64 data
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
                print("Falling back to local processing...")
                self.chunks = self._partition_locally(file_path)
        else:
            print("Using local processing...")
            self.chunks = self._partition_locally(file_path)
        
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
    
    def _debug_api_response(self, langchain_docs):
        """Save API response details to JSON for debugging"""
        if not langchain_docs:
            return
        
        debug_data = {
            'document_count': len(langchain_docs),
            'documents': []
        }
        
        image_count = 0
        for idx, doc in enumerate(langchain_docs):
            doc_info = {
                'index': idx,
                'metadata_keys': list(doc.metadata.keys()),
                'category': doc.metadata.get('category'),
                'page_number': doc.metadata.get('page_number'),
                'has_image_base64': 'image_base64' in doc.metadata
            }
            
            # Check for direct image_base64 in metadata
            if doc.metadata.get('image_base64'):
                img_b64 = doc.metadata['image_base64']
                doc_info['image_base64_length'] = len(img_b64)
                doc_info['image_base64_preview'] = img_b64[:100]
                image_count += 1
                print(f"★ Element {idx}: Has direct image_base64 (length: {len(img_b64)})")
            
            debug_data['documents'].append(doc_info)
        
        print(f"★ Total elements with image_base64: {image_count}")
        
        # Save to JSON file
        debug_file = 'debug_api_response.json'
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2)
        print(f"★★★ Debug data saved to {debug_file} ★★★\n")
    
    def _manual_chunk_elements(self, elements):
        """Manually chunk elements to reduce count while preserving images"""
        # Don't chunk - just return all elements
        # Images need to stay separate to be processed correctly
        # We'll limit summarization calls instead
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
    
    def _partition_locally(self, file_path: str) -> List[Any]:
        """Process PDF locally (fallback)
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of extracted elements
        """
        from unstructured.partition.pdf import partition_pdf
        
        try:
            chunks = partition_pdf(
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
                print("⚠ WARNING: Tesseract OCR is not installed!")
                print("="*80)
                print("\nFalling back to text-only extraction (no images)...")
                print("To enable images, either:")
                print("  1. Install Tesseract: choco install tesseract")
                print("  2. Set UNSTRUCTURED_API_KEY to use cloud processing")
                print("="*80 + "\n")
                
                chunks = partition_pdf(
                    filename=file_path,
                    strategy="auto",
                )
            else:
                raise
        
        return chunks
    
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
    
    def _get_images_base64(self, chunks) -> List[str]:
        """Extract base64 encoded images from chunks"""
        images_b64 = []
        for chunk in chunks:
            # Check if this is an Image element by category
            if hasattr(chunk, 'metadata'):
                category = getattr(chunk.metadata, 'category', '')
                
                if 'Image' in category:
                    # This is an image element - check LangChain metadata for image data
                    if hasattr(chunk, '_langchain_metadata'):
                        img_data = chunk._langchain_metadata.get('image_base64')
                        if not img_data and hasattr(chunk, 'text'):
                            img_data = chunk.text
                        
                        if img_data and self._is_valid_base64_image(img_data) and img_data not in images_b64:
                            images_b64.append(img_data)
                            print(f"Found image (length: {len(img_data)} chars)")
            
            # Check orig_elements (now parsed as list of dicts from JSON)
            if hasattr(chunk, 'metadata') and hasattr(chunk.metadata, 'orig_elements'):
                orig_els = chunk.metadata.orig_elements
                if isinstance(orig_els, list):
                    for el in orig_els:
                        # Elements are now dicts from parsed JSON
                        if isinstance(el, dict):
                            el_type = el.get('type', '')
                            if el_type == 'Image':
                                # Check for image data in metadata
                                el_metadata = el.get('metadata', {})
                                img_data = el_metadata.get('image_base64') or el_metadata.get('image_path')
                                
                                # Sometimes base64 is in text field
                                if not img_data:
                                    img_data = el.get('text', '')
                                
                                # Validate it's actually base64 image data
                                if img_data and self._is_valid_base64_image(img_data) and img_data not in images_b64:
                                    images_b64.append(img_data)
                                    print(f"Found embedded image (length: {len(img_data)} chars)")
        
        print(f"Total images extracted: {len(images_b64)}")  
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

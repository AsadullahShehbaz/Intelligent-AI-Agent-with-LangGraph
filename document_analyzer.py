"""
Document Upload and Analysis System
"""
import os
import hashlib
from pathlib import Path
from typing import List, Dict
import PyPDF2
import docx
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool
from memory import qdrant_client, embedding_model, generate_point_id
from qdrant_client.models import PointStruct
import config


class DocumentAnalyzer:
    def __init__(self, upload_folder="uploads"):
        self.upload_folder = upload_folder
        self.collection_name = "documents"
        Path(upload_folder).mkdir(exist_ok=True)
        self.setup_document_collection()
    
    def setup_document_collection(self):
        """Create Qdrant collection for documents"""
        try:
            collections = qdrant_client.get_collections().collections
            exists = any(col.name == self.collection_name for col in collections)
            
            if not exists:
                from qdrant_client.models import VectorParams, Distance
                qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                print(f"✅ Created document collection: {self.collection_name}")
            
            # Create index for user_id (CRITICAL FIX)
            try:
                from qdrant_client.models import PayloadSchemaType
                qdrant_client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="user_id",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                print(f"✅ Created index for 'user_id' in {self.collection_name}")
            except Exception as idx_err:
                # Index might already exist
                if "already exists" not in str(idx_err).lower():
                    print(f"⚠️ Index creation warning: {idx_err}")
                    
            # Create index for document_id
            try:
                from qdrant_client.models import PayloadSchemaType
                qdrant_client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="document_id",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                print(f"✅ Created index for 'document_id' in {self.collection_name}")
            except Exception as idx_err:
                if "already exists" not in str(idx_err).lower():
                    print(f"⚠️ Index creation warning: {idx_err}")
                    
        except Exception as e:
            print(f"⚠️ Document collection setup error: {e}")
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from Word document"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise Exception(f"DOCX extraction failed: {str(e)}")
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            raise Exception(f"TXT extraction failed: {str(e)}")
    
    def extract_text(self, file_path: str) -> str:
        """Extract text based on file type"""
        extension = Path(file_path).suffix.lower()
        
        if extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif extension == '.docx':
            return self.extract_text_from_docx(file_path)
        elif extension == '.txt':
            return self.extract_text_from_txt(file_path)
        else:
            raise Exception(f"Unsupported file type: {extension}")
    
    def chunk_text(self, text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """Split text into chunks"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        return chunks
    
    def upload_document(self, file, user_id: str) -> Dict:
        """Process and store document"""
        try:
            # Save file
            file_hash = hashlib.md5(file.read()).hexdigest()
            file.seek(0)  # Reset file pointer
            
            filename = f"{user_id}_{file_hash}_{file.name}"
            file_path = os.path.join(self.upload_folder, filename)
            
            with open(file_path, 'wb') as f:
                f.write(file.read())
            
            # Extract text
            text = self.extract_text(file_path)
            
            if not text:
                return {"success": False, "error": "No text found in document"}
            
            # Chunk text
            chunks = self.chunk_text(text)
            
            # Store chunks in Qdrant
            points = []
            for idx, chunk in enumerate(chunks):
                embedding = embedding_model.embed_query(chunk)
                point_id = generate_point_id(file_hash, chunk, idx)
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "user_id": str(user_id),
                        "document_id": file_hash,
                        "filename": file.name,
                        "chunk_index": idx,
                        "text": chunk,
                        "total_chunks": len(chunks)
                    }
                )
                points.append(point)
            
            # Batch upload to Qdrant
            qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            return {
                "success": True,
                "document_id": file_hash,
                "filename": file.name,
                "chunks": len(chunks),
                "total_chars": len(text),
                "message": f"Document uploaded successfully! {len(chunks)} chunks indexed."
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def query_documents(self, user_id: str, question: str, document_id: str = None, limit: int = 5) -> List[Dict]:
        """Search documents for relevant information"""
        try:
            # Create query vector
            query_vector = embedding_model.embed_query(question)
            
            # Build filter
            filter_conditions = [{"key": "user_id", "match": {"value": str(user_id)}}]
            
            if document_id:
                filter_conditions.append({"key": "document_id", "match": {"value": document_id}})
            
            # Search Qdrant
            results = qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter={"must": filter_conditions}
            )
            
            # Format results
            contexts = []
            for result in results:
                contexts.append({
                    "text": result.payload.get("text", ""),
                    "filename": result.payload.get("filename", ""),
                    "chunk_index": result.payload.get("chunk_index", 0),
                    "score": result.score
                })
            
            return contexts
            
        except Exception as e:
            print(f"⚠️ Query error: {e}")
            return []
    
    def get_user_documents(self, user_id: str) -> List[Dict]:
        """Get all documents uploaded by user"""
        try:
            results, _ = qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter={"must": [{"key": "user_id", "match": {"value": str(user_id)}}]},
                limit=100,
                with_payload=["document_id", "filename", "total_chunks"]
            )
            
            # Deduplicate by document_id
            documents = {}
            for point in results:
                doc_id = point.payload.get("document_id")
                if doc_id not in documents:
                    documents[doc_id] = {
                        "document_id": doc_id,
                        "filename": point.payload.get("filename"),
                        "chunks": point.payload.get("total_chunks")
                    }
            
            return list(documents.values())
            
        except Exception as e:
            print(f"⚠️ Error fetching documents: {e}")
            return []
    
    def delete_document(self, user_id: str, document_id: str) -> Dict:
        """Delete a document and all its chunks"""
        try:
            # Find all points for this document
            results, _ = qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [
                        {"key": "user_id", "match": {"value": str(user_id)}},
                        {"key": "document_id", "match": {"value": document_id}}
                    ]
                },
                limit=1000,
                with_payload=False
            )
            
            point_ids = [point.id for point in results]
            
            if point_ids:
                qdrant_client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
            
            return {
                "success": True,
                "deleted_chunks": len(point_ids),
                "message": "Document deleted successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Initialize document analyzer
doc_analyzer = DocumentAnalyzer()


# ============ Tool: Ask Document ============
@tool
def ask_document(question: str, user_id: str, document_id: str = None) -> str:
    """
    Ask questions about uploaded documents.
    
    Args:
        question: The question to ask about the document(s)
        user_id: User ID (automatically provided)
        document_id: Optional specific document ID to search in
    
    Returns:
        Answer based on document content
    
    Examples:
        - "What is the main topic of my document?"
        - "Summarize the uploaded PDF"
        - "Find information about X in my documents"
    """
    try:
        # Get relevant document chunks
        contexts = doc_analyzer.query_documents(user_id, question, document_id, limit=5)
        
        if not contexts:
            return "No relevant information found in your documents. Make sure you've uploaded documents first."
        
        # Build context string
        context_text = "\n\n".join([
            f"[From {ctx['filename']}, chunk {ctx['chunk_index']}]:\n{ctx['text']}"
            for ctx in contexts
        ])
        
        # Return context for the LLM to use
        return f"Based on your documents:\n\n{context_text}\n\nAnswer to your question: {question}"
        
    except Exception as e:
        return f"Error querying documents: {str(e)}"
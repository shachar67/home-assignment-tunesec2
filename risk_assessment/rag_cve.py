"""
RAG (Retrieval Augmented Generation) for CVE Knowledge Base.
Uses vector database for semantic search of CVE information.
"""

import os
from typing import List, Dict, Optional
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.schema import Document

from .cve_client import CVEDatabaseClient


class CVEKnowledgeBase:
    """
    RAG-based CVE knowledge base using vector embeddings.
    
    Stores CVE data in a vector database for semantic search,
    enabling more accurate vulnerability detection.
    """
    
    def __init__(
        self,
        google_api_key: str,
        vector_db_dir: str = "./data/vectordb",
        embedding_model: str = "models/embedding-001"
    ):
        """
        Initialize CVE knowledge base.
        
        Args:
            google_api_key: Google API key for embeddings
            vector_db_dir: Directory to store vector database
            embedding_model: Google embedding model to use
        """
        self.google_api_key = google_api_key
        self.vector_db_dir = vector_db_dir
        self.embedding_model = embedding_model
        
        # Initialize embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=google_api_key
        )
        
        # Initialize or load vector store
        os.makedirs(vector_db_dir, exist_ok=True)
        
        try:
            self.vectorstore = Chroma(
                persist_directory=vector_db_dir,
                embedding_function=self.embeddings,
                collection_name="cve_knowledge"
            )
            print(f"✅ CVE Knowledge Base loaded from {vector_db_dir}")
        except Exception as e:
            print(f"⚠️  Error loading vector store: {e}")
            self.vectorstore = None
    
    def add_cves_to_knowledge_base(self, cves: List[Dict]) -> int:
        """
        Add CVEs to the knowledge base.
        
        Args:
            cves: List of CVE dictionaries
            
        Returns:
            Number of CVEs added
        """
        if not self.vectorstore:
            print("⚠️  Vector store not initialized")
            return 0
        
        documents = []
        for cve in cves:
            # Create document with CVE information
            content = f"""CVE ID: {cve.get('cve_id', 'Unknown')}
Severity: {cve.get('severity', 'unknown')}
Description: {cve.get('description', '')}
Published: {cve.get('published_date', 'Unknown')}"""
            
            doc = Document(
                page_content=content,
                metadata={
                    "cve_id": cve.get("cve_id", "Unknown"),
                    "severity": cve.get("severity", "unknown"),
                    "published_date": cve.get("published_date", ""),
                    "source_url": cve.get("source_url", "")
                }
            )
            documents.append(doc)
        
        if documents:
            self.vectorstore.add_documents(documents)
            print(f"✅ Added {len(documents)} CVEs to knowledge base")
            return len(documents)
        
        return 0
    
    def search_relevant_cves(
        self,
        software_name: str,
        k: int = 10
    ) -> List[Dict]:
        """
        Search for CVEs relevant to software using semantic search.
        
        Args:
            software_name: Name of the software
            k: Number of results to return
            
        Returns:
            List of relevant CVE dictionaries
        """
        if not self.vectorstore:
            print("⚠️  Vector store not initialized")
            return []
        
        try:
            # Semantic search for relevant CVEs
            query = f"vulnerabilities security issues in {software_name}"
            results = self.vectorstore.similarity_search(
                query,
                k=k
            )
            
            # Convert back to dictionary format
            cves = []
            for doc in results:
                cves.append({
                    "cve_id": doc.metadata.get("cve_id"),
                    "severity": doc.metadata.get("severity"),
                    "description": doc.page_content,
                    "published_date": doc.metadata.get("published_date"),
                    "source_url": doc.metadata.get("source_url")
                })
            
            return cves
            
        except Exception as e:
            print(f"⚠️  Error searching CVEs: {e}")
            return []
    
    def build_knowledge_base_from_nvd(
        self,
        software_names: List[str],
        days_back: int = 730
    ) -> int:
        """
        Build knowledge base by fetching CVEs from NVD for multiple software.
        
        Args:
            software_names: List of software names to fetch CVEs for
            days_back: Number of days to look back
            
        Returns:
            Total number of CVEs added
        """
        cve_client = CVEDatabaseClient()
        total_added = 0
        
        for software in software_names:
            print(f"Fetching CVEs for {software}...")
            result = cve_client.search_cves(software, days_back=days_back)
            
            if result.get("cves"):
                added = self.add_cves_to_knowledge_base(result["cves"])
                total_added += added
        
        print(f"✅ Built knowledge base with {total_added} total CVEs")
        return total_added
    
    def get_statistics(self) -> Dict:
        """Get statistics about the knowledge base."""
        if not self.vectorstore:
            return {"status": "not initialized"}
        
        try:
            collection = self.vectorstore._collection
            count = collection.count()
            
            return {
                "status": "active",
                "total_cves": count,
                "vector_db_dir": self.vector_db_dir,
                "embedding_model": self.embedding_model
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# Helper function to initialize knowledge base
def initialize_cve_knowledge_base(
    google_api_key: str,
    vector_db_dir: str = "./data/vectordb",
    common_software: Optional[List[str]] = None
) -> CVEKnowledgeBase:
    """
    Initialize and optionally populate CVE knowledge base.
    
    Args:
        google_api_key: Google API key
        vector_db_dir: Directory for vector database
        common_software: List of common software to pre-populate
        
    Returns:
        Initialized CVEKnowledgeBase
    """
    kb = CVEKnowledgeBase(
        google_api_key=google_api_key,
        vector_db_dir=vector_db_dir
    )
    
    # Optionally pre-populate with common software
    if common_software:
        print("Building knowledge base...")
        kb.build_knowledge_base_from_nvd(common_software)
    
    return kb


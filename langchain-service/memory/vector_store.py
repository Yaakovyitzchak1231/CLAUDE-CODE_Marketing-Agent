"""
Vector Store Manager
Manages Chroma vector database for embeddings and semantic search
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import structlog

from config import settings, get_chroma_url


logger = structlog.get_logger()


class VectorStoreManager:
    """
    Manages vector storage and retrieval using Chroma

    Collections:
    - user_profiles: User and audience embeddings
    - content_library: Historical content for RAG
    - market_segments: Audience segment embeddings
    - competitor_content: Competitor content for analysis
    """

    def __init__(self):
        """Initialize Chroma client and embedding model"""

        # Initialize Chroma client
        self.client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            settings=Settings(
                anonymized_telemetry=False
            )
        )

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)

        # Collection references
        self.collections = {}

        logger.info("vector_store_initialized", host=settings.CHROMA_HOST)

    def get_collection(self, name: str):
        """
        Get or create collection

        Args:
            name: Collection name

        Returns:
            Collection object
        """
        if name not in self.collections:
            try:
                self.collections[name] = self.client.get_collection(name=name)
                logger.info("collection_retrieved", name=name)
            except Exception:
                self.collections[name] = self.client.create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("collection_created", name=name)

        return self.collections[name]

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ):
        """
        Add documents to collection

        Args:
            collection_name: Target collection
            documents: List of text documents
            metadatas: Optional metadata for each document
            ids: Optional custom IDs (auto-generated if None)
        """
        collection = self.get_collection(collection_name)

        # Generate embeddings
        embeddings = self.embedding_model.encode(documents).tolist()

        # Generate IDs if not provided
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]

        # Add to collection
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas or [{} for _ in documents],
            ids=ids
        )

        logger.info(
            "documents_added",
            collection=collection_name,
            count=len(documents)
        )

    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Search collection with semantic similarity

        Args:
            collection_name: Collection to search
            query: Search query text
            n_results: Number of results to return
            where: Optional metadata filters

        Returns:
            List of results with documents and metadata
        """
        collection = self.get_collection(collection_name)

        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0].tolist()

        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )

        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "id": results['ids'][0][i],
                "document": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i]
            })

        logger.info(
            "search_completed",
            collection=collection_name,
            query=query[:50],
            results=len(formatted_results)
        )

        return formatted_results

    def update_document(
        self,
        collection_name: str,
        document_id: str,
        document: str,
        metadata: Optional[Dict] = None
    ):
        """
        Update existing document

        Args:
            collection_name: Target collection
            document_id: ID of document to update
            document: New document text
            metadata: New metadata
        """
        collection = self.get_collection(collection_name)

        # Generate new embedding
        embedding = self.embedding_model.encode([document])[0].tolist()

        # Update
        collection.update(
            ids=[document_id],
            documents=[document],
            embeddings=[embedding],
            metadatas=[metadata or {}]
        )

        logger.info(
            "document_updated",
            collection=collection_name,
            id=document_id
        )

    def delete_document(self, collection_name: str, document_id: str):
        """
        Delete document from collection

        Args:
            collection_name: Target collection
            document_id: ID of document to delete
        """
        collection = self.get_collection(collection_name)
        collection.delete(ids=[document_id])

        logger.info(
            "document_deleted",
            collection=collection_name,
            id=document_id
        )

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get collection statistics

        Args:
            collection_name: Collection name

        Returns:
            Dict with collection stats
        """
        collection = self.get_collection(collection_name)
        count = collection.count()

        return {
            "name": collection_name,
            "count": count,
            "metadata": collection.metadata
        }

    # ==================== SPECIALIZED METHODS ====================

    def add_user_profile(
        self,
        user_id: str,
        profile_text: str,
        metadata: Dict
    ):
        """Add user/audience profile"""
        self.add_documents(
            collection_name="user_profiles",
            documents=[profile_text],
            metadatas=[metadata],
            ids=[f"user_{user_id}"]
        )

    def add_content_to_library(
        self,
        content_id: str,
        content: str,
        metadata: Dict
    ):
        """Add content to library for RAG"""
        self.add_documents(
            collection_name="content_library",
            documents=[content],
            metadatas=[metadata],
            ids=[f"content_{content_id}"]
        )

    def search_similar_content(
        self,
        query: str,
        content_type: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict]:
        """Search for similar content"""
        where = {"type": content_type} if content_type else None

        return self.search(
            collection_name="content_library",
            query=query,
            n_results=n_results,
            where=where
        )

    def add_competitor_content(
        self,
        competitor: str,
        content: str,
        metadata: Dict
    ):
        """Add competitor content"""
        import uuid
        self.add_documents(
            collection_name="competitor_content",
            documents=[content],
            metadatas=[{**metadata, "competitor": competitor}],
            ids=[f"competitor_{uuid.uuid4()}"]
        )

    def search_competitor_content(
        self,
        query: str,
        competitor: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict]:
        """Search competitor content"""
        where = {"competitor": competitor} if competitor else None

        return self.search(
            collection_name="competitor_content",
            query=query,
            n_results=n_results,
            where=where
        )

    def add_market_segment(
        self,
        segment_id: str,
        description: str,
        metadata: Dict
    ):
        """Add market segment"""
        self.add_documents(
            collection_name="market_segments",
            documents=[description],
            metadatas=[metadata],
            ids=[f"segment_{segment_id}"]
        )

    def find_relevant_segments(
        self,
        audience_description: str,
        n_results: int = 3
    ) -> List[Dict]:
        """Find relevant market segments for audience"""
        return self.search(
            collection_name="market_segments",
            query=audience_description,
            n_results=n_results
        )


# Global instance
_vector_store = None


def get_vector_store() -> VectorStoreManager:
    """Get singleton vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager()
    return _vector_store

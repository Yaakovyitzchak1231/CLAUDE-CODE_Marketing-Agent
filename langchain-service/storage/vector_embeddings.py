"""
Vector Embedding Pipelines
Creates and stores embeddings in Chroma vector database
"""

from langchain.embeddings import HuggingFaceEmbeddings, OllamaEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter
)
from typing import List, Dict, Any, Optional
import structlog
import os
from datetime import datetime

logger = structlog.get_logger()


class VectorEmbeddingPipeline:
    """
    Vector embedding pipeline for semantic search and RAG

    Features:
    - Multiple embedding models (HuggingFace, Ollama)
    - Text chunking strategies
    - Chroma vector store integration
    - Multiple collections for different content types
    """

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        chroma_host: str = "chroma",
        chroma_port: int = 8000,
        use_ollama: bool = False
    ):
        """
        Initialize embedding pipeline

        Args:
            embedding_model: HuggingFace model name or Ollama model
            chroma_host: Chroma server host
            chroma_port: Chroma server port
            use_ollama: Use Ollama embeddings instead of HuggingFace
        """
        self.embedding_model_name = embedding_model
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.use_ollama = use_ollama

        # Initialize embeddings
        if use_ollama:
            self.embeddings = OllamaEmbeddings(
                model=embedding_model,
                base_url=f"http://{os.getenv('OLLAMA_HOST', 'ollama')}:11434"
            )
        else:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': 'cpu'},  # Change to 'cuda' if GPU available
                encode_kwargs={'normalize_embeddings': True}
            )

        # Text splitters
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        self.token_splitter = TokenTextSplitter(
            chunk_size=512,
            chunk_overlap=50
        )

        # Collection references
        self._collections = {}

        logger.info(
            "vector_pipeline_initialized",
            embedding_model=embedding_model,
            use_ollama=use_ollama
        )

    def get_collection(self, collection_name: str) -> Chroma:
        """
        Get or create Chroma collection

        Args:
            collection_name: Name of the collection

        Returns:
            Chroma vector store instance
        """
        if collection_name not in self._collections:
            logger.info("creating_collection", collection_name=collection_name)

            self._collections[collection_name] = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                client_settings={
                    "chroma_server_host": self.chroma_host,
                    "chroma_server_http_port": self.chroma_port
                }
            )

        return self._collections[collection_name]

    def add_texts(
        self,
        texts: List[str],
        collection_name: str,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        chunk_strategy: str = "recursive"
    ) -> List[str]:
        """
        Add texts to vector store with chunking

        Args:
            texts: List of texts to add
            collection_name: Collection name
            metadatas: Optional metadata for each text
            chunk_strategy: Chunking strategy (recursive, token, none)

        Returns:
            List of document IDs
        """
        try:
            # Chunk texts
            if chunk_strategy == "recursive":
                documents = self._chunk_texts_recursive(texts, metadatas)
            elif chunk_strategy == "token":
                documents = self._chunk_texts_token(texts, metadatas)
            else:
                documents = [
                    Document(page_content=text, metadata=meta or {})
                    for text, meta in zip(texts, metadatas or [{}] * len(texts))
                ]

            # Get collection
            collection = self.get_collection(collection_name)

            # Add documents
            ids = collection.add_documents(documents)

            logger.info(
                "texts_added_to_collection",
                collection_name=collection_name,
                document_count=len(documents),
                chunk_strategy=chunk_strategy
            )

            return ids

        except Exception as e:
            logger.error(
                "add_texts_error",
                collection_name=collection_name,
                error=str(e)
            )
            raise

    def _chunk_texts_recursive(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[Document]:
        """Chunk texts using recursive character splitter"""
        documents = []

        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}

            # Split text
            chunks = self.recursive_splitter.split_text(text)

            # Create documents
            for chunk_idx, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = chunk_idx
                chunk_metadata['total_chunks'] = len(chunks)

                documents.append(
                    Document(page_content=chunk, metadata=chunk_metadata)
                )

        return documents

    def _chunk_texts_token(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[Document]:
        """Chunk texts using token-based splitter"""
        documents = []

        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}

            # Split text
            chunks = self.token_splitter.split_text(text)

            # Create documents
            for chunk_idx, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = chunk_idx
                chunk_metadata['total_chunks'] = len(chunks)

                documents.append(
                    Document(page_content=chunk, metadata=chunk_metadata)
                )

        return documents

    def search_similar(
        self,
        query: str,
        collection_name: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents

        Args:
            query: Search query
            collection_name: Collection to search
            k: Number of results to return
            filter_dict: Optional metadata filter

        Returns:
            List of similar documents with scores
        """
        try:
            collection = self.get_collection(collection_name)

            # Perform similarity search
            results = collection.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter_dict
            )

            # Format results
            formatted_results = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                }
                for doc, score in results
            ]

            logger.info(
                "similarity_search_completed",
                collection_name=collection_name,
                query_length=len(query),
                results_count=len(formatted_results)
            )

            return formatted_results

        except Exception as e:
            logger.error(
                "similarity_search_error",
                collection_name=collection_name,
                error=str(e)
            )
            return []

    def delete_documents(
        self,
        collection_name: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Delete documents from collection

        Args:
            collection_name: Collection name
            filter_dict: Delete by metadata filter
            ids: Delete by document IDs

        Returns:
            Success status
        """
        try:
            collection = self.get_collection(collection_name)

            if ids:
                collection.delete(ids=ids)
            elif filter_dict:
                collection.delete(where=filter_dict)
            else:
                logger.warning("delete_documents_no_criteria")
                return False

            logger.info(
                "documents_deleted",
                collection_name=collection_name,
                filter=filter_dict,
                ids_count=len(ids) if ids else 0
            )

            return True

        except Exception as e:
            logger.error(
                "delete_documents_error",
                collection_name=collection_name,
                error=str(e)
            )
            return False


# === Specialized Pipelines ===

class ContentLibraryPipeline:
    """
    Pipeline for storing historical content in vector store

    Use for RAG when generating new content
    """

    def __init__(self, embedding_pipeline: VectorEmbeddingPipeline):
        self.pipeline = embedding_pipeline
        self.collection_name = "content_library"

    def add_content(
        self,
        content: str,
        content_type: str,
        campaign_id: Optional[int] = None,
        performance_metrics: Optional[Dict[str, float]] = None
    ) -> List[str]:
        """
        Add content to library

        Args:
            content: Content text
            content_type: Type of content (blog_post, email, social, etc.)
            campaign_id: Optional campaign ID
            performance_metrics: Optional performance data (clicks, conversions, etc.)

        Returns:
            Document IDs
        """
        metadata = {
            "content_type": content_type,
            "added_at": datetime.now().isoformat(),
            "campaign_id": campaign_id
        }

        if performance_metrics:
            metadata["performance"] = performance_metrics

        return self.pipeline.add_texts(
            texts=[content],
            collection_name=self.collection_name,
            metadatas=[metadata],
            chunk_strategy="recursive"
        )

    def find_similar_content(
        self,
        query: str,
        content_type: Optional[str] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar content for reference

        Args:
            query: Search query or content description
            content_type: Optional content type filter
            k: Number of results

        Returns:
            Similar content with metadata
        """
        filter_dict = {"content_type": content_type} if content_type else None

        return self.pipeline.search_similar(
            query=query,
            collection_name=self.collection_name,
            k=k,
            filter_dict=filter_dict
        )


class CompetitorContentPipeline:
    """
    Pipeline for storing competitor content

    Use for competitive analysis and trend detection
    """

    def __init__(self, embedding_pipeline: VectorEmbeddingPipeline):
        self.pipeline = embedding_pipeline
        self.collection_name = "competitor_content"

    def add_competitor_content(
        self,
        content: str,
        competitor_id: int,
        url: str,
        content_type: str
    ) -> List[str]:
        """
        Add competitor content

        Args:
            content: Content text
            competitor_id: Competitor database ID
            url: Source URL
            content_type: Type of content

        Returns:
            Document IDs
        """
        metadata = {
            "competitor_id": competitor_id,
            "url": url,
            "content_type": content_type,
            "scraped_at": datetime.now().isoformat()
        }

        return self.pipeline.add_texts(
            texts=[content],
            collection_name=self.collection_name,
            metadatas=[metadata],
            chunk_strategy="recursive"
        )

    def find_similar_competitor_content(
        self,
        query: str,
        competitor_id: Optional[int] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar competitor content

        Args:
            query: Search query
            competitor_id: Optional competitor filter
            k: Number of results

        Returns:
            Similar competitor content
        """
        filter_dict = {"competitor_id": competitor_id} if competitor_id else None

        return self.pipeline.search_similar(
            query=query,
            collection_name=self.collection_name,
            k=k,
            filter_dict=filter_dict
        )


class UserProfilePipeline:
    """
    Pipeline for storing user/audience profiles

    Use for personalization and targeting
    """

    def __init__(self, embedding_pipeline: VectorEmbeddingPipeline):
        self.pipeline = embedding_pipeline
        self.collection_name = "user_profiles"

    def add_user_profile(
        self,
        user_id: int,
        profile_text: str,
        segment: str,
        interests: List[str]
    ) -> List[str]:
        """
        Add user profile

        Args:
            user_id: User database ID
            profile_text: Profile description
            segment: Market segment
            interests: List of interests

        Returns:
            Document IDs
        """
        metadata = {
            "user_id": user_id,
            "segment": segment,
            "interests": interests,
            "created_at": datetime.now().isoformat()
        }

        return self.pipeline.add_texts(
            texts=[profile_text],
            collection_name=self.collection_name,
            metadatas=[metadata],
            chunk_strategy="none"
        )

    def find_similar_profiles(
        self,
        query: str,
        segment: Optional[str] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar user profiles

        Args:
            query: Search query or profile description
            segment: Optional segment filter
            k: Number of results

        Returns:
            Similar user profiles
        """
        filter_dict = {"segment": segment} if segment else None

        return self.pipeline.search_similar(
            query=query,
            collection_name=self.collection_name,
            k=k,
            filter_dict=filter_dict
        )


class MarketSegmentPipeline:
    """
    Pipeline for storing market segment embeddings

    Use for audience analysis and targeting
    """

    def __init__(self, embedding_pipeline: VectorEmbeddingPipeline):
        self.pipeline = embedding_pipeline
        self.collection_name = "market_segments"

    def add_segment(
        self,
        segment_name: str,
        description: str,
        characteristics: Dict[str, Any],
        campaign_id: Optional[int] = None
    ) -> List[str]:
        """
        Add market segment

        Args:
            segment_name: Segment name
            description: Segment description
            characteristics: Segment characteristics
            campaign_id: Optional campaign ID

        Returns:
            Document IDs
        """
        metadata = {
            "segment_name": segment_name,
            "characteristics": characteristics,
            "campaign_id": campaign_id,
            "created_at": datetime.now().isoformat()
        }

        return self.pipeline.add_texts(
            texts=[description],
            collection_name=self.collection_name,
            metadatas=[metadata],
            chunk_strategy="none"
        )

    def find_relevant_segments(
        self,
        query: str,
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find relevant market segments

        Args:
            query: Search query or audience description
            k: Number of results

        Returns:
            Relevant market segments
        """
        return self.pipeline.search_similar(
            query=query,
            collection_name=self.collection_name,
            k=k
        )


# === Factory Functions ===

def create_embedding_pipeline(
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    use_ollama: bool = False
) -> VectorEmbeddingPipeline:
    """Create vector embedding pipeline"""
    return VectorEmbeddingPipeline(
        embedding_model=embedding_model,
        use_ollama=use_ollama
    )


def create_content_library_pipeline() -> ContentLibraryPipeline:
    """Create content library pipeline"""
    base_pipeline = create_embedding_pipeline()
    return ContentLibraryPipeline(base_pipeline)


def create_competitor_pipeline() -> CompetitorContentPipeline:
    """Create competitor content pipeline"""
    base_pipeline = create_embedding_pipeline()
    return CompetitorContentPipeline(base_pipeline)


def create_user_profile_pipeline() -> UserProfilePipeline:
    """Create user profile pipeline"""
    base_pipeline = create_embedding_pipeline()
    return UserProfilePipeline(base_pipeline)


def create_market_segment_pipeline() -> MarketSegmentPipeline:
    """Create market segment pipeline"""
    base_pipeline = create_embedding_pipeline()
    return MarketSegmentPipeline(base_pipeline)

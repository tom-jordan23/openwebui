"""
Embedding Service
Handles text embedding generation using various models including sentence transformers and OpenAI
"""

import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding generation"""
    text: str
    embedding: List[float]
    model: str
    dimension: int
    processing_time_ms: float


class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2", 
                 batch_size: int = 32, device: str = "cpu"):
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device
        self.model = None
        self.dimension = None
        
        # Initialize the appropriate model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model"""
        try:
            if self.model_name.startswith("text-embedding") and OPENAI_AVAILABLE:
                # OpenAI embedding model
                self.model_type = "openai"
                # OpenAI client will be initialized per request
                self.dimension = 1536  # Default for text-embedding-ada-002
                logger.info(f"Initialized OpenAI embedding model: {self.model_name}")
                
            elif SENTENCE_TRANSFORMERS_AVAILABLE:
                # Sentence transformer model
                self.model_type = "sentence_transformers"
                self.model = SentenceTransformer(self.model_name, device=self.device)
                self.dimension = self.model.get_sentence_embedding_dimension()
                logger.info(f"Initialized SentenceTransformer: {self.model_name} (dim={self.dimension})")
                
            else:
                # Fallback to simple TF-IDF or random embeddings
                self.model_type = "fallback"
                self.dimension = 768  # Standard dimension
                logger.warning("No embedding libraries available, using fallback implementation")
                
        except Exception as e:
            logger.error(f"Error initializing embedding model: {e}")
            self.model_type = "fallback"
            self.dimension = 768
    
    async def embed_text(self, text: str) -> EmbeddingResult:
        """Generate embedding for a single text"""
        results = await self.embed_texts([text])
        return results[0] if results else None
    
    async def embed_texts(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        start_time = time.time()
        
        try:
            if self.model_type == "openai":
                embeddings = await self._embed_with_openai(texts)
            elif self.model_type == "sentence_transformers":
                embeddings = await self._embed_with_sentence_transformers(texts)
            else:
                embeddings = await self._embed_with_fallback(texts)
            
            processing_time = (time.time() - start_time) * 1000
            
            # Create results
            results = []
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                result = EmbeddingResult(
                    text=text,
                    embedding=embedding,
                    model=self.model_name,
                    dimension=len(embedding),
                    processing_time_ms=processing_time / len(texts)  # Average per text
                )
                results.append(result)
            
            logger.info(f"Generated {len(results)} embeddings in {processing_time:.2f}ms")
            return results
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    async def _embed_with_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        try:
            # Process in batches to avoid API limits
            all_embeddings = []
            
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                
                # Clean texts for OpenAI API
                clean_batch = [text.replace("\n", " ").strip() for text in batch]
                
                # Call OpenAI API
                response = await openai.Embedding.acreate(
                    input=clean_batch,
                    model=self.model_name
                )
                
                # Extract embeddings
                batch_embeddings = [item['embedding'] for item in response['data']]
                all_embeddings.extend(batch_embeddings)
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error with OpenAI embeddings: {e}")
            # Fallback to sentence transformers or fallback method
            return await self._embed_with_fallback(texts)
    
    async def _embed_with_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence transformers"""
        try:
            # Process in batches
            all_embeddings = []
            
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                
                # Generate embeddings
                batch_embeddings = self.model.encode(
                    batch,
                    convert_to_numpy=True,
                    show_progress_bar=False
                )
                
                # Convert to list format
                for embedding in batch_embeddings:
                    all_embeddings.append(embedding.tolist())
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error with sentence transformers: {e}")
            return await self._embed_with_fallback(texts)
    
    async def _embed_with_fallback(self, texts: List[str]) -> List[List[float]]:
        """Simple fallback embedding method using text characteristics"""
        embeddings = []
        
        for text in texts:
            # Create a simple embedding based on text characteristics
            # This is a very basic implementation for fallback purposes
            text_lower = text.lower()
            
            # Basic features: length, word count, character frequencies
            features = [
                len(text) / 1000.0,  # Normalized length
                len(text.split()) / 100.0,  # Normalized word count
                text_lower.count('a') / len(text) if len(text) > 0 else 0,
                text_lower.count('e') / len(text) if len(text) > 0 else 0,
                text_lower.count('i') / len(text) if len(text) > 0 else 0,
                text_lower.count('o') / len(text) if len(text) > 0 else 0,
                text_lower.count('u') / len(text) if len(text) > 0 else 0,
            ]
            
            # Pad or truncate to desired dimension
            while len(features) < self.dimension:
                features.append(np.random.normal(0, 0.1))  # Add some random noise
            
            embeddings.append(features[:self.dimension])
        
        return embeddings
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def find_similar_embeddings(self, query_embedding: List[float], 
                              candidate_embeddings: List[List[float]], 
                              threshold: float = 0.7, 
                              top_k: int = 10) -> List[Tuple[int, float]]:
        """Find the most similar embeddings to a query"""
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            similarity = self.calculate_similarity(query_embedding, candidate)
            if similarity >= threshold:
                similarities.append((i, similarity))
        
        # Sort by similarity (descending) and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    async def update_model(self, new_model_name: str):
        """Update the embedding model"""
        old_model = self.model_name
        self.model_name = new_model_name
        self.model = None
        
        try:
            self._initialize_model()
            logger.info(f"Successfully updated embedding model from {old_model} to {new_model_name}")
        except Exception as e:
            # Rollback on failure
            self.model_name = old_model
            self._initialize_model()
            logger.error(f"Failed to update embedding model: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            'model_name': self.model_name,
            'model_type': self.model_type,
            'dimension': self.dimension,
            'batch_size': self.batch_size,
            'device': self.device,
            'available_libraries': {
                'sentence_transformers': SENTENCE_TRANSFORMERS_AVAILABLE,
                'openai': OPENAI_AVAILABLE
            }
        }


# Global embedding service instance
_embedding_service = None

def get_embedding_service(model_name: str = None, **kwargs) -> EmbeddingService:
    """Get or create global embedding service instance"""
    global _embedding_service
    
    if _embedding_service is None or (model_name and model_name != _embedding_service.model_name):
        _embedding_service = EmbeddingService(model_name or "sentence-transformers/all-mpnet-base-v2", **kwargs)
    
    return _embedding_service
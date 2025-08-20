"""
Document Chunking Service
Handles intelligent document chunking with various strategies including semantic, fixed-size, and sentence-based chunking
"""

import logging
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from transformers import AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from .models import DocumentChunk

logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Available chunking strategies"""
    FIXED_SIZE = "fixed"
    SEMANTIC = "semantic"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SLIDING_WINDOW = "sliding"


@dataclass
class ChunkingConfig:
    """Configuration for document chunking"""
    strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC
    chunk_size: int = 512  # Characters or tokens
    chunk_overlap: int = 50  # Characters or tokens
    min_chunk_size: int = 50  # Minimum chunk size
    max_chunk_size: int = 2000  # Maximum chunk size
    preserve_sentences: bool = True
    preserve_paragraphs: bool = True
    use_tokens: bool = False  # Use token count instead of character count
    tokenizer_model: str = "gpt2"  # Tokenizer for token-based chunking


class DocumentChunker:
    """Service for intelligent document chunking"""
    
    def __init__(self, config: ChunkingConfig = None):
        self.config = config or ChunkingConfig()
        
        # Initialize NLP models if available
        self.nlp = None
        self.tokenizer = None
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize NLP models for advanced chunking"""
        try:
            # Load spaCy model for sentence and semantic chunking
            if SPACY_AVAILABLE and self.config.strategy in [ChunkingStrategy.SEMANTIC, ChunkingStrategy.SENTENCE]:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                    logger.info("Loaded spaCy model for advanced chunking")
                except OSError:
                    logger.warning("spaCy en_core_web_sm model not found, using fallback")
                    
            # Load tokenizer for token-based chunking
            if TRANSFORMERS_AVAILABLE and self.config.use_tokens:
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained(self.config.tokenizer_model)
                    logger.info(f"Loaded tokenizer: {self.config.tokenizer_model}")
                except Exception as e:
                    logger.warning(f"Failed to load tokenizer: {e}")
                    
        except Exception as e:
            logger.error(f"Error initializing chunking models: {e}")
    
    def chunk_text(self, text: str, source_id: int) -> List[DocumentChunk]:
        """Chunk text using the configured strategy"""
        if not text or not text.strip():
            return []
        
        start_time = time.time()
        
        try:
            # Choose chunking method based on strategy
            if self.config.strategy == ChunkingStrategy.SEMANTIC:
                chunks = self._chunk_semantic(text, source_id)
            elif self.config.strategy == ChunkingStrategy.SENTENCE:
                chunks = self._chunk_by_sentences(text, source_id)
            elif self.config.strategy == ChunkingStrategy.PARAGRAPH:
                chunks = self._chunk_by_paragraphs(text, source_id)
            elif self.config.strategy == ChunkingStrategy.SLIDING_WINDOW:
                chunks = self._chunk_sliding_window(text, source_id)
            else:  # Fixed size
                chunks = self._chunk_fixed_size(text, source_id)
            
            # Post-process chunks
            chunks = self._post_process_chunks(chunks, text)
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"Chunked text into {len(chunks)} chunks in {processing_time:.2f}ms")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            # Fallback to fixed-size chunking
            return self._chunk_fixed_size(text, source_id)
    
    def _chunk_semantic(self, text: str, source_id: int) -> List[DocumentChunk]:
        """Chunk text using semantic boundaries"""
        if not self.nlp:
            # Fallback to sentence chunking
            return self._chunk_by_sentences(text, source_id)
        
        chunks = []
        doc = self.nlp(text)
        
        current_chunk = ""
        current_start = 0
        chunk_sentences = []
        
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if not sent_text:
                continue
            
            # Check if adding this sentence would exceed chunk size
            potential_chunk = current_chunk + (" " if current_chunk else "") + sent_text
            chunk_size = self._get_text_size(potential_chunk)
            
            if chunk_size <= self.config.chunk_size or not current_chunk:
                current_chunk = potential_chunk
                chunk_sentences.append(sent)
            else:
                # Create chunk from current content
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk, source_id, len(chunks), current_start
                    )
                    chunks.append(chunk)
                
                # Start new chunk with current sentence
                current_chunk = sent_text
                current_start = sent.start_char
                chunk_sentences = [sent]
        
        # Add final chunk
        if current_chunk:
            chunk = self._create_chunk(
                current_chunk, source_id, len(chunks), current_start
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_by_sentences(self, text: str, source_id: int) -> List[DocumentChunk]:
        """Chunk text by sentences"""
        if self.nlp:
            doc = self.nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        else:
            # Fallback regex-based sentence splitting
            sentence_pattern = r'(?<=[.!?])\s+'
            sentences = [s.strip() for s in re.split(sentence_pattern, text) if s.strip()]
        
        return self._group_sentences_into_chunks(sentences, source_id, text)
    
    def _chunk_by_paragraphs(self, text: str, source_id: int) -> List[DocumentChunk]:
        """Chunk text by paragraphs"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        current_start = 0
        
        for para in paragraphs:
            potential_chunk = current_chunk + ("\n\n" if current_chunk else "") + para
            chunk_size = self._get_text_size(potential_chunk)
            
            if chunk_size <= self.config.chunk_size or not current_chunk:
                current_chunk = potential_chunk
            else:
                # Create chunk from current content
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk, source_id, len(chunks), current_start
                    )
                    chunks.append(chunk)
                
                # Start new chunk
                current_chunk = para
                current_start = text.find(para, current_start)
        
        # Add final chunk
        if current_chunk:
            chunk = self._create_chunk(
                current_chunk, source_id, len(chunks), current_start
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_sliding_window(self, text: str, source_id: int) -> List[DocumentChunk]:
        """Chunk text using sliding window approach"""
        chunks = []
        step_size = self.config.chunk_size - self.config.chunk_overlap
        
        for i in range(0, len(text), step_size):
            chunk_text = text[i:i + self.config.chunk_size]
            
            # Try to end at sentence boundary if preserve_sentences is True
            if self.config.preserve_sentences and i + self.config.chunk_size < len(text):
                last_period = chunk_text.rfind('.')
                last_question = chunk_text.rfind('?')
                last_exclamation = chunk_text.rfind('!')
                
                sentence_end = max(last_period, last_question, last_exclamation)
                if sentence_end > len(chunk_text) * 0.8:  # Only if we don't lose too much
                    chunk_text = chunk_text[:sentence_end + 1]
            
            if chunk_text.strip():
                chunk = self._create_chunk(chunk_text.strip(), source_id, len(chunks), i)
                chunks.append(chunk)
        
        return chunks
    
    def _chunk_fixed_size(self, text: str, source_id: int) -> List[DocumentChunk]:
        """Chunk text using fixed size strategy"""
        chunks = []
        
        for i in range(0, len(text), self.config.chunk_size - self.config.chunk_overlap):
            chunk_text = text[i:i + self.config.chunk_size]
            
            if chunk_text.strip():
                chunk = self._create_chunk(chunk_text.strip(), source_id, len(chunks), i)
                chunks.append(chunk)
        
        return chunks
    
    def _group_sentences_into_chunks(self, sentences: List[str], source_id: int, full_text: str) -> List[DocumentChunk]:
        """Group sentences into appropriately sized chunks"""
        chunks = []
        current_chunk = ""
        current_start = 0
        
        for sentence in sentences:
            potential_chunk = current_chunk + (" " if current_chunk else "") + sentence
            chunk_size = self._get_text_size(potential_chunk)
            
            if chunk_size <= self.config.chunk_size or not current_chunk:
                current_chunk = potential_chunk
            else:
                # Create chunk from current content
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk, source_id, len(chunks), current_start
                    )
                    chunks.append(chunk)
                
                # Start new chunk with current sentence
                current_chunk = sentence
                current_start = full_text.find(sentence, current_start) if current_start < len(full_text) else 0
        
        # Add final chunk
        if current_chunk:
            chunk = self._create_chunk(
                current_chunk, source_id, len(chunks), current_start
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, content: str, source_id: int, chunk_index: int, start_position: int) -> DocumentChunk:
        """Create a DocumentChunk object"""
        chunk = DocumentChunk(
            source_id=source_id,
            chunk_index=chunk_index,
            content=content,
            start_position=start_position,
            end_position=start_position + len(content),
            character_count=len(content)
        )
        
        # Add token count if tokenizer is available
        if self.tokenizer:
            try:
                tokens = self.tokenizer.encode(content)
                chunk.token_count = len(tokens)
            except Exception as e:
                logger.warning(f"Error counting tokens: {e}")
        
        return chunk
    
    def _get_text_size(self, text: str) -> int:
        """Get text size based on configuration (characters or tokens)"""
        if self.config.use_tokens and self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        
        return len(text)
    
    def _post_process_chunks(self, chunks: List[DocumentChunk], original_text: str) -> List[DocumentChunk]:
        """Post-process chunks to improve quality"""
        processed_chunks = []
        
        for chunk in chunks:
            # Skip chunks that are too small
            if len(chunk.content) < self.config.min_chunk_size:
                continue
            
            # Truncate chunks that are too large
            if len(chunk.content) > self.config.max_chunk_size:
                chunk.content = chunk.content[:self.config.max_chunk_size]
                chunk.end_position = chunk.start_position + len(chunk.content)
                chunk.character_count = len(chunk.content)
            
            # Add quality scores
            chunk.coherence_score = self._calculate_coherence_score(chunk.content)
            chunk.completeness_score = self._calculate_completeness_score(chunk.content)
            chunk.relevance_score = self._calculate_relevance_score(chunk.content, original_text)
            
            processed_chunks.append(chunk)
        
        return processed_chunks
    
    def _calculate_coherence_score(self, text: str) -> float:
        """Calculate a simple coherence score for the chunk"""
        try:
            # Simple heuristics for coherence
            sentences = text.count('.') + text.count('!') + text.count('?')
            if sentences == 0:
                return 0.5  # Neutral score for single sentence or fragment
            
            # Prefer chunks with complete sentences
            words = len(text.split())
            avg_sentence_length = words / sentences if sentences > 0 else 0
            
            # Score based on sentence length distribution (10-30 words is good)
            if 10 <= avg_sentence_length <= 30:
                coherence = 0.9
            elif 5 <= avg_sentence_length <= 50:
                coherence = 0.7
            else:
                coherence = 0.5
            
            return coherence
            
        except Exception:
            return 0.5
    
    def _calculate_completeness_score(self, text: str) -> float:
        """Calculate completeness score based on text structure"""
        try:
            # Check if text ends with proper punctuation
            ends_properly = text.strip().endswith(('.', '!', '?', ':', ';'))
            
            # Check if text starts with capital letter or number
            starts_properly = text.strip() and (text.strip()[0].isupper() or text.strip()[0].isdigit())
            
            # Base score
            score = 0.5
            
            if ends_properly:
                score += 0.25
            if starts_properly:
                score += 0.25
            
            return min(score, 1.0)
            
        except Exception:
            return 0.5
    
    def _calculate_relevance_score(self, chunk_text: str, full_text: str) -> float:
        """Calculate relevance score of chunk to full document"""
        try:
            # Simple keyword overlap approach
            chunk_words = set(chunk_text.lower().split())
            full_words = set(full_text.lower().split())
            
            if not chunk_words or not full_words:
                return 0.5
            
            # Calculate Jaccard similarity
            intersection = len(chunk_words & full_words)
            union = len(chunk_words | full_words)
            
            if union == 0:
                return 0.5
            
            relevance = intersection / union
            
            # Normalize to reasonable range
            return min(max(relevance * 2, 0.1), 1.0)
            
        except Exception:
            return 0.5
    
    def update_config(self, new_config: ChunkingConfig):
        """Update chunking configuration"""
        old_strategy = self.config.strategy
        self.config = new_config
        
        # Reinitialize models if strategy changed
        if old_strategy != new_config.strategy:
            self._initialize_models()
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get current configuration information"""
        return {
            'strategy': self.config.strategy.value,
            'chunk_size': self.config.chunk_size,
            'chunk_overlap': self.config.chunk_overlap,
            'min_chunk_size': self.config.min_chunk_size,
            'max_chunk_size': self.config.max_chunk_size,
            'preserve_sentences': self.config.preserve_sentences,
            'preserve_paragraphs': self.config.preserve_paragraphs,
            'use_tokens': self.config.use_tokens,
            'tokenizer_model': self.config.tokenizer_model,
            'available_libraries': {
                'spacy': SPACY_AVAILABLE,
                'transformers': TRANSFORMERS_AVAILABLE
            },
            'models_loaded': {
                'nlp': self.nlp is not None,
                'tokenizer': self.tokenizer is not None
            }
        }


# Global chunker instance
_document_chunker = None

def get_document_chunker(config: ChunkingConfig = None) -> DocumentChunker:
    """Get or create global document chunker instance"""
    global _document_chunker
    
    if _document_chunker is None or (config and config != _document_chunker.config):
        _document_chunker = DocumentChunker(config)
    
    return _document_chunker
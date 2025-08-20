"""
Entity and Relationship Extraction Services
Handles extraction of entities and relationships from text using various NLP approaches
"""

import logging
import re
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict, Counter
import json

try:
    import spacy
    from spacy import displacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from .models import KnowledgeEntity, KnowledgeRelationship, EntityType, RelationshipType, DocumentChunk

logger = logging.getLogger(__name__)


@dataclass
class ExtractionConfig:
    """Configuration for entity and relationship extraction"""
    # Entity extraction
    entity_confidence_threshold: float = 0.7
    max_entities_per_chunk: int = 10
    entity_extraction_model: str = "spacy"  # spacy, transformers, regex
    merge_similar_entities: bool = True
    similarity_threshold: float = 0.8
    
    # Relationship extraction
    relationship_confidence_threshold: float = 0.6
    max_relationships_per_chunk: int = 15
    relationship_extraction_model: str = "rules"  # rules, transformers, openie
    
    # Processing options
    extract_dates: bool = True
    extract_numbers: bool = True
    extract_urls: bool = True
    extract_emails: bool = True
    custom_patterns: Dict[str, str] = None


class EntityExtractor:
    """Service for extracting entities from text"""
    
    def __init__(self, config: ExtractionConfig = None):
        self.config = config or ExtractionConfig()
        
        # Initialize models
        self.nlp = None
        self.ner_pipeline = None
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize NLP models for entity extraction"""
        try:
            if self.config.entity_extraction_model == "spacy" and SPACY_AVAILABLE:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                    logger.info("Loaded spaCy model for entity extraction")
                except OSError:
                    logger.warning("spaCy model not found, falling back to transformers")
                    self.config.entity_extraction_model = "transformers"
            
            if self.config.entity_extraction_model == "transformers" and TRANSFORMERS_AVAILABLE:
                try:
                    self.ner_pipeline = pipeline(
                        "ner", 
                        model="dbmdz/bert-large-cased-finetuned-conll03-english",
                        aggregation_strategy="simple"
                    )
                    logger.info("Loaded transformers NER pipeline")
                except Exception as e:
                    logger.warning(f"Failed to load transformers model: {e}")
                    
        except Exception as e:
            logger.error(f"Error initializing entity extraction models: {e}")
    
    def extract_entities(self, text: str, chunk_id: str = None, source_id: int = None) -> List[KnowledgeEntity]:
        """Extract entities from text"""
        if not text or not text.strip():
            return []
        
        start_time = time.time()
        entities = []
        
        try:
            if self.config.entity_extraction_model == "spacy" and self.nlp:
                entities = self._extract_with_spacy(text, chunk_id, source_id)
            elif self.config.entity_extraction_model == "transformers" and self.ner_pipeline:
                entities = self._extract_with_transformers(text, chunk_id, source_id)
            else:
                entities = self._extract_with_regex(text, chunk_id, source_id)
            
            # Merge similar entities if configured
            if self.config.merge_similar_entities:
                entities = self._merge_similar_entities(entities)
            
            # Limit results
            entities = entities[:self.config.max_entities_per_chunk]
            
            processing_time = (time.time() - start_time) * 1000
            logger.debug(f"Extracted {len(entities)} entities in {processing_time:.2f}ms")
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def _extract_with_spacy(self, text: str, chunk_id: str = None, source_id: int = None) -> List[KnowledgeEntity]:
        """Extract entities using spaCy"""
        entities = []
        doc = self.nlp(text)
        
        entity_counts = Counter()
        
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'EVENT', 'PRODUCT', 'WORK_OF_ART', 'LAW', 'LANGUAGE']:
                entity_type = self._map_spacy_label_to_entity_type(ent.label_)
                canonical_name = ent.text.lower().strip()
                
                # Skip very short entities
                if len(canonical_name) < 2:
                    continue
                
                entity_counts[canonical_name] += 1
                
                # Check if we already have this entity
                existing_entity = None
                for existing in entities:
                    if existing.canonical_name == canonical_name:
                        existing_entity = existing
                        break
                
                if existing_entity:
                    # Update existing entity
                    existing_entity.mention_count += 1
                    if source_id and source_id not in existing_entity.source_documents:
                        existing_entity.source_documents.append(source_id)
                else:
                    # Create new entity
                    entity = KnowledgeEntity(
                        name=ent.text.strip(),
                        entity_type=entity_type,
                        canonical_name=canonical_name,
                        description=f"{entity_type.value} extracted from text",
                        source_documents=[source_id] if source_id else [],
                        mention_count=1,
                        extraction_confidence=0.8,  # Default confidence for spaCy
                        type_confidence=0.8
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_with_transformers(self, text: str, chunk_id: str = None, source_id: int = None) -> List[KnowledgeEntity]:
        """Extract entities using transformers"""
        entities = []
        
        try:
            results = self.ner_pipeline(text)
            entity_counts = Counter()
            
            for result in results:
                if result['score'] >= self.config.entity_confidence_threshold:
                    entity_type = self._map_transformers_label_to_entity_type(result['entity_group'])
                    canonical_name = result['word'].lower().strip()
                    
                    # Skip very short entities
                    if len(canonical_name) < 2:
                        continue
                    
                    entity_counts[canonical_name] += 1
                    
                    # Check if we already have this entity
                    existing_entity = None
                    for existing in entities:
                        if existing.canonical_name == canonical_name:
                            existing_entity = existing
                            break
                    
                    if existing_entity:
                        # Update existing entity
                        existing_entity.mention_count += 1
                        existing_entity.extraction_confidence = max(
                            existing_entity.extraction_confidence, result['score']
                        )
                    else:
                        # Create new entity
                        entity = KnowledgeEntity(
                            name=result['word'].strip(),
                            entity_type=entity_type,
                            canonical_name=canonical_name,
                            description=f"{entity_type.value} extracted from text",
                            source_documents=[source_id] if source_id else [],
                            mention_count=1,
                            extraction_confidence=result['score'],
                            type_confidence=result['score']
                        )
                        entities.append(entity)
                        
        except Exception as e:
            logger.error(f"Error with transformers NER: {e}")
        
        return entities
    
    def _extract_with_regex(self, text: str, chunk_id: str = None, source_id: int = None) -> List[KnowledgeEntity]:
        """Extract entities using regex patterns"""
        entities = []
        
        # Define regex patterns for different entity types
        patterns = {
            EntityType.PERSON: [
                r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # First Last
                r'\b(?:Mr|Mrs|Ms|Dr|Prof)\. [A-Z][a-z]+\b'  # Title Name
            ],
            EntityType.ORGANIZATION: [
                r'\b[A-Z][A-Za-z]+ (?:Inc|Corp|LLC|Ltd|Company|Corporation)\b',
                r'\b[A-Z][A-Za-z]+ University\b',
                r'\b[A-Z][A-Za-z]+ Institute\b'
            ],
            EntityType.LOCATION: [
                r'\b[A-Z][a-z]+ City\b',
                r'\b[A-Z][a-z]+, [A-Z]{2}\b',  # City, State
                r'\b[A-Z][a-z]+ County\b'
            ],
            EntityType.DATE: [
                r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # MM/DD/YYYY
                r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b'
            ],
            EntityType.TECHNOLOGY: [
                r'\b[A-Z][a-z]+(?:\.js|\.py|\.java|\.cpp|\.html|\.css)\b',
                r'\b(?:Python|JavaScript|Java|C\+\+|HTML|CSS|SQL|React|Angular|Vue)\b'
            ]
        }
        
        # Add custom patterns if provided
        if self.config.custom_patterns:
            for entity_type_name, pattern in self.config.custom_patterns.items():
                try:
                    entity_type = EntityType(entity_type_name.lower())
                    if entity_type not in patterns:
                        patterns[entity_type] = []
                    patterns[entity_type].append(pattern)
                except ValueError:
                    logger.warning(f"Unknown entity type in custom patterns: {entity_type_name}")
        
        # Extract entities using patterns
        for entity_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                try:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        entity_text = match.group().strip()
                        canonical_name = entity_text.lower()
                        
                        # Skip very short matches
                        if len(canonical_name) < 2:
                            continue
                        
                        # Check if we already have this entity
                        existing_entity = None
                        for existing in entities:
                            if existing.canonical_name == canonical_name:
                                existing_entity = existing
                                break
                        
                        if existing_entity:
                            existing_entity.mention_count += 1
                        else:
                            entity = KnowledgeEntity(
                                name=entity_text,
                                entity_type=entity_type,
                                canonical_name=canonical_name,
                                description=f"{entity_type.value} extracted using regex",
                                source_documents=[source_id] if source_id else [],
                                mention_count=1,
                                extraction_confidence=0.6,  # Lower confidence for regex
                                type_confidence=0.6
                            )
                            entities.append(entity)
                            
                except re.error as e:
                    logger.warning(f"Invalid regex pattern: {pattern} - {e}")
        
        return entities
    
    def _merge_similar_entities(self, entities: List[KnowledgeEntity]) -> List[KnowledgeEntity]:
        """Merge similar entities based on name similarity"""
        if not entities:
            return entities
        
        merged_entities = []
        used_indices = set()
        
        for i, entity1 in enumerate(entities):
            if i in used_indices:
                continue
            
            # Find similar entities
            similar_entities = [entity1]
            used_indices.add(i)
            
            for j, entity2 in enumerate(entities[i+1:], start=i+1):
                if j in used_indices:
                    continue
                
                # Check similarity
                if self._calculate_entity_similarity(entity1, entity2) >= self.config.similarity_threshold:
                    similar_entities.append(entity2)
                    used_indices.add(j)
            
            # Merge similar entities
            if len(similar_entities) > 1:
                merged_entity = self._merge_entities(similar_entities)
                merged_entities.append(merged_entity)
            else:
                merged_entities.append(entity1)
        
        return merged_entities
    
    def _calculate_entity_similarity(self, entity1: KnowledgeEntity, entity2: KnowledgeEntity) -> float:
        """Calculate similarity between two entities"""
        # Must be same type
        if entity1.entity_type != entity2.entity_type:
            return 0.0
        
        # Calculate string similarity (simple Jaccard similarity)
        name1_words = set(entity1.canonical_name.split())
        name2_words = set(entity2.canonical_name.split())
        
        if not name1_words or not name2_words:
            return 0.0
        
        intersection = len(name1_words & name2_words)
        union = len(name1_words | name2_words)
        
        return intersection / union if union > 0 else 0.0
    
    def _merge_entities(self, entities: List[KnowledgeEntity]) -> KnowledgeEntity:
        """Merge multiple entities into one"""
        if not entities:
            return None
        
        # Use the entity with highest confidence as base
        base_entity = max(entities, key=lambda e: e.extraction_confidence)
        
        # Aggregate data from all entities
        all_names = list(set([e.name for e in entities]))
        all_aliases = []
        all_source_docs = []
        total_mentions = 0
        max_confidence = 0.0
        
        for entity in entities:
            all_aliases.extend(entity.aliases)
            all_source_docs.extend(entity.source_documents)
            total_mentions += entity.mention_count
            max_confidence = max(max_confidence, entity.extraction_confidence)
        
        # Create merged entity
        merged_entity = KnowledgeEntity(
            name=base_entity.name,
            entity_type=base_entity.entity_type,
            canonical_name=base_entity.canonical_name,
            description=base_entity.description,
            aliases=list(set(all_aliases + [name for name in all_names if name != base_entity.name])),
            source_documents=list(set(all_source_docs)),
            mention_count=total_mentions,
            extraction_confidence=max_confidence,
            type_confidence=max_confidence
        )
        
        return merged_entity
    
    def _map_spacy_label_to_entity_type(self, spacy_label: str) -> EntityType:
        """Map spaCy entity labels to our EntityType enum"""
        mapping = {
            'PERSON': EntityType.PERSON,
            'ORG': EntityType.ORGANIZATION,
            'GPE': EntityType.LOCATION,  # Geopolitical entity
            'EVENT': EntityType.EVENT,
            'PRODUCT': EntityType.PRODUCT,
            'WORK_OF_ART': EntityType.CONCEPT,
            'LAW': EntityType.CONCEPT,
            'LANGUAGE': EntityType.CONCEPT
        }
        return mapping.get(spacy_label, EntityType.CONCEPT)
    
    def _map_transformers_label_to_entity_type(self, transformers_label: str) -> EntityType:
        """Map transformers entity labels to our EntityType enum"""
        mapping = {
            'PER': EntityType.PERSON,
            'ORG': EntityType.ORGANIZATION,
            'LOC': EntityType.LOCATION,
            'MISC': EntityType.CONCEPT
        }
        return mapping.get(transformers_label, EntityType.CONCEPT)


class RelationshipExtractor:
    """Service for extracting relationships between entities"""
    
    def __init__(self, config: ExtractionConfig = None):
        self.config = config or ExtractionConfig()
        self.nlp = None
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize models for relationship extraction"""
        try:
            if SPACY_AVAILABLE:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                    logger.info("Loaded spaCy model for relationship extraction")
                except OSError:
                    logger.warning("spaCy model not found for relationship extraction")
        except Exception as e:
            logger.error(f"Error initializing relationship extraction models: {e}")
    
    def extract_relationships(self, text: str, entities: List[KnowledgeEntity], 
                            chunk_id: str = None, source_id: int = None) -> List[KnowledgeRelationship]:
        """Extract relationships between entities in text"""
        if not text or not entities or len(entities) < 2:
            return []
        
        start_time = time.time()
        
        try:
            if self.config.relationship_extraction_model == "rules" or not self.nlp:
                relationships = self._extract_with_rules(text, entities, chunk_id, source_id)
            else:
                relationships = self._extract_with_nlp(text, entities, chunk_id, source_id)
            
            # Limit results
            relationships = relationships[:self.config.max_relationships_per_chunk]
            
            processing_time = (time.time() - start_time) * 1000
            logger.debug(f"Extracted {len(relationships)} relationships in {processing_time:.2f}ms")
            
            return relationships
            
        except Exception as e:
            logger.error(f"Error extracting relationships: {e}")
            return []
    
    def _extract_with_rules(self, text: str, entities: List[KnowledgeEntity], 
                           chunk_id: str = None, source_id: int = None) -> List[KnowledgeRelationship]:
        """Extract relationships using rule-based approach"""
        relationships = []
        text_lower = text.lower()
        
        # Define relationship patterns
        patterns = {
            RelationshipType.WORKS_FOR: [
                r'{entity1} works (?:for|at) {entity2}',
                r'{entity1} (?:is|was) employed (?:by|at) {entity2}',
                r'{entity1} (?:is|was) a (?:member|employee) of {entity2}'
            ],
            RelationshipType.LOCATED_IN: [
                r'{entity1} (?:is|was) (?:in|located in|based in) {entity2}',
                r'{entity1}, {entity2}',
                r'{entity1} of {entity2}'
            ],
            RelationshipType.CREATED_BY: [
                r'{entity2} (?:created|developed|built|made) {entity1}',
                r'{entity1} (?:by|from) {entity2}',
                r'{entity1} (?:was|is) (?:created|developed|built) by {entity2}'
            ],
            RelationshipType.PART_OF: [
                r'{entity1} (?:is|was) (?:part of|a component of) {entity2}',
                r'{entity1} belongs to {entity2}',
                r'{entity2} includes {entity1}'
            ]
        }
        
        # Check all pairs of entities
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i+1:], start=i+1):
                # Try each relationship pattern
                for rel_type, type_patterns in patterns.items():
                    for pattern in type_patterns:
                        # Create pattern with entity placeholders
                        pattern1 = pattern.replace('{entity1}', re.escape(entity1.name.lower()))
                        pattern1 = pattern1.replace('{entity2}', re.escape(entity2.name.lower()))
                        
                        pattern2 = pattern.replace('{entity1}', re.escape(entity2.name.lower()))
                        pattern2 = pattern2.replace('{entity2}', re.escape(entity1.name.lower()))
                        
                        # Check both directions
                        if re.search(pattern1, text_lower):
                            relationship = KnowledgeRelationship(
                                source_entity_id=entity1.id,
                                target_entity_id=entity2.id,
                                relationship_type=rel_type,
                                description=f"{entity1.name} {rel_type.value} {entity2.name}",
                                weight=1.0,
                                confidence=0.7,
                                source_documents=[source_id] if source_id else [],
                                source_chunks=[chunk_id] if chunk_id else [],
                                evidence_text=[text[:200]]  # First 200 chars as evidence
                            )
                            relationships.append(relationship)
                            
                        elif re.search(pattern2, text_lower):
                            relationship = KnowledgeRelationship(
                                source_entity_id=entity2.id,
                                target_entity_id=entity1.id,
                                relationship_type=rel_type,
                                description=f"{entity2.name} {rel_type.value} {entity1.name}",
                                weight=1.0,
                                confidence=0.7,
                                source_documents=[source_id] if source_id else [],
                                source_chunks=[chunk_id] if chunk_id else [],
                                evidence_text=[text[:200]]
                            )
                            relationships.append(relationship)
        
        # Add proximity-based relationships for entities that appear close together
        relationships.extend(self._extract_proximity_relationships(text, entities, chunk_id, source_id))
        
        return relationships
    
    def _extract_with_nlp(self, text: str, entities: List[KnowledgeEntity], 
                         chunk_id: str = None, source_id: int = None) -> List[KnowledgeRelationship]:
        """Extract relationships using NLP dependency parsing"""
        if not self.nlp:
            return self._extract_with_rules(text, entities, chunk_id, source_id)
        
        relationships = []
        doc = self.nlp(text)
        
        # Create entity span mapping
        entity_spans = {}
        for ent in doc.ents:
            for entity in entities:
                if entity.name.lower() in ent.text.lower():
                    entity_spans[ent] = entity
                    break
        
        # Extract relationships using dependency parsing
        for sent in doc.sents:
            for token in sent:
                # Look for verbs that might indicate relationships
                if token.pos_ == "VERB":
                    # Find subjects and objects
                    subjects = []
                    objects = []
                    
                    for child in token.children:
                        if child.dep_ in ["nsubj", "nsubjpass"]:
                            subjects.append(child)
                        elif child.dep_ in ["dobj", "pobj", "attr"]:
                            objects.append(child)
                    
                    # Create relationships between subjects and objects
                    for subj in subjects:
                        for obj in objects:
                            subj_entity = self._find_entity_for_token(subj, entities, doc)
                            obj_entity = self._find_entity_for_token(obj, entities, doc)
                            
                            if subj_entity and obj_entity and subj_entity.id != obj_entity.id:
                                rel_type = self._infer_relationship_type(token.lemma_)
                                
                                relationship = KnowledgeRelationship(
                                    source_entity_id=subj_entity.id,
                                    target_entity_id=obj_entity.id,
                                    relationship_type=rel_type,
                                    description=f"{subj_entity.name} {token.lemma_} {obj_entity.name}",
                                    weight=0.8,
                                    confidence=0.6,
                                    source_documents=[source_id] if source_id else [],
                                    source_chunks=[chunk_id] if chunk_id else [],
                                    evidence_text=[sent.text]
                                )
                                relationships.append(relationship)
        
        # Add rule-based relationships as well
        relationships.extend(self._extract_with_rules(text, entities, chunk_id, source_id))
        
        return relationships
    
    def _extract_proximity_relationships(self, text: str, entities: List[KnowledgeEntity], 
                                       chunk_id: str = None, source_id: int = None) -> List[KnowledgeRelationship]:
        """Extract relationships based on entity proximity in text"""
        relationships = []
        text_lower = text.lower()
        
        # Find entity positions in text
        entity_positions = []
        for entity in entities:
            pos = text_lower.find(entity.name.lower())
            while pos != -1:
                entity_positions.append((entity, pos, pos + len(entity.name)))
                pos = text_lower.find(entity.name.lower(), pos + 1)
        
        # Sort by position
        entity_positions.sort(key=lambda x: x[1])
        
        # Create proximity relationships
        max_distance = 100  # Maximum character distance for proximity relationships
        
        for i, (entity1, start1, end1) in enumerate(entity_positions):
            for j, (entity2, start2, end2) in enumerate(entity_positions[i+1:], start=i+1):
                distance = start2 - end1
                
                if distance > max_distance:
                    break  # Too far apart
                
                if entity1.id != entity2.id:
                    # Create a generic "related to" relationship
                    confidence = max(0.1, 0.5 - (distance / max_distance) * 0.4)  # Closer = higher confidence
                    
                    relationship = KnowledgeRelationship(
                        source_entity_id=entity1.id,
                        target_entity_id=entity2.id,
                        relationship_type=RelationshipType.RELATED_TO,
                        description=f"{entity1.name} appears near {entity2.name}",
                        weight=confidence,
                        confidence=confidence,
                        source_documents=[source_id] if source_id else [],
                        source_chunks=[chunk_id] if chunk_id else [],
                        evidence_text=[text[max(0, start1-20):min(len(text), end2+20)]]
                    )
                    relationships.append(relationship)
        
        return relationships
    
    def _find_entity_for_token(self, token, entities: List[KnowledgeEntity], doc) -> Optional[KnowledgeEntity]:
        """Find which entity a token belongs to"""
        token_text = token.text.lower()
        
        # First, check if token is part of any entity
        for entity in entities:
            if token_text in entity.name.lower() or token_text in entity.canonical_name:
                return entity
        
        # Check if token is part of a larger span that matches an entity
        for ent in doc.ents:
            if token in ent:
                for entity in entities:
                    if entity.name.lower() in ent.text.lower():
                        return entity
        
        return None
    
    def _infer_relationship_type(self, verb: str) -> RelationshipType:
        """Infer relationship type from verb"""
        verb_lower = verb.lower()
        
        if verb_lower in ['work', 'employ', 'hire']:
            return RelationshipType.WORKS_FOR
        elif verb_lower in ['create', 'build', 'develop', 'make', 'produce']:
            return RelationshipType.CREATED_BY
        elif verb_lower in ['use', 'utilize', 'employ']:
            return RelationshipType.USED_BY
        elif verb_lower in ['locate', 'situate', 'place']:
            return RelationshipType.LOCATED_IN
        elif verb_lower in ['mention', 'cite', 'reference']:
            return RelationshipType.MENTIONS
        elif verb_lower in ['depend', 'rely', 'require']:
            return RelationshipType.DEPENDS_ON
        else:
            return RelationshipType.RELATED_TO


# Global extractor instances
_entity_extractor = None
_relationship_extractor = None

def get_entity_extractor(config: ExtractionConfig = None) -> EntityExtractor:
    """Get or create global entity extractor instance"""
    global _entity_extractor
    
    if _entity_extractor is None or (config and config != _entity_extractor.config):
        _entity_extractor = EntityExtractor(config)
    
    return _entity_extractor

def get_relationship_extractor(config: ExtractionConfig = None) -> RelationshipExtractor:
    """Get or create global relationship extractor instance"""
    global _relationship_extractor
    
    if _relationship_extractor is None or (config and config != _relationship_extractor.config):
        _relationship_extractor = RelationshipExtractor(config)
    
    return _relationship_extractor
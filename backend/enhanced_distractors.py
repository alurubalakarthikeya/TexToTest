"""
Enhanced distractor generator with semantic similarity using sentence transformers.
This module provides better quality distractors through semantic analysis.
"""

import numpy as np
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
import re
import random
from collections import defaultdict

try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not installed. Falling back to pattern-based distractors only.")
    # Create dummy classes for compatibility
    class SentenceTransformer:
        def __init__(self, *args, **kwargs):
            pass
        def encode(self, *args, **kwargs):
            return []
    
    class util:
        @staticmethod
        def pytorch_cos_sim(*args, **kwargs):
            return []

@dataclass
class DistractorCandidate:
    text: str
    score: float
    source: str  # 'semantic', 'pattern', 'heuristic'
    confidence: float

class EnhancedDistractorGenerator:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize enhanced distractor generator with semantic similarity model
        
        Args:
            model_name: SentenceTransformers model name (lightweight by default)
        """
        self.model = None
        global SENTENCE_TRANSFORMERS_AVAILABLE
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                print(f"Loaded semantic model: {model_name}")
            except Exception as e:
                print(f"Failed to load semantic model: {e}")
                SENTENCE_TRANSFORMERS_AVAILABLE = False
        
        # Initialize pattern-based generator as fallback
        from distractor_generator import DistractorGenerator
        self.pattern_generator = DistractorGenerator()
        
        # Semantic similarity thresholds
        self.similarity_thresholds = {
            'too_similar': 0.85,  # Too close to correct answer
            'good_distractor': 0.3,  # Good semantic similarity
            'minimum': 0.1  # Minimum semantic relatedness
        }
        
        # Domain-specific distractor pools
        self.domain_pools = {
            'science': [
                'hypothesis', 'theory', 'experiment', 'observation', 'analysis',
                'synthesis', 'catalyst', 'reaction', 'element', 'compound',
                'molecule', 'atom', 'electron', 'proton', 'neutron'
            ],
            'history': [
                'revolution', 'empire', 'dynasty', 'civilization', 'monarchy',
                'democracy', 'republic', 'conquest', 'treaty', 'alliance',
                'war', 'peace', 'culture', 'society', 'economy'
            ],
            'literature': [
                'metaphor', 'symbolism', 'allegory', 'irony', 'theme',
                'plot', 'character', 'setting', 'narrative', 'conflict',
                'climax', 'resolution', 'protagonist', 'antagonist', 'dialogue'
            ],
            'mathematics': [
                'equation', 'function', 'variable', 'constant', 'coefficient',
                'polynomial', 'derivative', 'integral', 'limit', 'theorem',
                'proof', 'axiom', 'formula', 'algorithm', 'matrix'
            ]
        }

    def generate_semantic_distractors(self, correct_answer: str, context: str, 
                                    num_distractors: int = 3) -> List[DistractorCandidate]:
        """Generate distractors using semantic similarity"""
        if not self.model:
            return []
        
        # Extract candidate words/phrases from context
        candidates = self._extract_semantic_candidates(context, correct_answer)
        
        if not candidates:
            return []
        
        # Encode correct answer and candidates
        try:
            correct_embedding = self.model.encode([correct_answer])
            candidate_embeddings = self.model.encode(candidates)
            
            # Calculate similarities
            similarities = util.cos_sim(correct_embedding, candidate_embeddings)[0]
            
            # Filter and score candidates
            distractor_candidates = []
            for i, candidate in enumerate(candidates):
                similarity = similarities[i].item()
                
                # Skip if too similar or too dissimilar
                if (similarity > self.similarity_thresholds['too_similar'] or 
                    similarity < self.similarity_thresholds['minimum']):
                    continue
                
                # Calculate confidence based on similarity range
                if similarity > self.similarity_thresholds['good_distractor']:
                    confidence = 0.9
                else:
                    confidence = similarity / self.similarity_thresholds['good_distractor']
                
                distractor_candidates.append(DistractorCandidate(
                    text=candidate,
                    score=similarity,
                    source='semantic',
                    confidence=confidence
                ))
            
            # Sort by optimal similarity (not too high, not too low)
            distractor_candidates.sort(
                key=lambda x: abs(x.score - self.similarity_thresholds['good_distractor'])
            )
            
            return distractor_candidates[:num_distractors]
            
        except Exception as e:
            print(f"Semantic distractor generation failed: {e}")
            return []

    def _extract_semantic_candidates(self, context: str, correct_answer: str) -> List[str]:
        """Extract candidate words/phrases from context for semantic comparison"""
        # Use various extraction strategies
        candidates = set()
        
        # Extract nouns and noun phrases (basic NLP)
        words = context.split()
        for i, word in enumerate(words):
            # Single word candidates (nouns, proper nouns)
            cleaned_word = re.sub(r'[^\w]', '', word)
            if (len(cleaned_word) > 3 and 
                cleaned_word.lower() != correct_answer.lower() and
                cleaned_word.istitle()):  # Likely proper noun
                candidates.add(cleaned_word)
            
            # Two-word phrases
            if i < len(words) - 1:
                phrase = f"{cleaned_word} {re.sub(r'[^\w]', '', words[i+1])}"
                if (len(phrase) > 5 and 
                    phrase.lower() != correct_answer.lower()):
                    candidates.add(phrase)
        
        # Extract quoted terms and definitions
        quoted_terms = re.findall(r'"([^"]+)"', context)
        for term in quoted_terms:
            if (len(term) > 2 and 
                term.lower() != correct_answer.lower()):
                candidates.add(term)
        
        # Extract terms in italics or emphasized text (common in academic texts)
        emphasized = re.findall(r'\*([^*]+)\*', context)
        for term in emphasized:
            if (len(term) > 2 and 
                term.lower() != correct_answer.lower()):
                candidates.add(term)
        
        return list(candidates)[:50]  # Limit for performance

    def generate_domain_specific_distractors(self, correct_answer: str, domain: str, 
                                           num_distractors: int = 2) -> List[DistractorCandidate]:
        """Generate distractors from domain-specific pools"""
        if domain not in self.domain_pools:
            domain = 'science'  # Default fallback
        
        pool = self.domain_pools[domain]
        distractors = []
        
        # Filter out the correct answer and select random distractors
        filtered_pool = [item for item in pool 
                        if item.lower() != correct_answer.lower()]
        
        selected = random.sample(filtered_pool, min(num_distractors, len(filtered_pool)))
        
        for distractor in selected:
            distractors.append(DistractorCandidate(
                text=distractor,
                score=0.5,  # Neutral semantic score
                source='domain',
                confidence=0.7
            ))
        
        return distractors

    def generate_hybrid_distractors(self, correct_answer: str, context: str, 
                                  domain: Optional[str] = None,
                                  num_distractors: int = 3) -> List[str]:
        """Generate distractors using hybrid approach combining multiple methods"""
        all_candidates = []
        
        # 1. Semantic distractors (if available)
        if self.model:
            semantic_candidates = self.generate_semantic_distractors(
                correct_answer, context, num_distractors
            )
            all_candidates.extend(semantic_candidates)
        
        # 2. Domain-specific distractors
        if domain:
            domain_candidates = self.generate_domain_specific_distractors(
                correct_answer, domain, max(1, num_distractors // 2)
            )
            all_candidates.extend(domain_candidates)
        
        # 3. Pattern-based distractors (fallback)
        pattern_distractors = self.pattern_generator.generate_pattern_based_distractors(
            correct_answer
        )
        for distractor in pattern_distractors:
            all_candidates.append(DistractorCandidate(
                text=distractor,
                score=0.3,
                source='pattern',
                confidence=0.6
            ))
        
        # 4. Heuristic distractors from context
        heuristic_distractors = self.pattern_generator.generate_heuristic_distractors(
            correct_answer, context
        )
        for distractor in heuristic_distractors:
            all_candidates.append(DistractorCandidate(
                text=distractor,
                score=0.4,
                source='heuristic',
                confidence=0.7
            ))
        
        # Remove duplicates and correct answer
        unique_candidates = []
        seen_texts = set()
        seen_texts.add(correct_answer.lower())
        
        for candidate in all_candidates:
            if (candidate.text.lower() not in seen_texts and 
                len(candidate.text.strip()) > 0):
                unique_candidates.append(candidate)
                seen_texts.add(candidate.text.lower())
        
        # Sort by confidence and source priority
        source_priority = {'semantic': 3, 'domain': 2, 'heuristic': 1, 'pattern': 0}
        unique_candidates.sort(
            key=lambda x: (source_priority.get(x.source, 0), x.confidence),
            reverse=True
        )
        
        # Select top distractors
        selected_distractors = [c.text for c in unique_candidates[:num_distractors]]
        
        # If still not enough, add generic ones
        while len(selected_distractors) < num_distractors:
            generic = self._generate_generic_distractor(
                correct_answer, selected_distractors
            )
            if generic and generic not in selected_distractors:
                selected_distractors.append(generic)
            else:
                break
        
        return selected_distractors

    def _generate_generic_distractor(self, correct_answer: str, 
                                   existing_distractors: List[str]) -> Optional[str]:
        """Generate generic distractors as last resort"""
        generic_options = [
            f"Not {correct_answer}",
            f"Alternative to {correct_answer}",
            f"Opposite of {correct_answer}",
            "None of the above",
            "All of the above",
            "Cannot be determined",
            "Insufficient information"
        ]
        
        for option in generic_options:
            if option not in existing_distractors:
                return option
        
        return None

    def evaluate_distractor_quality(self, correct_answer: str, 
                                   distractors: List[str]) -> Dict[str, float]:
        """Evaluate the quality of generated distractors"""
        if not self.model:
            return {"overall_quality": 0.5}  # Default when no semantic model
        
        try:
            # Encode correct answer and distractors
            all_texts = [correct_answer] + distractors
            embeddings = self.model.encode(all_texts)
            
            correct_embedding = embeddings[0:1]
            distractor_embeddings = embeddings[1:]
            
            # Calculate similarities
            similarities = util.cos_sim(correct_embedding, distractor_embeddings)[0]
            
            # Quality metrics
            avg_similarity = similarities.mean().item()
            similarity_variance = similarities.var().item()
            
            # Ideal range: not too similar, not too different
            ideal_similarity = 0.4
            quality_score = 1.0 - abs(avg_similarity - ideal_similarity)
            
            # Diversity bonus
            diversity_score = similarity_variance
            
            overall_quality = (quality_score + diversity_score) / 2
            
            return {
                "overall_quality": min(1.0, max(0.0, overall_quality)),
                "avg_similarity": avg_similarity,
                "diversity": diversity_score,
                "individual_similarities": similarities.tolist()
            }
            
        except Exception as e:
            print(f"Quality evaluation failed: {e}")
            return {"overall_quality": 0.5}

# Factory function for backward compatibility
def create_enhanced_distractor_generator(**kwargs) -> EnhancedDistractorGenerator:
    """Create enhanced distractor generator with optional configuration"""
    return EnhancedDistractorGenerator(**kwargs)
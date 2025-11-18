import re
import random
from typing import List, Dict, Set, Tuple
from collections import defaultdict, Counter

# Try to import NLTK components with fallbacks
try:
    import nltk
    from nltk.corpus import wordnet
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.pos_tag import pos_tag
    from nltk.chunk import ne_chunk
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    print("NLTK not available, using basic text processing")
    NLTK_AVAILABLE = False
    WordNetLemmatizer = None

class ImprovedDistractorGenerator:
    def __init__(self):
        # Download required NLTK data if available
        if NLTK_AVAILABLE:
            try:
                import nltk
                nltk.download('punkt', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
                nltk.download('wordnet', quiet=True)
                nltk.download('maxent_ne_chunker', quiet=True)
                nltk.download('words', quiet=True)
                nltk.download('omw-1.4', quiet=True)
                self.lemmatizer = WordNetLemmatizer()
                print("✓ NLTK initialized successfully")
            except Exception as e:
                print(f"NLTK initialization failed: {e}")
                self.lemmatizer = None
        else:
            print("Using basic text processing (NLTK not available)")
            self.lemmatizer = None
        
        # Define semantic categories with domain-specific terms
        self.semantic_categories = {
            'networking': {
                'concepts': ['protocol', 'packet', 'router', 'switch', 'hub', 'gateway', 'firewall', 'bandwidth', 'latency', 'throughput', 'topology', 'ethernet', 'wifi', 'bluetooth'],
                'protocols': ['TCP', 'UDP', 'HTTP', 'HTTPS', 'FTP', 'SMTP', 'DNS', 'DHCP', 'IP', 'ICMP', 'ARP', 'BGP'],
                'layers': ['physical', 'data link', 'network', 'transport', 'session', 'presentation', 'application'],
                'devices': ['router', 'switch', 'hub', 'modem', 'access point', 'bridge', 'repeater', 'gateway']
            },
            'programming': {
                'concepts': ['algorithm', 'function', 'variable', 'loop', 'condition', 'array', 'object', 'class', 'method', 'parameter'],
                'languages': ['Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'PHP', 'Go', 'Rust', 'Swift'],
                'structures': ['list', 'dictionary', 'set', 'tuple', 'queue', 'stack', 'tree', 'graph', 'heap'],
                'paradigms': ['procedural', 'object-oriented', 'functional', 'declarative', 'imperative']
            },
            'computer_science': {
                'concepts': ['algorithm', 'complexity', 'recursion', 'iteration', 'optimization', 'hashing', 'encryption', 'compression'],
                'structures': ['array', 'linked list', 'binary tree', 'hash table', 'graph', 'heap', 'stack', 'queue'],
                'algorithms': ['sorting', 'searching', 'traversal', 'shortest path', 'minimum spanning tree', 'dynamic programming'],
                'complexity': ['O(1)', 'O(n)', 'O(log n)', 'O(n²)', 'O(2^n)', 'polynomial', 'exponential', 'logarithmic']
            },
            'technology': {
                'concepts': ['system', 'process', 'service', 'application', 'platform', 'framework', 'architecture', 'infrastructure'],
                'types': ['hardware', 'software', 'firmware', 'middleware', 'database', 'server', 'client', 'cloud'],
                'methods': ['implementation', 'deployment', 'configuration', 'optimization', 'monitoring', 'maintenance'],
                'properties': ['scalable', 'reliable', 'secure', 'efficient', 'robust', 'flexible', 'maintainable']
            }
        }
        
        # Common distractor patterns for different answer types
        self.distractor_patterns = {
            'definition': {
                'prefixes': ['A type of', 'A method of', 'A process of', 'A system for', 'A technique for'],
                'modifiers': ['advanced', 'basic', 'simple', 'complex', 'modern', 'traditional', 'innovative', 'standard'],
                'suffixes': ['system', 'process', 'method', 'technique', 'approach', 'strategy', 'mechanism']
            },
            'technology': {
                'versions': ['2.0', '3.0', '4.0', 'Pro', 'Advanced', 'Enterprise', 'Standard', 'Basic'],
                'protocols': ['TCP', 'UDP', 'HTTP', 'FTP', 'SMTP', 'DNS', 'DHCP', 'SSL', 'TLS'],
                'standards': ['IEEE', 'ISO', 'ITU', 'RFC', 'W3C', 'ANSI', 'NIST']
            }
        }
        
        # Quality thresholds
        self.min_distractor_length = 2
        self.max_distractor_length = 50
        self.similarity_threshold = 0.3

    def extract_domain_context(self, text: str) -> str:
        """Determine the domain/context of the text"""
        text_lower = text.lower()
        domain_scores = {}
        
        for domain, categories in self.semantic_categories.items():
            score = 0
            for category, terms in categories.items():
                for term in terms:
                    if term.lower() in text_lower:
                        score += 1
            domain_scores[domain] = score
        
        # Return domain with highest score, or 'general' if no clear domain
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                return best_domain
        
        return 'general'

    def extract_entities_advanced(self, text: str) -> Dict[str, Set[str]]:
        """Extract entities using multiple approaches"""
        entities = defaultdict(set)
        
        # Method 1: Pattern-based extraction
        patterns = {
            'technical_terms': r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})*\b',  # Acronyms
            'protocols': r'\b(?:TCP|UDP|HTTP|HTTPS|FTP|SMTP|DNS|DHCP|IP|SSL|TLS)\b',
            'numbers': r'\b\d+(?:\.\d+)?\s*(?:MHz|GHz|GB|MB|KB|Mbps|Gbps|%|bytes?)\b',
            'devices': r'\b(?:router|switch|hub|modem|server|client|computer|laptop|smartphone)\b',
            'concepts': r'\b[a-z]+(?:ing|tion|sion|ment|ness|ity|ism|ology)\b'
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) >= self.min_distractor_length:
                    entities[entity_type].add(match.strip())
        
        # Method 2: NLTK-based extraction (if available)
        if NLTK_AVAILABLE:
            try:
                tokens = word_tokenize(text)
                pos_tags = pos_tag(tokens)
                
                # Extract nouns and proper nouns
                for word, pos in pos_tags:
                    if pos in ['NN', 'NNS', 'NNP', 'NNPS'] and len(word) >= self.min_distractor_length:
                        entities['nouns'].add(word)
            except Exception as e:
                print(f"NLTK processing failed: {e}")
        
        # Method 3: Basic pattern-based noun extraction (fallback)
        if 'nouns' not in entities or not entities['nouns']:
            # Simple pattern for likely nouns (words that follow 'the', 'a', 'an')
            noun_patterns = [
                r'(?:the|a|an)\s+([a-zA-Z]+)',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'  # Capitalized words/phrases
            ]
            
            for pattern in noun_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if len(match) >= self.min_distractor_length:
                        entities['nouns'].add(match)
        
        return dict(entities)

    def generate_semantic_distractors(self, correct_answer: str, context: str, domain: str) -> List[str]:
        """Generate semantically similar but incorrect distractors"""
        distractors = []
        
        # Get domain-specific terms
        if domain in self.semantic_categories:
            domain_terms = []
            for category, terms in self.semantic_categories[domain].items():
                domain_terms.extend(terms)
            
            # Find terms similar to the correct answer
            answer_lower = correct_answer.lower()
            similar_terms = []
            
            for term in domain_terms:
                if (term.lower() != answer_lower and 
                    self._calculate_similarity(term.lower(), answer_lower) > self.similarity_threshold):
                    similar_terms.append(term)
            
            # Add best matches
            distractors.extend(similar_terms[:2])
        
        # Generate pattern-based alternatives
        if len(distractors) < 3:
            pattern_distractors = self._generate_pattern_distractors(correct_answer, domain)
            distractors.extend(pattern_distractors)
        
        return distractors[:3]

    def generate_contextual_distractors(self, correct_answer: str, context: str) -> List[str]:
        """Generate distractors from context that are plausible but incorrect"""
        entities = self.extract_entities_advanced(context)
        distractors = []
        
        # Determine the type of the correct answer
        answer_type = self._classify_answer_type(correct_answer)
        
        # Get candidates from the same category
        candidates = []
        for entity_type, entity_set in entities.items():
            if self._type_matches(answer_type, entity_type):
                candidates.extend(list(entity_set))
        
        # Filter out the correct answer and select best candidates
        candidates = [c for c in candidates if c.lower() != correct_answer.lower()]
        
        # Score candidates based on length and complexity similarity
        scored_candidates = []
        for candidate in candidates:
            score = self._score_distractor(candidate, correct_answer)
            if score > 0:
                scored_candidates.append((candidate, score))
        
        # Sort by score and take top candidates
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        distractors.extend([c[0] for c in scored_candidates[:3]])
        
        return distractors[:3]

    def generate_synthetic_distractors(self, correct_answer: str, domain: str) -> List[str]:
        """Generate synthetic but plausible distractors"""
        distractors = []
        
        # Method 1: Morphological variations
        if len(correct_answer) > 4:
            # Create variations by changing suffixes
            variations = [
                correct_answer + 's',
                correct_answer + 'ing',
                correct_answer.rstrip('s') if correct_answer.endswith('s') else correct_answer,
                correct_answer.rstrip('ing') if correct_answer.endswith('ing') else correct_answer,
            ]
            
            # Add prefix variations
            prefixes = ['pre-', 'post-', 'anti-', 'pro-', 'sub-', 'super-']
            for prefix in prefixes[:2]:
                variations.append(prefix + correct_answer.lower())
            
            # Filter valid variations
            for var in variations:
                if (len(var) >= self.min_distractor_length and 
                    var.lower() != correct_answer.lower() and
                    len(var) <= self.max_distractor_length):
                    distractors.append(var.capitalize())
        
        # Method 2: Combination with domain terms
        if domain in self.semantic_categories:
            domain_terms = []
            for terms in self.semantic_categories[domain].values():
                domain_terms.extend(terms[:5])  # Limit to avoid too many options
            
            # Create compound terms
            for term in domain_terms[:3]:
                if term.lower() != correct_answer.lower():
                    combinations = [
                        f"{correct_answer} {term}",
                        f"{term} {correct_answer}",
                        f"{correct_answer.split()[0]} {term}" if ' ' in correct_answer else None
                    ]
                    
                    for combo in combinations:
                        if (combo and len(combo) <= self.max_distractor_length):
                            distractors.append(combo.title())
        
        return distractors[:3]

    def _classify_answer_type(self, answer: str) -> str:
        """Classify the type of answer for better distractor matching"""
        answer_lower = answer.lower()
        
        # Check for patterns
        if re.match(r'^[A-Z]{2,}$', answer):
            return 'acronym'
        elif re.match(r'^\d+(?:\.\d+)?\s*(?:MB|GB|MHz|GHz|%|bytes?)$', answer):
            return 'measurement'
        elif any(word in answer_lower for word in ['protocol', 'algorithm', 'method', 'process']):
            return 'process'
        elif answer[0].isupper() and ' ' not in answer:
            return 'proper_noun'
        elif any(word in answer_lower for word in ['system', 'network', 'device', 'service']):
            return 'system'
        else:
            return 'concept'

    def _type_matches(self, answer_type: str, entity_type: str) -> bool:
        """Check if answer type matches entity type for better distractor selection"""
        type_mappings = {
            'acronym': ['technical_terms', 'protocols'],
            'measurement': ['numbers'],
            'process': ['concepts', 'nouns'],
            'proper_noun': ['nouns', 'technical_terms'],
            'system': ['devices', 'nouns', 'concepts'],
            'concept': ['nouns', 'concepts', 'technical_terms']
        }
        
        return entity_type in type_mappings.get(answer_type, [])

    def _score_distractor(self, candidate: str, correct_answer: str) -> float:
        """Score a distractor candidate based on plausibility"""
        score = 0.0
        
        # Length similarity (prefer similar length)
        len_diff = abs(len(candidate) - len(correct_answer))
        if len_diff <= 3:
            score += 0.3
        elif len_diff <= 6:
            score += 0.1
        
        # Word count similarity
        candidate_words = len(candidate.split())
        correct_words = len(correct_answer.split())
        if candidate_words == correct_words:
            score += 0.2
        
        # Capitalization pattern similarity
        if candidate[0].isupper() == correct_answer[0].isupper():
            score += 0.2
        
        # Avoid too similar or too different
        similarity = self._calculate_similarity(candidate.lower(), correct_answer.lower())
        if 0.2 <= similarity <= 0.7:
            score += 0.3
        
        # Penalize very short or very long candidates
        if len(candidate) < 3 or len(candidate) > 30:
            score -= 0.5
        
        return max(0.0, score)

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using Levenshtein-like approach"""
        if not str1 or not str2:
            return 0.0
        
        # Simple character-based similarity
        common_chars = set(str1.lower()) & set(str2.lower())
        total_chars = set(str1.lower()) | set(str2.lower())
        
        if not total_chars:
            return 0.0
        
        return len(common_chars) / len(total_chars)

    def _generate_pattern_distractors(self, correct_answer: str, domain: str) -> List[str]:
        """Generate distractors using predefined patterns"""
        distractors = []
        
        if domain in self.distractor_patterns:
            patterns = self.distractor_patterns[domain]
            
            # Generate variations based on patterns
            if 'versions' in patterns:
                for version in patterns['versions'][:2]:
                    if version not in correct_answer:
                        distractors.append(f"{correct_answer} {version}")
            
            if 'protocols' in patterns:
                for protocol in patterns['protocols'][:2]:
                    if protocol.lower() not in correct_answer.lower():
                        distractors.append(protocol)
        
        return distractors

    def generate_high_quality_distractors(self, correct_answer: str, context: str, num_distractors: int = 3) -> List[str]:
        """Generate high-quality, contextually relevant distractors"""
        
        # Determine domain context
        domain = self.extract_domain_context(context)
        
        all_distractors = []
        
        # Strategy 1: Semantic distractors (most important)
        semantic_distractors = self.generate_semantic_distractors(correct_answer, context, domain)
        all_distractors.extend(semantic_distractors)
        
        # Strategy 2: Contextual distractors
        contextual_distractors = self.generate_contextual_distractors(correct_answer, context)
        all_distractors.extend(contextual_distractors)
        
        # Strategy 3: Synthetic distractors (fallback)
        if len(all_distractors) < num_distractors:
            synthetic_distractors = self.generate_synthetic_distractors(correct_answer, domain)
            all_distractors.extend(synthetic_distractors)
        
        # Remove duplicates and filter quality
        unique_distractors = []
        seen = set()
        
        for distractor in all_distractors:
            if (distractor and 
                distractor.lower() not in seen and 
                distractor.lower() != correct_answer.lower() and
                self.min_distractor_length <= len(distractor) <= self.max_distractor_length and
                not self._is_nonsensical(distractor)):
                
                unique_distractors.append(distractor.strip())
                seen.add(distractor.lower())
        
        # If still not enough, generate generic but sensible distractors
        while len(unique_distractors) < num_distractors:
            generic_distractor = self._generate_sensible_generic(correct_answer, unique_distractors, domain)
            if generic_distractor:
                unique_distractors.append(generic_distractor)
            else:
                break
        
        return unique_distractors[:num_distractors]

    def _is_nonsensical(self, distractor: str) -> bool:
        """Check if a distractor is nonsensical or low quality"""
        distractor = distractor.strip()
        
        # Check for common nonsensical patterns
        nonsensical_patterns = [
            r'^[A-Z]\d*$',  # Single letter with optional numbers
            r'^\d+$',       # Just numbers
            r'^[^\w\s]+$',  # Just punctuation
            r'^.{1,2}$',    # Too short
        ]
        
        for pattern in nonsensical_patterns:
            if re.match(pattern, distractor):
                return True
        
        # Check for meaningless fragments
        meaningless_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        if distractor.lower() in meaningless_words:
            return True
        
        # Check for random text fragments (common failure mode)
        if re.match(r'^(?:Figure|Table|Page|Section|Chapter)\s*\d*$', distractor, re.IGNORECASE):
            return True
        
        return False

    def _generate_sensible_generic(self, correct_answer: str, existing: List[str], domain: str) -> str:
        """Generate sensible generic distractors as last resort"""
        
        # Domain-appropriate generic options
        generic_templates = {
            'networking': [
                'Network protocol', 'Data transmission', 'Communication standard', 'Connection method',
                'Network topology', 'Data format', 'Transfer protocol', 'Network service'
            ],
            'programming': [
                'Code structure', 'Program logic', 'Software component', 'Data type',
                'Control flow', 'Program function', 'Code pattern', 'Software method'
            ],
            'computer_science': [
                'Algorithm type', 'Data structure', 'Computational method', 'Processing technique',
                'System approach', 'Analysis method', 'Design pattern', 'Optimization strategy'
            ],
            'technology': [
                'System component', 'Technical process', 'Digital method', 'Technology standard',
                'Implementation approach', 'Service type', 'Platform feature', 'System function'
            ],
            'general': [
                'Alternative method', 'Different approach', 'Other technique', 'Similar concept',
                'Related process', 'Comparable system', 'Equivalent method', 'Parallel approach'
            ]
        }
        
        templates = generic_templates.get(domain, generic_templates['general'])
        
        # Find a template that hasn't been used
        for template in templates:
            if template not in existing and template.lower() != correct_answer.lower():
                return template
        
        # If all templates used, create a variation
        if templates:
            base_template = random.choice(templates)
            variations = [
                f"Advanced {base_template.lower()}",
                f"Modified {base_template.lower()}",
                f"Standard {base_template.lower()}"
            ]
            
            for variation in variations:
                if variation not in existing:
                    return variation.capitalize()
        
        return None

def create_improved_distractor_generator():
    """Factory function to create the improved distractor generator"""
    return ImprovedDistractorGenerator()
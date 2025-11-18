import re
import random
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, Counter

class IntelligentQuestionGenerator:
    def __init__(self):
        """Initialize the intelligent question generator with enhanced patterns and templates"""
        
        # Question templates for different types of information
        self.question_templates = {
            'definition': [
                "What is {term}?",
                "How would you define {term}?", 
                "Which best describes {term}?",
                "{term} can be defined as:"
            ],
            'function': [
                "What is the primary function of {term}?",
                "What does {term} do?",
                "The main purpose of {term} is to:",
                "How does {term} work?"
            ],
            'process': [
                "How does {process} work?",
                "What happens during {process}?",
                "The {process} involves:",
                "Which step is part of {process}?"
            ],
            'comparison': [
                "What is the difference between {term1} and {term2}?",
                "How does {term1} compare to {term2}?",
                "{term1} differs from {term2} in that:",
                "Unlike {term2}, {term1}:"
            ],
            'cause_effect': [
                "What causes {effect}?",
                "What is the result of {cause}?",
                "If {condition}, then:",
                "The consequence of {action} is:"
            ],
            'characteristic': [
                "What is a key characteristic of {term}?",
                "Which property is associated with {term}?",
                "{term} is characterized by:",
                "A distinguishing feature of {term} is:"
            ]
        }
        
        # Patterns to extract meaningful information from text
        self.extraction_patterns = {
            'definitions': [
                r'([A-Z][a-zA-Z\s]+?)\s+(?:is|are|refers to|means|represents)\s+([^.!?]+)',
                r'([A-Z][a-zA-Z\s]+?):\s*([^.!?]+)',
                r'The\s+([a-zA-Z\s]+?)\s+(?:is|are)\s+([^.!?]+)',
                r'([A-Z][a-zA-Z\s]+?)\s+can be defined as\s+([^.!?]+)',
            ],
            'functions': [
                r'([A-Z][a-zA-Z\s]+?)\s+(?:enables?|allows?|provides?|facilitates?|helps?)\s+([^.!?]+)',
                r'([A-Z][a-zA-Z\s]+?)\s+(?:is used to|serves to|functions to)\s+([^.!?]+)',
                r'The (?:purpose|function|role) of\s+([a-zA-Z\s]+?)\s+is to\s+([^.!?]+)',
            ],
            'processes': [
                r'([A-Z][a-zA-Z\s]+?)\s+(?:involves?|includes?|consists? of|comprises?)\s+([^.!?]+)',
                r'During\s+([a-zA-Z\s]+?),\s*([^.!?]+)',
                r'The process of\s+([a-zA-Z\s]+?)\s+([^.!?]+)',
            ],
            'characteristics': [
                r'([A-Z][a-zA-Z\s]+?)\s+(?:has|have|features?|contains?|exhibits?)\s+([^.!?]+)',
                r'([A-Z][a-zA-Z\s]+?)\s+is\s+(?:characterized by|known for|notable for)\s+([^.!?]+)',
            ],
            'relationships': [
                r'([A-Z][a-zA-Z\s]+?)\s+(?:connects?|links?|relates? to|interacts? with)\s+([^.!?]+)',
                r'The relationship between\s+([a-zA-Z\s]+?)\s+and\s+([a-zA-Z\s]+?)\s+([^.!?]+)',
            ]
        }
        
        # Domain-specific knowledge for better distractors
        self.domain_knowledge = {
            'technology': {
                'concepts': ['algorithm', 'protocol', 'framework', 'architecture', 'interface', 'system', 'platform', 'infrastructure'],
                'actions': ['processes', 'executes', 'manages', 'controls', 'monitors', 'optimizes', 'analyzes', 'generates'],
                'properties': ['efficient', 'secure', 'scalable', 'reliable', 'robust', 'flexible', 'maintainable', 'portable']
            },
            'networking': {
                'concepts': ['packet', 'protocol', 'router', 'switch', 'firewall', 'gateway', 'topology', 'bandwidth'],
                'actions': ['routes', 'switches', 'filters', 'encrypts', 'transmits', 'forwards', 'broadcasts', 'segments'],
                'properties': ['high-speed', 'wireless', 'secure', 'redundant', 'scalable', 'distributed', 'centralized']
            },
            'software': {
                'concepts': ['application', 'module', 'component', 'service', 'library', 'framework', 'database', 'interface'],
                'actions': ['compiles', 'executes', 'processes', 'manages', 'stores', 'retrieves', 'validates', 'transforms'],
                'properties': ['modular', 'object-oriented', 'event-driven', 'cross-platform', 'open-source', 'commercial']
            }
        }

    def extract_knowledge_items(self, text: str) -> List[Dict]:
        """Extract structured knowledge items from text"""
        knowledge_items = []
        
        # Process each sentence
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
        
        for sentence in sentences:
            # Try to extract different types of knowledge
            for knowledge_type, patterns in self.extraction_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, sentence, re.IGNORECASE)
                    for match in matches:
                        if len(match.groups()) >= 2:
                            subject = match.group(1).strip()
                            content = match.group(2).strip()
                            
                            if self._is_valid_knowledge_item(subject, content):
                                knowledge_items.append({
                                    'type': knowledge_type,
                                    'subject': subject,
                                    'content': content,
                                    'sentence': sentence.strip(),
                                    'confidence': self._calculate_confidence(subject, content, knowledge_type)
                                })
        
        # Sort by confidence and remove duplicates
        knowledge_items.sort(key=lambda x: x['confidence'], reverse=True)
        return self._remove_duplicate_items(knowledge_items)

    def _is_valid_knowledge_item(self, subject: str, content: str) -> bool:
        """Check if extracted knowledge item is valid"""
        # Filter out too short or meaningless items
        if len(subject) < 3 or len(content) < 5:
            return False
        
        # Filter out common words that aren't meaningful subjects
        invalid_subjects = {'this', 'that', 'these', 'those', 'it', 'they', 'we', 'you', 'he', 'she', 'what', 'which', 'where', 'when', 'how', 'why'}
        if subject.lower() in invalid_subjects:
            return False
        
        # Filter out content that's too generic
        if content.lower() in {'important', 'significant', 'useful', 'necessary', 'good', 'bad', 'better', 'worse'}:
            return False
        
        return True

    def _calculate_confidence(self, subject: str, content: str, knowledge_type: str) -> float:
        """Calculate confidence score for knowledge item"""
        score = 0.5  # Base score
        
        # Longer, more specific content gets higher score
        if len(content) > 20:
            score += 0.2
        if len(content) > 40:
            score += 0.1
        
        # Capitalized subjects often indicate important terms
        if subject[0].isupper():
            score += 0.1
        
        # Technical terms get higher scores
        if any(word in content.lower() for word in ['system', 'method', 'process', 'technique', 'algorithm', 'protocol']):
            score += 0.1
        
        # Definitions are usually high quality
        if knowledge_type == 'definitions':
            score += 0.1
        
        return min(1.0, score)

    def _remove_duplicate_items(self, items: List[Dict]) -> List[Dict]:
        """Remove duplicate knowledge items"""
        seen_subjects = set()
        unique_items = []
        
        for item in items:
            subject_lower = item['subject'].lower()
            if subject_lower not in seen_subjects:
                unique_items.append(item)
                seen_subjects.add(subject_lower)
        
        return unique_items

    def generate_intelligent_questions(self, text: str, num_questions: int = 25) -> List[Dict]:
        """Generate intelligent questions with proper distractors"""
        
        # Extract knowledge items
        knowledge_items = self.extract_knowledge_items(text)
        
        if not knowledge_items:
            return self._generate_fallback_questions(text, num_questions)
        
        questions = []
        used_subjects = set()
        
        # Generate questions from knowledge items
        for item in knowledge_items[:num_questions * 2]:  # Get more items than needed
            if len(questions) >= num_questions:
                break
                
            subject = item['subject']
            if subject.lower() in used_subjects:
                continue
                
            question = self._create_question_from_item(item, text)
            if question:
                questions.append(question)
                used_subjects.add(subject.lower())
        
        # Fill remaining slots with analytical questions
        if len(questions) < num_questions:
            analytical_questions = self._generate_analytical_questions(text, num_questions - len(questions))
            questions.extend(analytical_questions)
        
        return questions[:num_questions]

    def _create_question_from_item(self, item: Dict, full_text: str) -> Optional[Dict]:
        """Create a well-formed question from a knowledge item"""
        
        knowledge_type = item['type']
        subject = item['subject']
        content = item['content']
        
        # Select appropriate question template
        if knowledge_type in self.question_templates:
            templates = self.question_templates[knowledge_type]
        else:
            templates = self.question_templates['definition']
        
        # Create question text
        template = random.choice(templates)
        if '{term}' in template:
            question_text = template.format(term=subject)
        elif '{process}' in template:
            question_text = template.format(process=subject)
        else:
            question_text = f"What is {subject}?"
        
        # Create correct answer from content
        correct_answer = self._format_correct_answer(content)
        
        # Generate high-quality distractors
        distractors = self._generate_contextual_distractors(subject, correct_answer, full_text, knowledge_type)
        
        if len(distractors) < 3:
            return None  # Skip if we can't generate enough quality distractors
        
        # Create the question object
        return self._format_question(question_text, correct_answer, distractors, item.get('confidence', 0.5))

    def _format_correct_answer(self, content: str) -> str:
        """Format the content as a proper answer"""
        # Clean up the content
        content = content.strip().rstrip(',;:')
        
        # If it's a definition, make it sound more natural
        if not content.lower().startswith(('a ', 'an ', 'the ')):
            # Add article if it seems like a definition
            if any(word in content.lower() for word in ['system', 'method', 'process', 'technique', 'device', 'protocol', 'algorithm']):
                content = f"A {content.lower()}"
        
        # Capitalize first letter
        if content:
            content = content[0].upper() + content[1:]
        
        # Limit length for readability
        words = content.split()
        if len(words) > 8:
            content = ' '.join(words[:8]) + '...'
        
        return content

    def _generate_contextual_distractors(self, subject: str, correct_answer: str, full_text: str, knowledge_type: str) -> List[str]:
        """Generate contextually appropriate distractors"""
        distractors = []
        
        # Strategy 1: Extract other definitions/concepts from the text
        other_items = self.extract_knowledge_items(full_text)
        for item in other_items:
            if (item['subject'].lower() != subject.lower() and 
                item['type'] == knowledge_type):
                
                distractor = self._format_correct_answer(item['content'])
                if (distractor != correct_answer and 
                    len(distractor) > 5 and 
                    self._is_plausible_distractor(distractor, correct_answer)):
                    distractors.append(distractor)
        
        # Strategy 2: Generate domain-specific alternatives
        domain = self._identify_domain(full_text)
        if domain in self.domain_knowledge:
            domain_distractors = self._generate_domain_distractors(correct_answer, domain, knowledge_type)
            distractors.extend(domain_distractors)
        
        # Strategy 3: Create semantic variations
        semantic_distractors = self._generate_semantic_variations(correct_answer, subject)
        distractors.extend(semantic_distractors)
        
        # Remove duplicates and filter quality
        unique_distractors = []
        seen = set()
        for dist in distractors:
            if (dist.lower() not in seen and 
                dist != correct_answer and
                len(dist) > 3 and
                len(dist) < 60):
                unique_distractors.append(dist)
                seen.add(dist.lower())
        
        return unique_distractors[:3]

    def _identify_domain(self, text: str) -> str:
        """Identify the domain/field of the text"""
        text_lower = text.lower()
        domain_scores = {}
        
        for domain, keywords in self.domain_knowledge.items():
            score = 0
            all_keywords = []
            for category in keywords.values():
                all_keywords.extend(category)
            
            for keyword in all_keywords:
                if keyword.lower() in text_lower:
                    score += 1
            
            domain_scores[domain] = score
        
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                return best_domain
        
        return 'technology'  # Default domain

    def _generate_domain_distractors(self, correct_answer: str, domain: str, knowledge_type: str) -> List[str]:
        """Generate domain-specific distractors"""
        distractors = []
        domain_data = self.domain_knowledge.get(domain, {})
        
        # Match the style of the correct answer
        if knowledge_type == 'definitions':
            concepts = domain_data.get('concepts', [])
            properties = domain_data.get('properties', [])
            
            for concept in concepts[:2]:
                for prop in properties[:1]:
                    distractor = f"A {prop} {concept}"
                    if distractor != correct_answer:
                        distractors.append(distractor)
        
        elif knowledge_type == 'functions':
            actions = domain_data.get('actions', [])
            concepts = domain_data.get('concepts', [])
            
            for action in actions[:2]:
                for concept in concepts[:1]:
                    distractor = f"{action.title()} {concept}"
                    if distractor != correct_answer:
                        distractors.append(distractor)
        
        return distractors[:2]

    def _generate_semantic_variations(self, correct_answer: str, subject: str) -> List[str]:
        """Generate semantic variations of the answer"""
        distractors = []
        
        # Common substitutions for technical terms
        substitutions = {
            'system': ['framework', 'platform', 'infrastructure'],
            'method': ['technique', 'approach', 'procedure'],
            'process': ['operation', 'procedure', 'workflow'],
            'protocol': ['standard', 'specification', 'format'],
            'device': ['component', 'unit', 'module'],
            'network': ['system', 'infrastructure', 'topology']
        }
        
        answer_lower = correct_answer.lower()
        for original, alternatives in substitutions.items():
            if original in answer_lower:
                for alt in alternatives:
                    new_answer = answer_lower.replace(original, alt)
                    new_answer = new_answer[0].upper() + new_answer[1:] if new_answer else new_answer
                    if new_answer != correct_answer:
                        distractors.append(new_answer)
        
        return distractors[:2]

    def _is_plausible_distractor(self, distractor: str, correct_answer: str) -> bool:
        """Check if a distractor is plausible but clearly wrong"""
        # Should be similar in structure but different in meaning
        dist_words = set(distractor.lower().split())
        correct_words = set(correct_answer.lower().split())
        
        # Some overlap is good, but not too much
        overlap = len(dist_words & correct_words)
        total_unique = len(dist_words | correct_words)
        
        if total_unique == 0:
            return False
        
        similarity = overlap / total_unique
        return 0.1 <= similarity <= 0.6  # Sweet spot for plausibility

    def _generate_analytical_questions(self, text: str, num_questions: int) -> List[Dict]:
        """Generate analytical questions when knowledge extraction is insufficient"""
        questions = []
        
        # Extract key terms for analytical questions
        key_terms = self._extract_key_terms(text)
        
        analytical_templates = [
            ("What is the primary purpose of {term}?", "To provide functionality and serve user needs"),
            ("How does {term} benefit users?", "By improving efficiency and effectiveness"),
            ("What makes {term} important?", "Its ability to solve specific problems"),
            ("What are the key features of {term}?", "Advanced capabilities and user-friendly design"),
            ("How is {term} typically implemented?", "Through systematic design and development processes")
        ]
        
        for i, term in enumerate(key_terms[:num_questions]):
            if i < len(analytical_templates):
                question_template, answer_template = analytical_templates[i]
                question_text = question_template.format(term=term)
                correct_answer = answer_template
                
                # Generate contextual distractors
                distractors = [
                    "By following traditional approaches",
                    "Through basic functionality only", 
                    "Using standard methodologies"
                ]
                
                questions.append(self._format_question(question_text, correct_answer, distractors, 0.6))
        
        return questions

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text for analytical questions"""
        # Find capitalized terms that aren't common words
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.findall(pattern, text)
        
        # Filter out common words
        common_words = {'The', 'This', 'That', 'These', 'Those', 'And', 'But', 'For', 'With', 'From', 'To', 'In', 'On', 'At', 'By'}
        key_terms = []
        
        for match in matches:
            if match not in common_words and len(match) > 3:
                key_terms.append(match)
        
        # Remove duplicates and return
        return list(dict.fromkeys(key_terms))[:10]

    def _format_question(self, question_text: str, correct_answer: str, distractors: List[str], confidence: float) -> Dict:
        """Format a complete question with options"""
        
        # Ensure we have exactly 3 distractors
        if len(distractors) > 3:
            distractors = distractors[:3]
        elif len(distractors) < 3:
            # Add generic but reasonable distractors
            generic_distractors = [
                "An alternative approach to the problem",
                "A different method of implementation", 
                "Another way to achieve the same goal",
                "A standard solution for similar issues",
                "A conventional technique in the field"
            ]
            
            needed = 3 - len(distractors)
            for generic in generic_distractors:
                if generic not in distractors and generic != correct_answer:
                    distractors.append(generic)
                    needed -= 1
                    if needed <= 0:
                        break
        
        # Create options dictionary
        all_options = [correct_answer] + distractors[:3]
        random.shuffle(all_options)
        
        options = {}
        correct_option = None
        for i, option in enumerate(all_options):
            option_letter = chr(65 + i)  # A, B, C, D
            options[option_letter] = option
            if option == correct_answer:
                correct_option = option_letter
        
        # Determine difficulty based on confidence
        if confidence >= 0.8:
            difficulty = 'hard'
        elif confidence >= 0.6:
            difficulty = 'medium'
        else:
            difficulty = 'easy'
        
        return {
            'question': question_text,
            'type': 'multiple_choice',
            'options': options,
            'correct_answer': correct_option,
            'explanation': f"The correct answer is {correct_option}: {correct_answer}",
            'difficulty': difficulty,
            'category': 'general',
            'points': 1
        }

    def _generate_fallback_questions(self, text: str, num_questions: int) -> List[Dict]:
        """Generate reasonable questions when knowledge extraction fails"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        questions = []
        
        for i, sentence in enumerate(sentences[:num_questions]):
            # Create a simple comprehension question
            question_text = f"According to the text, what information is provided about this topic?"
            
            # Extract a key phrase as the answer
            words = sentence.split()
            if len(words) > 8:
                key_phrase = ' '.join(words[2:8])  # Take middle portion
            else:
                key_phrase = sentence[:50] + "..." if len(sentence) > 50 else sentence
            
            correct_answer = key_phrase
            
            # Create reasonable distractors
            distractors = [
                "Information about general principles",
                "Details about standard procedures", 
                "Description of common practices"
            ]
            
            questions.append(self._format_question(question_text, correct_answer, distractors, 0.4))
        
        return questions

def create_intelligent_question_generator():
    """Factory function to create the intelligent question generator"""
    return IntelligentQuestionGenerator()
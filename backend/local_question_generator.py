"""
Local Question Generation Module
Generates intelligent questions directly from content without external APIs
"""

import re
import random
from typing import List, Dict, Any


class LocalQuestionGenerator:
    """Generate questions directly from content using NLP patterns"""
    
    def __init__(self):
        self.question_templates = {
            'definition': [
                "What is {}?",
                "How would you define {}?",
                "What does {} mean?",
                "What is meant by {}?"
            ],
            'purpose': [
                "What is the purpose of {}?", 
                "Why is {} important?",
                "What is {} used for?",
                "What does {} achieve?"
            ],
            'function': [
                "How does {} work?",
                "What does {} do?",
                "How is {} implemented?",
                "What is the function of {}?"
            ],
            'comparison': [
                "What is the difference between {} and {}?",
                "How does {} compare to {}?",
                "What are the advantages of {} over {}?"
            ],
            'process': [
                "How is {} accomplished?",
                "What is the process of {}?", 
                "What steps are involved in {}?"
            ]
        }
        
    def extract_key_concepts(self, text: str) -> List[Dict[str, str]]:
        """Extract key concepts and their definitions from text"""
        concepts = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        # Pattern 1: "X is Y" definitions
        for sentence in sentences:
            pattern = r'([A-Z][a-zA-Z\s]{2,30}?)\s+(?:is|are)\s+([^,.!?]{10,100})'
            matches = re.finditer(pattern, sentence)
            for match in matches:
                concept = match.group(1).strip()
                definition = match.group(2).strip()
                concepts.append({
                    'concept': concept,
                    'definition': definition,
                    'type': 'definition'
                })
        
        # Pattern 2: "X provides/enables/allows Y"
        for sentence in sentences:
            pattern = r'([A-Z][a-zA-Z\s]{2,30}?)\s+(?:provides?|enables?|allows?)\s+([^,.!?]{5,80})'
            matches = re.finditer(pattern, sentence)
            for match in matches:
                concept = match.group(1).strip() 
                function = match.group(2).strip()
                concepts.append({
                    'concept': concept,
                    'function': function,
                    'type': 'function'
                })
        
        # Pattern 3: Technical terms (capitalized words)
        words = text.split()
        tech_terms = []
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if (len(clean_word) > 3 and 
                clean_word[0].isupper() and
                clean_word.lower() not in ['The', 'This', 'That', 'These', 'Those', 'When', 'Where', 'What', 'Which', 'How', 'Why', 'Who']):
                tech_terms.append(clean_word)
        
        # Add tech terms with context
        for term in set(tech_terms):
            # Find sentence containing the term for context
            for sentence in sentences:
                if term in sentence:
                    concepts.append({
                        'concept': term,
                        'context': sentence,
                        'type': 'term'
                    })
                    break
        
        return concepts
    
    def generate_mcq_from_concepts(self, concepts: List[Dict], num_questions: int = 10) -> List[Dict]:
        """Generate multiple choice questions from extracted concepts"""
        questions = []
        
        for concept_data in concepts[:num_questions]:
            concept = concept_data['concept']
            concept_type = concept_data['type']
            
            # Choose appropriate question template
            if concept_type == 'definition' and 'definition' in concept_data:
                question_text = random.choice(self.question_templates['definition']).format(concept.lower())
                correct_answer = concept_data['definition']
            elif concept_type == 'function' and 'function' in concept_data:
                question_text = random.choice(self.question_templates['function']).format(concept.lower())
                correct_answer = concept_data['function']
            else:
                question_text = random.choice(self.question_templates['definition']).format(concept.lower())
                correct_answer = concept
            
            # Generate distractors
            distractors = self.generate_smart_distractors(correct_answer, concepts, concept_data)
            
            # Create options
            options = [correct_answer] + distractors[:3]
            random.shuffle(options)
            
            # Find correct answer position
            correct_position = chr(65 + options.index(correct_answer))  # A, B, C, D
            
            # Format options as dict
            option_dict = {}
            for i, option in enumerate(options):
                option_dict[chr(65 + i)] = option[:100]  # Limit length
            
            questions.append({
                'question': question_text,
                'type': 'multiple_choice',
                'correct_answer': correct_position,
                'options': option_dict,
                'explanation': f"The correct answer is '{correct_answer}'",
                'difficulty': self.assess_difficulty(question_text, correct_answer),
                'category': self.categorize_content(concept),
                'points': 1
            })
        
        return questions
    
    def generate_smart_distractors(self, correct_answer: str, all_concepts: List[Dict], current_concept: Dict) -> List[str]:
        """Generate intelligent distractors based on context"""
        distractors = []
        
        # Type 1: Use other concept definitions/functions
        for concept_data in all_concepts:
            if concept_data != current_concept:
                if 'definition' in concept_data:
                    distractor = concept_data['definition'][:50]  # Truncate
                    if distractor.lower() != correct_answer.lower() and len(distractor) > 3:
                        distractors.append(distractor)
                elif 'function' in concept_data:
                    distractor = concept_data['function'][:50]
                    if distractor.lower() != correct_answer.lower() and len(distractor) > 3:
                        distractors.append(distractor)
        
        # Type 2: Modify correct answer slightly
        if len(correct_answer.split()) > 2:
            words = correct_answer.split()
            # Remove first word
            distractor = ' '.join(words[1:])
            if len(distractor) > 3:
                distractors.append(distractor)
            
            # Remove last word
            distractor = ' '.join(words[:-1])
            if len(distractor) > 3:
                distractors.append(distractor)
        
        # Type 3: Generic but plausible distractors
        generic_distractors = [
            "A method for processing information",
            "A type of communication protocol", 
            "A form of data storage",
            "A network security feature",
            "A software application",
            "A hardware component",
            "A programming technique",
            "A system architecture"
        ]
        
        # Add generic distractors if needed
        for distractor in generic_distractors:
            if distractor.lower() != correct_answer.lower():
                distractors.append(distractor)
        
        # Remove duplicates and return best ones
        unique_distractors = list(set(distractors))
        return unique_distractors[:6]  # Return up to 6 for selection
    
    def assess_difficulty(self, question: str, answer: str) -> str:
        """Assess question difficulty based on complexity"""
        # Simple heuristic based on length and complexity
        total_length = len(question) + len(answer)
        word_count = len(question.split()) + len(answer.split())
        
        if total_length < 50 or word_count < 8:
            return 'easy'
        elif total_length < 120 or word_count < 15:
            return 'medium' 
        else:
            return 'hard'
    
    def categorize_content(self, concept: str) -> str:
        """Categorize content based on concept keywords"""
        concept_lower = concept.lower()
        
        if any(word in concept_lower for word in ['network', 'protocol', 'router', 'ethernet', 'tcp', 'ip']):
            return 'networking'
        elif any(word in concept_lower for word in ['computer', 'system', 'software', 'hardware']):
            return 'computer systems'
        elif any(word in concept_lower for word in ['security', 'firewall', 'encryption', 'authentication']):
            return 'security'
        elif any(word in concept_lower for word in ['data', 'information', 'database']):
            return 'data management'
        else:
            return 'general'
    
    def generate_questions_from_text(self, text: str, num_questions: int = 10, question_type: str = 'multiple_choice') -> List[Dict]:
        """Main method to generate questions from text"""
        concepts = self.extract_key_concepts(text)
        
        if question_type == 'multiple_choice':
            return self.generate_mcq_from_concepts(concepts, num_questions)
        elif question_type == 'true_false':
            return self.generate_true_false(concepts, num_questions)
        else:
            return self.generate_mcq_from_concepts(concepts, num_questions)
    
    def generate_true_false(self, concepts: List[Dict], num_questions: int) -> List[Dict]:
        """Generate true/false questions"""
        questions = []
        
        for concept_data in concepts[:num_questions]:
            if 'definition' in concept_data:
                # Create true statement
                statement = f"{concept_data['concept']} is {concept_data['definition']}"
                
                questions.append({
                    'question': f"True or False: {statement}",
                    'type': 'true_false',
                    'correct_answer': 'True',
                    'options': ['True', 'False'],
                    'explanation': 'The statement is True',
                    'difficulty': 'easy',
                    'category': self.categorize_content(concept_data['concept']),
                    'points': 1
                })
        
        return questions


def create_local_question_generator():
    """Factory function to create local question generator"""
    return LocalQuestionGenerator()
import re
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_IN_BLANK = "fill_in_blank"
    SHORT_ANSWER = "short_answer"
    MATCHING = "matching"

class DifficultyLevel(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

@dataclass
class Question:
    question_type: QuestionType
    question_text: str
    correct_answer: Any
    options: Optional[List[str]] = None
    distractors: Optional[List[str]] = None
    explanation: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None
    category: Optional[str] = None
    points: int = 1

class QuestionGenerator:
    def __init__(self):
        self.patterns = {
            'definition': [
                r'(\w+(?:\s+\w+)*)\s+is\s+defined\s+as\s+(.*?)[\.\n]',
                r'(\w+(?:\s+\w+)*)\s+refers\s+to\s+(.*?)[\.\n]',
                r'(\w+(?:\s+\w+)*)\s+means\s+(.*?)[\.\n]',
                r'The\s+term\s+(\w+(?:\s+\w+)*)\s+describes\s+(.*?)[\.\n]'
            ],
            'process': [
                r'The\s+process\s+of\s+(\w+(?:\s+\w+)*)\s+involves\s+(.*?)[\.\n]',
                r'(\w+(?:\s+\w+)*)\s+occurs\s+when\s+(.*?)[\.\n]',
                r'During\s+(\w+(?:\s+\w+)*),\s+(.*?)[\.\n]'
            ],
            'comparison': [
                r'(\w+(?:\s+\w+)*)\s+(?:is|are)\s+(?:different\s+from|similar\s+to|unlike|like)\s+(\w+(?:\s+\w+)*)(?:\s+because\s+(.*?))?[\.\n]',
                r'Unlike\s+(\w+(?:\s+\w+)*),\s+(\w+(?:\s+\w+)*)\s+(.*?)[\.\n]'
            ],
            'causation': [
                r'(\w+(?:\s+\w+)*)\s+(?:causes|leads\s+to|results\s+in)\s+(\w+(?:\s+\w+)*)[\.\n]',
                r'(\w+(?:\s+\w+)*)\s+is\s+caused\s+by\s+(\w+(?:\s+\w+)*)[\.\n]'
            ],
            'numerical': [
                r'(\d+(?:\.\d+)?(?:%|\s*percent))',
                r'(\d+(?:,\d{3})*(?:\.\d+)?)',
                r'(\d+(?:\s+(?:million|billion|thousand)))'
            ]
        }

    def generate_multiple_choice(self, text: str, correct_answer: str, distractors: List[str]) -> Question:
        """Generate a multiple choice question"""
        options = [correct_answer] + distractors[:3]  # Limit to 4 options total
        random.shuffle(options)
        
        return Question(
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text=text,
            correct_answer=correct_answer,
            options=options,
            explanation=f"The correct answer is '{correct_answer}'"
        )

    def generate_true_false(self, statement: str, is_true: bool, context: str = "") -> Question:
        """Generate a true/false question"""
        # Create variations of the statement
        if not is_true:
            # For false statements, we might need to modify the statement
            modified_statement = self._create_false_statement(statement, context)
            statement = modified_statement if modified_statement else statement
        
        return Question(
            question_type=QuestionType.TRUE_FALSE,
            question_text=f"True or False: {statement}",
            correct_answer=is_true,
            options=["True", "False"],
            explanation=f"The statement is {'True' if is_true else 'False'}"
        )

    def generate_fill_in_blank(self, sentence: str, target_word: str) -> Question:
        """Generate a fill-in-the-blank question"""
        # Replace target word with blank
        question_text = sentence.replace(target_word, "_____", 1)
        
        return Question(
            question_type=QuestionType.FILL_IN_BLANK,
            question_text=f"Fill in the blank: {question_text}",
            correct_answer=target_word,
            explanation=f"The correct answer is '{target_word}'"
        )

    def generate_short_answer(self, question_text: str, answer: str) -> Question:
        """Generate a short answer question"""
        return Question(
            question_type=QuestionType.SHORT_ANSWER,
            question_text=question_text,
            correct_answer=answer,
            explanation=f"Sample answer: {answer}"
        )

    def generate_matching(self, items: List[Dict[str, str]]) -> Question:
        """Generate a matching question"""
        if len(items) < 2:
            raise ValueError("At least 2 items required for matching question")
        
        left_items = [item['left'] for item in items]
        right_items = [item['right'] for item in items]
        
        # Shuffle right items to make it challenging
        shuffled_right = right_items.copy()
        random.shuffle(shuffled_right)
        
        correct_matches = {item['left']: item['right'] for item in items}
        
        return Question(
            question_type=QuestionType.MATCHING,
            question_text="Match the items from the left column with the correct items from the right column:",
            correct_answer=correct_matches,
            options={
                'left': left_items,
                'right': shuffled_right
            },
            explanation="Correct matches provided in answer key"
        )

    def extract_question_candidates(self, text: str) -> List[Dict[str, Any]]:
        """Extract potential question candidates from text using patterns"""
        candidates = []
        
        # Extract definition-based candidates
        for pattern in self.patterns['definition']:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    term, definition = match[0].strip(), match[1].strip()
                    if len(term.split()) <= 3 and len(definition) > 10:  # Quality filters
                        candidates.append({
                            'type': 'definition',
                            'term': term,
                            'definition': definition,
                            'sentence': f"{term} is defined as {definition}"
                        })
        
        # Extract process-based candidates
        for pattern in self.patterns['process']:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    process, description = match[0].strip(), match[1].strip()
                    candidates.append({
                        'type': 'process',
                        'process': process,
                        'description': description,
                        'sentence': f"The process of {process} involves {description}"
                    })
        
        # Extract numerical candidates
        numbers = []
        for pattern in self.patterns['numerical']:
            numbers.extend(re.findall(pattern, text))
        
        for number in numbers[:5]:  # Limit to avoid too many
            candidates.append({
                'type': 'numerical',
                'number': number,
                'context': self._get_context_around_number(text, number)
            })
        
        return candidates

    def _create_false_statement(self, statement: str, context: str) -> str:
        """Create a false version of a true statement"""
        # Simple negation strategies
        negation_words = ['not', 'never', 'cannot', 'does not', 'is not', 'are not']
        
        # Add 'not' after 'is' or 'are'
        if ' is ' in statement:
            return statement.replace(' is ', ' is not ', 1)
        elif ' are ' in statement:
            return statement.replace(' are ', ' are not ', 1)
        elif statement.startswith('The'):
            return statement.replace('The ', 'The opposite of the ', 1)
        
        return f"It is false that {statement.lower()}"

    def _get_context_around_number(self, text: str, number: str) -> str:
        """Get context around a number for better question generation"""
        # Find the number in text and extract surrounding context
        index = text.find(number)
        if index == -1:
            return ""
        
        start = max(0, index - 50)
        end = min(len(text), index + len(number) + 50)
        
        return text[start:end].strip()

    def classify_difficulty(self, question: Question, context: str = "") -> DifficultyLevel:
        """Classify question difficulty based on various metrics"""
        score = 0
        
        # Length complexity
        if len(question.question_text.split()) > 20:
            score += 2
        elif len(question.question_text.split()) > 10:
            score += 1
        
        # Question type complexity
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            score += 1
        elif question.question_type == QuestionType.MATCHING:
            score += 2
        elif question.question_type == QuestionType.SHORT_ANSWER:
            score += 3
        
        # Content complexity (simple heuristics)
        complex_words = ['analyze', 'evaluate', 'synthesize', 'compare', 'contrast', 'justify', 'critique']
        if any(word in question.question_text.lower() for word in complex_words):
            score += 2
        
        # Bloom's taxonomy indicators
        if any(word in question.question_text.lower() for word in ['what', 'when', 'where', 'who']):
            score += 0  # Remember/Understand level
        elif any(word in question.question_text.lower() for word in ['how', 'why', 'explain']):
            score += 1  # Apply/Analyze level
        elif any(word in question.question_text.lower() for word in ['evaluate', 'judge', 'critique']):
            score += 2  # Evaluate/Create level
        
        # Classify based on total score
        if score <= 2:
            return DifficultyLevel.EASY
        elif score <= 4:
            return DifficultyLevel.MEDIUM
        else:
            return DifficultyLevel.HARD

    def categorize_question(self, question: Question, context: str = "") -> str:
        """Categorize question by subject area or topic"""
        # Simple keyword-based categorization
        categories = {
            'science': ['experiment', 'hypothesis', 'theory', 'research', 'data', 'analysis', 'biology', 'chemistry', 'physics'],
            'history': ['century', 'war', 'revolution', 'empire', 'civilization', 'ancient', 'medieval', 'modern'],
            'mathematics': ['equation', 'formula', 'calculate', 'solve', 'number', 'algebra', 'geometry', 'statistics'],
            'literature': ['author', 'novel', 'poem', 'character', 'plot', 'theme', 'symbolism', 'metaphor'],
            'technology': ['computer', 'software', 'algorithm', 'network', 'database', 'programming', 'digital'],
            'business': ['market', 'profit', 'revenue', 'strategy', 'management', 'economics', 'finance', 'investment']
        }
        
        question_text = question.question_text.lower()
        
        for category, keywords in categories.items():
            if any(keyword in question_text for keyword in keywords):
                return category
        
        return 'general'

def format_question_for_display(question: Question) -> Dict[str, Any]:
    """Format question for frontend display"""
    formatted = {
        'type': question.question_type.value,
        'question': question.question_text,
        'correct_answer': question.correct_answer,
        'explanation': question.explanation,
        'difficulty': question.difficulty.value if question.difficulty else 'medium',
        'category': question.category or 'general',
        'points': question.points
    }
    
    if question.question_type == QuestionType.MULTIPLE_CHOICE:
        # Format MCQ options as A, B, C, D
        if question.options:
            formatted['options'] = {
                chr(65 + i): option for i, option in enumerate(question.options)
            }
            # Find correct answer letter
            try:
                correct_index = question.options.index(question.correct_answer)
                formatted['correct_answer'] = chr(65 + correct_index)
            except ValueError:
                formatted['correct_answer'] = 'A'
    
    elif question.question_type == QuestionType.TRUE_FALSE:
        formatted['options'] = ['True', 'False']
        formatted['correct_answer'] = 'True' if question.correct_answer else 'False'
    
    elif question.question_type == QuestionType.MATCHING:
        formatted['left_items'] = question.options.get('left', [])
        formatted['right_items'] = question.options.get('right', [])
    
    return formatted
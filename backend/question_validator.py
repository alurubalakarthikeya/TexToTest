"""
Question Quality Validation Module
Provides comprehensive validation of generated questions using NLP metrics and grammar checking.
"""

import re
import string
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.tag import pos_tag
    from nltk.chunk import ne_chunk
    from nltk.tree import Tree
    
    # Test if NLTK data is accessible before marking as available
    try:
        # Test basic functionality without downloading
        word_tokenize("Test sentence.")
        sent_tokenize("Test sentence.")
        stopwords.words('english')[:5]
        pos_tag(['test'])
        NLTK_AVAILABLE = True
    except Exception as nltk_error:
        print(f"NLTK data not accessible: {nltk_error}")
        NLTK_AVAILABLE = False
                
except (ImportError, Exception) as e:
    print(f"NLTK not available: {e}")
    NLTK_AVAILABLE = False

try:
    from textstat import flesch_reading_ease, flesch_kincaid_grade, automated_readability_index
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    print("Warning: textstat not installed. Readability analysis not available.")

class ValidationSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationIssue:
    severity: ValidationSeverity
    category: str
    message: str
    suggestion: Optional[str] = None
    location: Optional[str] = None

@dataclass
class QuestionQualityScore:
    overall_score: float  # 0-100
    grammar_score: float
    clarity_score: float
    difficulty_consistency: float
    educational_value: float
    distractor_quality: float
    issues: List[ValidationIssue]
    suggestions: List[str]

class QuestionValidator:
    """Comprehensive question quality validation system"""
    
    def __init__(self):
        self.setup_logging()
        self.setup_validation_rules()
        
        # Load stopwords if NLTK is available
        if NLTK_AVAILABLE:
            try:
                self.stop_words = set(stopwords.words('english'))
            except Exception as e:
                print(f"Warning: Could not load stopwords: {e}")
                self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
        else:
            self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])

    def setup_logging(self):
        """Setup logging for validation"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def setup_validation_rules(self):
        """Initialize validation rules and patterns"""
        
        # Grammar patterns to detect common issues
        self.grammar_issues = [
            (r'\b(a)\s+[aeiouAEIOU]', 'Use "an" before words starting with vowels'),
            (r'\b(an)\s+[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]', 'Use "a" before words starting with consonants'),
            (r'\?\?+|\!\!+', 'Avoid multiple punctuation marks'),
            (r'\s{2,}', 'Remove extra spaces'),
            (r'[.]{3,}', 'Use proper ellipsis (...)'),
            (r'\b(it\'s|its)\b', 'Check if you mean "it is" (it\'s) or possessive (its)'),
        ]
        
        # Question quality patterns
        self.quality_patterns = {
            'ambiguous_pronouns': r'\b(this|that|these|those|it|they)\b(?!\s+(?:is|are|was|were)\s+(?:a|an|the|\w+))',
            'vague_terms': r'\b(thing|stuff|something|anything|everything|nothing|some|many|few|several)\b',
            'absolute_terms': r'\b(always|never|all|none|every|any|only|just|must|cannot|impossible)\b',
            'leading_questions': r'\b(obviously|clearly|of course|naturally|certainly|definitely)\b',
            'double_negative': r'\b(not\s+(?:un|in|im|il|ir|dis|mis|non)|\w*n\'t\s+(?:un|in|im|il|ir|dis|mis|non))',
            'complex_sentence': r'^[^.!?]*[.!?]\s*[^.!?]*[.!?]',  # Multiple sentences in question
        }
        
        # Educational quality indicators
        self.educational_keywords = {
            'blooms_remember': ['define', 'identify', 'list', 'name', 'recall', 'recognize', 'select', 'state'],
            'blooms_understand': ['describe', 'explain', 'interpret', 'summarize', 'classify', 'compare', 'contrast'],
            'blooms_apply': ['apply', 'demonstrate', 'solve', 'use', 'implement', 'execute', 'carry out'],
            'blooms_analyze': ['analyze', 'categorize', 'examine', 'investigate', 'distinguish', 'differentiate'],
            'blooms_evaluate': ['evaluate', 'judge', 'critique', 'assess', 'rate', 'validate', 'justify'],
            'blooms_create': ['create', 'design', 'generate', 'compose', 'plan', 'construct', 'develop']
        }
        
        # Distractor quality indicators
        self.distractor_issues = [
            'too_similar_to_correct',
            'obviously_wrong',
            'grammatically_inconsistent',
            'length_disparity',
            'semantic_implausibility'
        ]

    def validate_question(self, question_data: Dict[str, Any]) -> QuestionQualityScore:
        """
        Validate a single question and return comprehensive quality assessment
        
        Args:
            question_data: Dictionary containing question information
            
        Returns:
            QuestionQualityScore with detailed analysis
        """
        issues = []
        suggestions = []
        
        question_text = question_data.get('question', '')
        question_type = question_data.get('type', 'multiple_choice')
        correct_answer = question_data.get('correct_answer', '')
        options = question_data.get('options', {})
        
        # Grammar validation
        grammar_score, grammar_issues = self._validate_grammar(question_text)
        issues.extend(grammar_issues)
        
        # Clarity validation
        clarity_score, clarity_issues = self._validate_clarity(question_text, question_type)
        issues.extend(clarity_issues)
        
        # Educational value assessment
        educational_score, edu_suggestions = self._assess_educational_value(question_text, question_type)
        suggestions.extend(edu_suggestions)
        
        # Distractor quality (for MCQ)
        distractor_score = 100.0  # Default for non-MCQ
        if question_type == 'multiple_choice' and options:
            distractor_score, distractor_issues = self._validate_distractors(
                correct_answer, options, question_text
            )
            issues.extend(distractor_issues)
        
        # Difficulty consistency check
        difficulty_score = self._check_difficulty_consistency(question_data)
        
        # Calculate overall score
        overall_score = (
            grammar_score * 0.25 +
            clarity_score * 0.25 +
            educational_score * 0.25 +
            distractor_score * 0.15 +
            difficulty_score * 0.10
        )
        
        # Add general suggestions based on scores
        if overall_score < 70:
            suggestions.append("Consider revising this question to improve overall quality")
        if grammar_score < 80:
            suggestions.append("Review grammar and sentence structure")
        if clarity_score < 70:
            suggestions.append("Simplify language and improve clarity")
        if educational_score < 60:
            suggestions.append("Enhance educational value with more specific learning objectives")
        
        return QuestionQualityScore(
            overall_score=round(overall_score, 1),
            grammar_score=round(grammar_score, 1),
            clarity_score=round(clarity_score, 1),
            difficulty_consistency=round(difficulty_score, 1),
            educational_value=round(educational_score, 1),
            distractor_quality=round(distractor_score, 1),
            issues=issues,
            suggestions=suggestions
        )

    def _validate_grammar(self, text: str) -> Tuple[float, List[ValidationIssue]]:
        """Validate grammar and detect common issues"""
        issues = []
        score = 100.0
        
        # Check basic grammar patterns
        for pattern, message in self.grammar_issues:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="Grammar",
                    message=message,
                    location=f"Position {match.start()}-{match.end()}"
                ))
                score -= 5
        
        # Check sentence structure
        if not text.strip().endswith('?'):
            if 'true or false' not in text.lower() and 'fill in the blank' not in text.lower():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="Grammar",
                    message="Question should end with a question mark",
                    suggestion="Add '?' at the end of the question"
                ))
                score -= 10
        
        # Check capitalization
        if text and not text[0].isupper():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Grammar",
                message="Question should start with a capital letter",
                suggestion="Capitalize the first word"
            ))
            score -= 5
        
        # Use NLTK for advanced grammar checking if available
        if NLTK_AVAILABLE:
            try:
                grammar_score_nltk = self._nltk_grammar_check(text)
                score = (score + grammar_score_nltk) / 2
            except Exception as e:
                self.logger.warning(f"NLTK grammar check failed: {e}")
        
        return max(score, 0), issues

    def _nltk_grammar_check(self, text: str) -> float:
        """Use NLTK for advanced grammar analysis"""
        try:
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            
            score = 100.0
            
            # Check for proper sentence structure
            has_verb = any(tag.startswith('VB') for word, tag in pos_tags)
            has_noun = any(tag.startswith('NN') for word, tag in pos_tags)
            
            if not has_verb:
                score -= 20
            if not has_noun:
                score -= 15
            
            # Check for balanced sentence structure
            verb_count = sum(1 for word, tag in pos_tags if tag.startswith('VB'))
            noun_count = sum(1 for word, tag in pos_tags if tag.startswith('NN'))
            
            # Ideal ratio is roughly 1:2 to 1:3 (verbs:nouns)
            if noun_count > 0:
                ratio = verb_count / noun_count
                if ratio < 0.2 or ratio > 1.0:
                    score -= 10
            
            return max(score, 0)
            
        except Exception as e:
            self.logger.warning(f"NLTK grammar analysis failed: {e}")
            return 80.0  # Default score if analysis fails

    def _validate_clarity(self, text: str, question_type: str) -> Tuple[float, List[ValidationIssue]]:
        """Validate question clarity and readability"""
        issues = []
        score = 100.0
        
        # Check for ambiguous language
        for pattern_name, pattern in self.quality_patterns.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                severity = ValidationSeverity.WARNING
                if pattern_name in ['ambiguous_pronouns', 'double_negative']:
                    severity = ValidationSeverity.CRITICAL
                    score -= 15
                else:
                    score -= 8
                
                issues.append(ValidationIssue(
                    severity=severity,
                    category="Clarity",
                    message=f"Detected {pattern_name.replace('_', ' ')}: {matches[0].group()}",
                    suggestion=self._get_clarity_suggestion(pattern_name)
                ))
        
        # Check readability if textstat is available
        if TEXTSTAT_AVAILABLE:
            try:
                readability_score = flesch_reading_ease(text)
                grade_level = flesch_kincaid_grade(text)
                
                # Ideal range for educational content is 60-80 (fairly easy to standard)
                if readability_score < 30:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="Clarity",
                        message="Text may be too difficult to read",
                        suggestion="Simplify vocabulary and sentence structure"
                    ))
                    score -= 10
                elif readability_score > 90:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category="Clarity",
                        message="Text may be too simple for the target audience",
                        suggestion="Consider using more precise academic vocabulary"
                    ))
                    score -= 5
                
                # Check grade level appropriateness
                if grade_level > 16:
                    score -= 15
                elif grade_level > 12:
                    score -= 10
                    
            except Exception as e:
                self.logger.warning(f"Readability analysis failed: {e}")
        
        # Check question length
        word_count = len(text.split())
        if word_count > 50:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Clarity",
                message="Question may be too long",
                suggestion="Consider breaking into shorter, more focused questions"
            ))
            score -= 10
        elif word_count < 5:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Clarity",
                message="Question may be too short or unclear",
                suggestion="Provide more context or detail"
            ))
            score -= 10
        
        return max(score, 0), issues

    def _get_clarity_suggestion(self, pattern_name: str) -> str:
        """Get specific suggestions for clarity issues"""
        suggestions = {
            'ambiguous_pronouns': 'Replace pronouns with specific nouns',
            'vague_terms': 'Use specific, concrete terms instead',
            'absolute_terms': 'Consider using more qualified language',
            'leading_questions': 'Remove biased language that leads to specific answers',
            'double_negative': 'Rephrase using positive language',
            'complex_sentence': 'Break into simpler sentences or clauses'
        }
        return suggestions.get(pattern_name, 'Review and clarify the language used')

    def _assess_educational_value(self, text: str, question_type: str) -> Tuple[float, List[str]]:
        """Assess the educational value of the question"""
        score = 70.0  # Base score
        suggestions = []
        
        text_lower = text.lower()
        
        # Identify Bloom's taxonomy level
        bloom_level = None
        highest_level = 0
        
        # Map Bloom's levels to numbers
        bloom_levels = {
            'blooms_remember': 1,
            'blooms_understand': 2, 
            'blooms_apply': 3,
            'blooms_analyze': 4,
            'blooms_evaluate': 5,
            'blooms_create': 6
        }
        
        for level, keywords in self.educational_keywords.items():
            level_num = bloom_levels.get(level, 1)
            if any(keyword in text_lower for keyword in keywords):
                if level_num > highest_level:
                    highest_level = level_num
                    bloom_level = level
        
        # Score based on Bloom's level
        if bloom_level:
            bloom_scores = {
                'blooms_remember': 60,
                'blooms_understand': 70,
                'blooms_apply': 80,
                'blooms_analyze': 90,
                'blooms_evaluate': 95,
                'blooms_create': 100
            }
            score = bloom_scores.get(bloom_level, 70)
        else:
            suggestions.append("Consider using action verbs that clearly indicate the learning objective")
            score -= 10
        
        # Check for specific learning indicators
        if any(word in text_lower for word in ['example', 'instance', 'case', 'illustration']):
            score += 5
        
        if any(word in text_lower for word in ['why', 'how', 'explain', 'justify', 'reason']):
            score += 10
        
        # Question type appropriateness
        type_educational_value = {
            'multiple_choice': 70,
            'true_false': 60,
            'fill_in_blank': 75,
            'short_answer': 85,
            'matching': 80,
            'mixed': 80
        }
        
        type_score = type_educational_value.get(question_type, 70)
        score = (score + type_score) / 2
        
        # Additional suggestions based on question type
        if question_type == 'true_false' and score < 80:
            suggestions.append("True/False questions work best for testing factual knowledge or misconceptions")
        
        if question_type == 'multiple_choice' and 'best' in text_lower:
            suggestions.append("'Best answer' questions can be effective for testing judgment and application")
            score += 5
        
        return min(score, 100), suggestions

    def _validate_distractors(self, correct_answer: str, options: Dict[str, str], 
                            question_text: str) -> Tuple[float, List[ValidationIssue]]:
        """Validate quality of distractors in multiple choice questions"""
        issues = []
        score = 100.0
        
        if not options or len(options) < 2:
            return 0, [ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="Distractors",
                message="Multiple choice questions need at least 2 options"
            )]
        
        # Handle both dict and list formats for options
        if isinstance(options, dict):
            distractor_options = [opt for key, opt in options.items() if key != correct_answer]
        elif isinstance(options, list):
            distractor_options = [opt for opt in options if opt != correct_answer]
        else:
            distractor_options = []
        
        if not distractor_options:
            return 0, [ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="Distractors",
                message="No distractors found"
            )]
        
        # Check distractor lengths
        correct_length = len(correct_answer.split())
        distractor_lengths = [len(opt.split()) for opt in distractor_options]
        
        # Length consistency check
        avg_distractor_length = sum(distractor_lengths) / len(distractor_lengths)
        length_ratio = abs(correct_length - avg_distractor_length) / max(correct_length, avg_distractor_length, 1)
        
        if length_ratio > 0.5:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Distractors",
                message="Significant length difference between correct answer and distractors",
                suggestion="Make options similar in length to avoid giving away the answer"
            ))
            score -= 15
        
        # Check for obviously wrong answers
        for distractor in distractor_options:
            if any(word in distractor.lower() for word in ['obviously', 'clearly', 'never', 'always', 'impossible']):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="Distractors",
                    message=f"Distractor may be obviously wrong: '{distractor[:30]}...'",
                    suggestion="Make distractors plausible but incorrect"
                ))
                score -= 10
        
        # Check for grammatical consistency
        correct_starts_with_vowel = correct_answer[0].lower() in 'aeiou'
        
        for distractor in distractor_options:
            distractor_starts_with_vowel = distractor[0].lower() in 'aeiou'
            
            # If question uses "a" or "an", all options should be consistent
            if 'a ' in question_text.lower() or 'an ' in question_text.lower():
                if correct_starts_with_vowel != distractor_starts_with_vowel:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="Distractors",
                        message="Grammatical inconsistency in options (a/an usage)",
                        suggestion="Ensure all options work grammatically with the question stem"
                    ))
                    score -= 8
                    break
        
        # Check for semantic similarity (basic)
        if NLTK_AVAILABLE:
            try:
                # Simple similarity check based on word overlap
                correct_words = set(word_tokenize(correct_answer.lower()))
                
                for distractor in distractor_options:
                    distractor_words = set(word_tokenize(distractor.lower()))
                    overlap = len(correct_words & distractor_words)
                    
                    if overlap > len(correct_words) * 0.7:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            category="Distractors",
                            message=f"Distractor too similar to correct answer: '{distractor[:30]}...'",
                            suggestion="Create more distinct distractors"
                        ))
                        score -= 12
                        
            except Exception as e:
                self.logger.warning(f"Semantic similarity check failed: {e}")
        
        return max(score, 0), issues

    def _check_difficulty_consistency(self, question_data: Dict[str, Any]) -> float:
        """Check if question difficulty matches its classification"""
        stated_difficulty = question_data.get('difficulty', 'medium')
        question_text = question_data.get('question', '')
        question_type = question_data.get('type', 'multiple_choice')
        
        # Calculate estimated difficulty
        estimated_difficulty = self._estimate_difficulty(question_text, question_type)
        
        difficulty_mapping = {'easy': 1, 'medium': 2, 'hard': 3}
        stated_level = difficulty_mapping.get(stated_difficulty, 2)
        estimated_level = difficulty_mapping.get(estimated_difficulty, 2)
        
        # Calculate consistency score
        difference = abs(stated_level - estimated_level)
        consistency_score = max(0, 100 - (difference * 25))
        
        return consistency_score

    def _estimate_difficulty(self, text: str, question_type: str) -> str:
        """Estimate question difficulty based on text analysis"""
        score = 0
        
        # Vocabulary complexity
        words = text.split()
        long_words = [word for word in words if len(word) > 8]
        if len(long_words) / len(words) > 0.3:
            score += 2
        elif len(long_words) / len(words) > 0.15:
            score += 1
        
        # Sentence complexity
        if len(words) > 25:
            score += 2
        elif len(words) > 15:
            score += 1
        
        # Question type complexity
        type_difficulty = {
            'true_false': 0,
            'multiple_choice': 1,
            'fill_in_blank': 1,
            'matching': 2,
            'short_answer': 3
        }
        score += type_difficulty.get(question_type, 1)
        
        # Bloom's taxonomy indicators
        text_lower = text.lower()
        if any(word in text_lower for word in ['analyze', 'evaluate', 'create', 'synthesize']):
            score += 3
        elif any(word in text_lower for word in ['apply', 'compare', 'contrast', 'explain']):
            score += 2
        elif any(word in text_lower for word in ['describe', 'identify', 'summarize']):
            score += 1
        
        # Map score to difficulty
        if score <= 2:
            return 'easy'
        elif score <= 5:
            return 'medium'
        else:
            return 'hard'

    def validate_quiz_batch(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a batch of questions and provide overall assessment"""
        
        individual_scores = []
        all_issues = []
        all_suggestions = []
        
        for i, question in enumerate(questions):
            score = self.validate_question(question)
            individual_scores.append(score)
            
            # Add question number to issues
            for issue in score.issues:
                issue.location = f"Question {i+1}: {issue.location or ''}"
                all_issues.append(issue)
            
            all_suggestions.extend([f"Q{i+1}: {s}" for s in score.suggestions])
        
        # Calculate overall statistics
        if individual_scores:
            avg_overall = sum(s.overall_score for s in individual_scores) / len(individual_scores)
            avg_grammar = sum(s.grammar_score for s in individual_scores) / len(individual_scores)
            avg_clarity = sum(s.clarity_score for s in individual_scores) / len(individual_scores)
            avg_educational = sum(s.educational_value for s in individual_scores) / len(individual_scores)
            
            # Count issues by severity
            critical_count = len([i for i in all_issues if i.severity == ValidationSeverity.CRITICAL])
            warning_count = len([i for i in all_issues if i.severity == ValidationSeverity.WARNING])
            
            # Overall quality assessment
            if avg_overall >= 85:
                quality_rating = "Excellent"
            elif avg_overall >= 75:
                quality_rating = "Good"
            elif avg_overall >= 60:
                quality_rating = "Acceptable"
            else:
                quality_rating = "Needs Improvement"
        
        else:
            avg_overall = avg_grammar = avg_clarity = avg_educational = 0
            critical_count = warning_count = 0
            quality_rating = "No questions to validate"
        
        return {
            'overall_quality_rating': quality_rating,
            'average_scores': {
                'overall': round(avg_overall, 1),
                'grammar': round(avg_grammar, 1),
                'clarity': round(avg_clarity, 1),
                'educational_value': round(avg_educational, 1)
            },
            'issue_summary': {
                'total_issues': len(all_issues),
                'critical_issues': critical_count,
                'warnings': warning_count,
                'info': len(all_issues) - critical_count - warning_count
            },
            'individual_scores': individual_scores,
            'all_issues': all_issues,
            'recommendations': all_suggestions[:20],  # Top 20 recommendations
            'validation_summary': self._generate_validation_summary(individual_scores, all_issues)
        }

    def _generate_validation_summary(self, scores: List[QuestionQualityScore], 
                                   issues: List[ValidationIssue]) -> List[str]:
        """Generate actionable validation summary"""
        summary = []
        
        if not scores:
            return ["No questions to validate"]
        
        avg_score = sum(s.overall_score for s in scores) / len(scores)
        
        # Overall assessment
        if avg_score >= 80:
            summary.append("✅ Quiz quality is good overall")
        else:
            summary.append("⚠️ Quiz quality needs improvement")
        
        # Specific recommendations
        grammar_issues = [i for i in issues if i.category == "Grammar"]
        clarity_issues = [i for i in issues if i.category == "Clarity"]
        distractor_issues = [i for i in issues if i.category == "Distractors"]
        
        if len(grammar_issues) > len(scores) * 0.3:
            summary.append("📝 Focus on improving grammar and sentence structure")
        
        if len(clarity_issues) > len(scores) * 0.3:
            summary.append("🔍 Work on making questions clearer and less ambiguous")
        
        if len(distractor_issues) > len(scores) * 0.2:
            summary.append("🎯 Improve distractor quality for multiple choice questions")
        
        # Educational value feedback
        avg_educational = sum(s.educational_value for s in scores) / len(scores)
        if avg_educational < 70:
            summary.append("📚 Consider aligning questions more closely with learning objectives")
        
        return summary


def create_question_validator() -> QuestionValidator:
    """Factory function to create a question validator instance"""
    return QuestionValidator()
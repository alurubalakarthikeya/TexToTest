import requests
import os
import re
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv
from distractor_generator import DistractorGenerator, create_multiple_choice_question
from question_types import QuestionGenerator, QuestionType, DifficultyLevel, format_question_for_display

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MISTRAL_MODEL = "mistralai/mistral-7b-instruct"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_SITE = os.getenv("OPENROUTER_SITE_URL") or os.getenv("SITE_URL")
APP_TITLE = os.getenv("APP_TITLE", "TexToTest")

# Initialize generators
distractor_gen = DistractorGenerator()
question_gen = QuestionGenerator()

# Initialize enhanced distractor generator (with fallback)
try:
    from improved_distractor_generator import create_improved_distractor_generator
    improved_distractor_gen = create_improved_distractor_generator()
    USE_IMPROVED_DISTRACTORS = True
    print("✓ Improved distractor generator loaded successfully")
except ImportError:
    print("Improved distractors not available. Using basic distractor generator.")
    improved_distractor_gen = None
    USE_IMPROVED_DISTRACTORS = False

try:
    from enhanced_distractors import create_enhanced_distractor_generator
    enhanced_distractor_gen = create_enhanced_distractor_generator()
    USE_ENHANCED_DISTRACTORS = True
except ImportError:
    enhanced_distractor_gen = None
    USE_ENHANCED_DISTRACTORS = False

# Initialize question validator (optional)
try:
    from question_validator import create_question_validator
    question_validator = create_question_validator()
    USE_QUESTION_VALIDATION = True
except ImportError:
    print("Question validator not available.")
    question_validator = None
    USE_QUESTION_VALIDATION = False

def get_openrouter_status() -> dict:
    """Return non-sensitive diagnostics for OpenRouter config."""
    key = os.getenv("OPENROUTER_API_KEY")
    return {
        "configured": bool(key and key.strip()),
        "key_prefix": (key[:7] + "…") if key else None,
        "model": MISTRAL_MODEL,
        "site_header_set": bool(OPENROUTER_SITE),
        "app_title": APP_TITLE,
    }

def generate_questions(context, num_questions=25, question_type="multiple_choice", difficulty=None, category=None):
    """Generate high-quality questions with intelligent analysis"""
    
    # Use new intelligent question generator as primary method
    try:
        from intelligent_question_generator import create_intelligent_question_generator
        intelligent_gen = create_intelligent_question_generator()
        
        if question_type == "multiple_choice":
            intelligent_questions = intelligent_gen.generate_intelligent_questions(context, num_questions)
            
            if intelligent_questions:
                print(f"✓ Generated {len(intelligent_questions)} high-quality questions using intelligent generator")
                return intelligent_questions
        
    except Exception as e:
        print(f"Intelligent question generation failed: {e}")
    
    # Fallback to local question generation
    try:
        from local_question_generator import create_local_question_generator
        local_gen = create_local_question_generator()
        local_questions = local_gen.generate_questions_from_text(context, num_questions, question_type)
        
        if local_questions:
            print(f"✓ Generated {len(local_questions)} questions using local generator (fallback)")
            return local_questions
    except Exception as e:
        print(f"Local intelligent generation also failed: {e}")
    
    # Final fallback to API-based generation
    try:
        if question_type == "multiple_choice":
            return generate_multiple_choice_questions(context, num_questions, difficulty, category)
        elif question_type == "true_false":
            return generate_simple_true_false(context, num_questions)
        else:
            return generate_multiple_choice_questions(context, num_questions, difficulty, category)
    except Exception as e:
        print(f"All question generation methods failed: {e}")
        return []

def generate_simple_true_false(context, num_questions=5):
    """Generate simple true/false questions from context"""
    import re
    
    questions = []
    sentences = re.split(r'[.!?]+', context)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    
    for i, sentence in enumerate(sentences[:num_questions]):
        questions.append({
            'question': f'True or False: {sentence.strip()}',
            'type': 'true_false',
            'correct_answer': 'True',
            'options': ['True', 'False'],
            'explanation': 'The statement is True based on the content',
            'difficulty': 'easy',
            'category': 'general',
            'points': 1
        })
    
    return questions

def generate_simple_questions(context, num_questions=25):
    """Generate simple text questions without multiple choice options"""
    if not OPENROUTER_API_KEY:
        raise Exception("Missing OPENROUTER_API_KEY. Set it in your deployment environment.")

    try:
        prompt = (
            f"Generate {num_questions} diverse, high-quality questions based on the following context.\n"
            f"Return each question on a new line without numbering.\n"
            f"Context: {context}\nQuestions:"
        )
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        if OPENROUTER_SITE:
            headers["HTTP-Referer"] = OPENROUTER_SITE
        headers["X-Title"] = APP_TITLE
        data = {
            "model": MISTRAL_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1024,
            "temperature": 0.7
        }
        response = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            try:
                content = result["choices"][0]["message"]["content"]
            except Exception:
                raise Exception(f"Unexpected OpenRouter response format: {result}")
            questions = [q.strip() for q in content.split("\n") if q.strip()]
            return questions[:num_questions]
        else:
            raise Exception(f"OpenRouter API error {response.status_code}: {response.text}")
    except Exception as e:
        # Fallback to demo questions when API fails
        print(f"Warning: OpenRouter API failed ({e}). Using demo questions.")
        return generate_demo_questions(context, num_questions)
def generate_demo_questions(context, num_questions=25):
    """Generate intelligent questions directly from content when API is unavailable"""
    import re
    
    # Split context into sentences
    sentences = re.split(r'[.!?]+', context)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    questions = []
    
    # Extract key concepts and create meaningful questions
    for sentence in sentences[:num_questions]:
        # Pattern 1: Convert statements to questions
        if 'is' in sentence or 'are' in sentence:
            # "X is Y" -> "What is X?"
            match = re.search(r'([A-Z][a-zA-Z\s]+?)\s+(?:is|are)\s+([^,]+)', sentence)
            if match:
                subject = match.group(1).strip()
                questions.append(f"What is {subject.lower()}?")
        
        # Pattern 2: Purpose and function questions
        if any(word in sentence.lower() for word in ['provides', 'enables', 'allows', 'helps']):
            match = re.search(r'([A-Z][a-zA-Z\s]+?)\s+(?:provides?|enables?|allows?|helps?)', sentence)
            if match:
                subject = match.group(1).strip()
                questions.append(f"What does {subject.lower()} do?")
        
        # Pattern 3: Process questions
        if any(word in sentence.lower() for word in ['by', 'through', 'using', 'via']):
            questions.append(f"How is this process accomplished?")
        
        # Pattern 4: Definition questions from descriptive sentences
        if len(sentence.split()) > 5:
            # Extract first noun phrase
            words = sentence.split()
            if len(words) > 2 and words[0][0].isupper():
                noun_phrase = ' '.join(words[:3]).rstrip('.,!?;:')
                questions.append(f"According to the text, what can you tell about {noun_phrase.lower()}?")
    
    # Extract key terms and create specific questions
    words = context.split()
    key_terms = []
    for word in words:
        clean_word = re.sub(r'[^\w]', '', word)
        if (len(clean_word) > 4 and 
            clean_word[0].isupper() and
            clean_word.lower() not in ['This', 'That', 'These', 'Those', 'With', 'From', 'They', 'Have', 'Will', 'Been', 'Were', 'When', 'Where', 'What', 'Which', 'Such']):
            key_terms.append(clean_word)
    
    # Add term-specific questions
    unique_terms = list(set(key_terms))[:8]
    for term in unique_terms:
        if len(questions) < num_questions:
            questions.append(f"What is the significance of {term} in this context?")
            questions.append(f"How does {term} relate to the main subject?")
    
    # Add analytical questions based on content
    if len(questions) < num_questions:
        analytical_questions = [
            f"What are the main points discussed in this text?",
            f"What conclusions can be drawn from the information?",
            f"What are the key benefits mentioned?",
            f"What challenges or issues are addressed?",
            f"What methods or approaches are described?",
            f"What examples support the main ideas?",
            f"What is the overall purpose of this content?",
            f"What relationships exist between different concepts?",
        ]
        questions.extend(analytical_questions[:num_questions - len(questions)])
    
    # Remove duplicates and clean up
    unique_questions = []
    seen = set()
    for q in questions:
        if q.lower() not in seen and len(q) > 10:
            unique_questions.append(q)
            seen.add(q.lower())
    
    return unique_questions[:num_questions]
def generate_multiple_choice_questions(context, num_questions=25, difficulty=None, category=None):
    """Generate multiple choice questions with distractors"""
    
    # First, generate question-answer pairs
    qa_pairs = generate_question_answer_pairs(context, num_questions)
    
    multiple_choice_questions = []
    
    for qa_pair in qa_pairs:
        question = qa_pair.get('question', '')
        answer = qa_pair.get('answer', '')
        
        if question and answer:
            try:
                # Use improved distractor generator for high-quality options
                if USE_IMPROVED_DISTRACTORS and improved_distractor_gen:
                    try:
                        distractors = improved_distractor_gen.generate_high_quality_distractors(
                            correct_answer=answer,
                            context=context,
                            num_distractors=3
                        )
                        print(f"✓ Generated high-quality distractors: {distractors}")
                    except Exception as e:
                        print(f"Improved distractors failed: {e}. Trying enhanced distractors.")
                        # Fallback to enhanced distractors
                        if USE_ENHANCED_DISTRACTORS and enhanced_distractor_gen:
                            try:
                                distractors = enhanced_distractor_gen.generate_hybrid_distractors(
                                    correct_answer=answer,
                                    context=context,
                                    num_distractors=3
                                )
                            except Exception as e2:
                                print(f"Enhanced distractors also failed: {e2}. Using basic distractors.")
                                distractors = distractor_gen.generate_distractors(
                                    correct_answer=answer,
                                    context=context,
                                    num_distractors=3
                                )
                        else:
                            distractors = distractor_gen.generate_distractors(
                                correct_answer=answer,
                                context=context,
                                num_distractors=3
                            )
                elif USE_ENHANCED_DISTRACTORS and enhanced_distractor_gen:
                    try:
                        distractors = enhanced_distractor_gen.generate_hybrid_distractors(
                            correct_answer=answer,
                            context=context,
                            num_distractors=3
                        )
                    except Exception as e:
                        print(f"Enhanced distractors failed: {e}. Using basic distractors.")
                        distractors = distractor_gen.generate_distractors(
                            correct_answer=answer,
                            context=context,
                            num_distractors=3
                        )
                else:
                    # Fallback to basic distractor generation
                    distractors = distractor_gen.generate_distractors(
                        correct_answer=answer,
                        context=context,
                        num_distractors=3
                    )
                
                # Create question object
                q_obj = question_gen.generate_multiple_choice(
                    text=question,
                    correct_answer=answer,
                    distractors=distractors
                )
                
                # Add difficulty and category with error handling
                try:
                    q_obj.difficulty = question_gen.classify_difficulty(q_obj, context)
                except Exception:
                    q_obj.difficulty = DifficultyLevel.MEDIUM
                
                try:
                    q_obj.category = question_gen.categorize_question(q_obj, context)
                except Exception:
                    q_obj.category = "general"
                
                # Format for display
                formatted_q = format_question_for_display(q_obj)
                multiple_choice_questions.append(formatted_q)
            except Exception as e:
                print(f"Error processing question '{question}': {e}")
                continue
    
    # Filter by difficulty if specified
    if difficulty:
        multiple_choice_questions = [
            q for q in multiple_choice_questions 
            if q.get('difficulty') == difficulty
        ]
    
    return multiple_choice_questions[:num_questions]

def generate_question_answer_pairs(context, num_questions=25):
    """Generate question-answer pairs from context using OpenRouter"""
    if not OPENROUTER_API_KEY:
        raise Exception("Missing OPENROUTER_API_KEY. Set it in your deployment environment.")
    
    try:
        prompt = f"""Based on the following context, generate {num_questions} question-answer pairs.
        Format strictly: Q: [concise question]
        A: [one word or at most a very short phrase (<= 2 words)]

        Keep answers noun-like and compact (e.g., 'Gradient', 'Overfitting', 'Neuron'). Avoid full sentences.

        Context: {context}

        Question-Answer pairs:"""
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        if OPENROUTER_SITE:
            headers["HTTP-Referer"] = OPENROUTER_SITE
        headers["X-Title"] = APP_TITLE
        data = {
            "model": MISTRAL_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.7
        }
        
        response = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=90)
        if response.status_code == 200:
            result = response.json()
            try:
                content = result["choices"][0]["message"]["content"]
            except Exception:
                raise Exception(f"Unexpected OpenRouter response format: {result}")
            return parse_question_answer_pairs(content)
        else:
            raise Exception(f"OpenRouter API error {response.status_code}: {response.text}")
    except Exception as e:
        # Fallback to demo question-answer pairs when API fails
        print(f"Warning: OpenRouter API failed ({e}). Using demo Q&A pairs.")
        # Try local intelligent question generation first
        try:
            from local_question_generator import create_local_question_generator
            local_gen = create_local_question_generator()
            local_questions = local_gen.generate_questions_from_text(context, num_questions, 'qa_pairs')
            # Convert to expected format
            qa_pairs = []
            for q in local_questions:
                qa_pairs.append({
                    "question": q['question'], 
                    "answer": q.get('correct_answer', q.get('options', {}).get('A', 'Unknown'))
                })
            return qa_pairs if qa_pairs else generate_demo_qa_pairs(context, num_questions)
        except Exception as e:
            print(f"Local question generation failed: {e}")
            return generate_demo_qa_pairs(context, num_questions)

def generate_demo_qa_pairs(context, num_questions=25):
    """Generate intelligent question-answer pairs from actual content"""
    import re
    
    # Clean and analyze the context
    sentences = re.split(r'[.!?]+', context)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    # Extract key information patterns
    qa_pairs = []
    
    # Pattern 1: Definition patterns (X is Y, X refers to Y, etc.)
    definition_patterns = [
        r'([A-Z][a-zA-Z\s]+?)\s+(?:is|are|refers? to|means?|represents?)\s+([^.!?]+)',
        r'([A-Z][a-zA-Z\s]+?):\s*([^.!?]+)',
        r'The\s+([a-zA-Z\s]+?)\s+(?:is|are)\s+([^.!?]+)',
    ]
    
    for sentence in sentences:
        for pattern in definition_patterns:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                concept = match.group(1).strip()
                definition = match.group(2).strip()
                if len(concept) > 2 and len(definition) > 5:
                    qa_pairs.append({
                        "question": f"What is {concept.lower()}?",
                        "answer": ' '.join(definition.split()[:4])  # Take first 4 words for cleaner answer
                    })
    
    # Pattern 2: Process and method questions
    process_patterns = [
        r'(?:by|through|via|using)\s+([^.!?,]+)',
        r'(?:process|method|approach|technique)\s+(?:of|for)\s+([^.!?,]+)',
    ]
    
    for sentence in sentences:
        for pattern in process_patterns:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                process = match.group(1).strip()
                if len(process) > 5:
                    qa_pairs.append({
                        "question": f"How is {process.lower().split()[0]} achieved?",
                        "answer": ' '.join(process.split()[:3]).capitalize()
                    })
    
    # Pattern 3: Purpose and function questions
    purpose_patterns = [
        r'(?:to|for)\s+([^.!?,]+?)(?:\s+and|\s+or|,|\.)',
        r'(?:purpose|goal|objective)\s+(?:is|of)\s+([^.!?,]+)',
    ]
    
    for sentence in sentences:
        for pattern in purpose_patterns:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                purpose = match.group(1).strip()
                if len(purpose) > 5 and not purpose.lower().startswith('the'):
                    qa_pairs.append({
                        "question": f"What is the purpose of {purpose.lower()}?",
                        "answer": purpose.split()[0].capitalize()
                    })
    
    # Pattern 4: Feature and characteristic questions
    feature_patterns = [
        r'([A-Z][a-zA-Z\s]+?)\s+(?:has|have|includes?|contains?|features?)\s+([^.!?,]+)',
        r'([A-Z][a-zA-Z\s]+?)\s+(?:provides?|offers?|enables?)\s+([^.!?,]+)',
    ]
    
    for sentence in sentences:
        for pattern in feature_patterns:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                subject = match.group(1).strip()
                feature = match.group(2).strip()
                if len(subject) > 2 and len(feature) > 5:
                    qa_pairs.append({
                        "question": f"What does {subject.lower()} provide?",
                        "answer": feature.split()[0].capitalize()
                    })
    
    # Pattern 5: Component and part questions
    component_patterns = [
        r'(?:consists? of|comprises?|includes?)\s+([^.!?]+)',
        r'(?:components?|parts?|elements?)\s+(?:are|include)\s+([^.!?]+)',
    ]
    
    for sentence in sentences:
        for pattern in component_patterns:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                components = match.group(1).strip()
                if len(components) > 5:
                    qa_pairs.append({
                        "question": f"What are the main components?",
                        "answer": components.split(',')[0].strip().split()[0].capitalize()
                    })
    
    # Extract key terms from context as fallback
    words = context.split()
    key_terms = []
    for word in words:
        clean_word = re.sub(r'[^\w]', '', word)
        if (len(clean_word) > 4 and 
            clean_word.lower() not in ['this', 'that', 'these', 'those', 'with', 'from', 'they', 'have', 'will', 'been', 'were', 'when', 'where', 'what', 'which', 'such'] and
            clean_word[0].isupper()):
            key_terms.append(clean_word)
    
    # Add key term questions if we don't have enough
    key_terms = list(set(key_terms))[:10]
    for term in key_terms:
        if len(qa_pairs) < num_questions:
            # Try to find the term in context for better answers
            term_context = ""
            for sentence in sentences:
                if term.lower() in sentence.lower():
                    term_context = sentence
                    break
            
            if term_context:
                # Extract meaningful answer from context
                words_after = term_context.lower().split(term.lower())[1:] if term.lower() in term_context.lower() else []
                if words_after:
                    answer_words = words_after[0].split()[:3]  # Take first few words after the term
                    answer = ' '.join(answer_words).strip('.,!?;: ')
                    if len(answer) > 2:
                        qa_pairs.append({
                            "question": f"What is {term}?",
                            "answer": answer.capitalize() if answer else term
                        })
                    else:
                        qa_pairs.append({
                            "question": f"What does {term} refer to?",
                            "answer": term
                        })
    
    # Remove duplicates and filter quality
    unique_pairs = []
    seen_questions = set()
    for pair in qa_pairs:
        if (pair['question'].lower() not in seen_questions and 
            len(pair['answer']) > 1 and 
            len(pair['question']) > 5):
            unique_pairs.append(pair)
            seen_questions.add(pair['question'].lower())
    
    # If we still don't have enough, add some context-based generic questions
    if len(unique_pairs) < num_questions:
        context_words = [w for w in context.split() if len(w) > 6][:5]
        for word in context_words:
            if len(unique_pairs) < num_questions:
                clean_word = re.sub(r'[^\w]', '', word)
                unique_pairs.append({
                    "question": f"According to the text, what is discussed about {clean_word.lower()}?",
                    "answer": clean_word.capitalize()
                })
    
    return unique_pairs[:num_questions]

def parse_question_answer_pairs(content: str) -> List[Dict[str, str]]:
    """Parse question-answer pairs from model output"""
    pairs = []
    lines = content.split('\n')
    
    current_question = ""
    current_answer = ""
    
    for line in lines:
        line = line.strip()
        if line.startswith('Q:'):
            current_question = line[2:].strip()
        elif line.startswith('A:'):
            current_answer = line[2:].strip()
            if current_question and current_answer:
                pairs.append({
                    'question': current_question,
                    'answer': current_answer
                })
                current_question = ""
                current_answer = ""
    
    # Alternative parsing for different formats
    if not pairs:
        # Try to find patterns like "1. Question? Answer:"
        pattern = r'(\d+\.\s*.*?\?)\s*(.*?)(?=\d+\.|$)'
        matches = re.findall(pattern, content, re.DOTALL)
        for match in matches:
            question = match[0].strip()
            answer = match[1].strip()
            if question and answer:
                pairs.append({
                    'question': question,
                    'answer': answer
                })
    
    return pairs

def generate_true_false_questions(context, num_questions=10, difficulty=None, category=None):
    """Generate true/false questions from context"""
    # Extract factual statements from context
    statements = extract_factual_statements(context, num_questions * 2)
    
    questions = []
    for i, statement in enumerate(statements[:num_questions]):
        # Create true statement (original)
        true_q = question_gen.generate_true_false(statement, True)
        true_q.difficulty = question_gen.classify_difficulty(true_q, context)
        true_q.category = question_gen.categorize_question(true_q, context)
        
        questions.append(format_question_for_display(true_q))
        
        # Optionally create false statement
        if len(questions) < num_questions and i < len(statements) - 1:
            false_q = question_gen.generate_true_false(statements[i+1], False)
            false_q.difficulty = question_gen.classify_difficulty(false_q, context)
            false_q.category = question_gen.categorize_question(false_q, context)
            
            questions.append(format_question_for_display(false_q))
    
    return questions[:num_questions]

def generate_fill_in_blank_questions(context, num_questions=10, difficulty=None, category=None):
    """Generate fill-in-the-blank questions"""
    candidates = question_gen.extract_question_candidates(context)
    questions = []
    
    for candidate in candidates[:num_questions]:
        if candidate['type'] == 'definition':
            # Create fill-in-blank for term
            sentence = candidate['sentence']
            term = candidate['term']
            
            q_obj = question_gen.generate_fill_in_blank(sentence, term)
            q_obj.difficulty = question_gen.classify_difficulty(q_obj, context)
            q_obj.category = question_gen.categorize_question(q_obj, context)
            
            questions.append(format_question_for_display(q_obj))
    
    return questions[:num_questions]

def generate_short_answer_questions(context, num_questions=10, difficulty=None, category=None):
    """Generate short answer questions"""
    # Generate open-ended questions using AI
    qa_pairs = generate_open_ended_questions(context, num_questions)
    
    questions = []
    for qa_pair in qa_pairs:
        question_text = qa_pair.get('question', '')
        answer = qa_pair.get('answer', '')
        
        if question_text and answer:
            q_obj = question_gen.generate_short_answer(question_text, answer)
            q_obj.difficulty = question_gen.classify_difficulty(q_obj, context)
            q_obj.category = question_gen.categorize_question(q_obj, context)
            
            questions.append(format_question_for_display(q_obj))
    
    return questions[:num_questions]

def generate_matching_questions(context, num_questions=5, difficulty=None, category=None):
    """Generate matching questions"""
    candidates = question_gen.extract_question_candidates(context)
    
    # Group candidates by type for matching
    definitions = [c for c in candidates if c['type'] == 'definition']
    
    questions = []
    i = 0
    while i < len(definitions) - 3 and len(questions) < num_questions:
        # Create matching question with 4 items
        items = []
        for j in range(4):
            if i + j < len(definitions):
                items.append({
                    'left': definitions[i + j]['term'],
                    'right': definitions[i + j]['definition'][:50] + '...'  # Truncate for readability
                })
        
        if len(items) >= 2:
            q_obj = question_gen.generate_matching(items)
            q_obj.difficulty = question_gen.classify_difficulty(q_obj, context)
            q_obj.category = question_gen.categorize_question(q_obj, context)
            
            questions.append(format_question_for_display(q_obj))
        
        i += 4
    
    return questions[:num_questions]

def generate_mixed_questions(context, num_questions=25, difficulty=None, category=None):
    """Generate a mix of different question types"""
    # Distribute questions across types
    mcq_count = max(1, num_questions // 2)  # 50% MCQ
    tf_count = max(1, num_questions // 4)   # 25% True/False
    fib_count = max(1, num_questions // 8)  # 12.5% Fill-in-blank
    sa_count = max(1, num_questions // 8)   # 12.5% Short answer
    
    questions = []
    
    # Generate each type
    questions.extend(generate_multiple_choice_questions(context, mcq_count, difficulty, category))
    questions.extend(generate_true_false_questions(context, tf_count, difficulty, category))
    questions.extend(generate_fill_in_blank_questions(context, fib_count, difficulty, category))
    questions.extend(generate_short_answer_questions(context, sa_count, difficulty, category))
    
    # Shuffle for variety
    import random
    random.shuffle(questions)
    
    return questions[:num_questions]

def extract_factual_statements(context, max_statements=20):
    """Extract factual statements from context for true/false questions"""
    sentences = context.split('.')
    statements = []
    
    for sentence in sentences[:max_statements * 2]:
        sentence = sentence.strip()
        if (len(sentence.split()) > 5 and 
            len(sentence.split()) < 25 and
            any(word in sentence.lower() for word in ['is', 'are', 'was', 'were', 'has', 'have'])):
            statements.append(sentence + '.')
    
    return statements[:max_statements]

def generate_open_ended_questions(context, num_questions=10):
    """Generate open-ended question-answer pairs for short answer questions"""
    if not OPENROUTER_API_KEY:
        raise Exception("Missing OPENROUTER_API_KEY. Set it in your deployment environment.")
    
    prompt = f"""Based on the following context, generate {num_questions} open-ended question-answer pairs.
    Format: Q: [analytical/explanatory question requiring 1-3 sentence answers]
    A: [concise but complete answer in 1-3 sentences]
    
    Focus on 'how', 'why', 'explain', 'describe', 'analyze' questions that test understanding.

    Context: {context}

    Question-Answer pairs:"""
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    if OPENROUTER_SITE:
        headers["HTTP-Referer"] = OPENROUTER_SITE
    headers["X-Title"] = APP_TITLE
    
    data = {
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1500,
        "temperature": 0.7
    }
    
    response = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=90)
    if response.status_code == 200:
        result = response.json()
        try:
            content = result["choices"][0]["message"]["content"]
        except Exception:
            raise Exception(f"Unexpected OpenRouter response format: {result}")
        return parse_question_answer_pairs(content)
    else:
        raise Exception(f"OpenRouter API error {response.status_code}: {response.text}")

import requests
import os
import re
import json
from typing import List, Dict
from dotenv import load_dotenv
from distractor_generator import DistractorGenerator, create_multiple_choice_question

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MISTRAL_MODEL = "mistralai/mistral-7b-instruct"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_SITE = os.getenv("OPENROUTER_SITE_URL") or os.getenv("SITE_URL")
APP_TITLE = os.getenv("APP_TITLE", "TexToTest")

# Initialize distractor generator
distractor_gen = DistractorGenerator()

def generate_questions(context, num_questions=25, question_type="multiple_choice"):
    """Generate questions with multiple choice options using distractor generation"""
    
    if question_type == "multiple_choice":
        return generate_multiple_choice_questions(context, num_questions)
    else:
        return generate_simple_questions(context, num_questions)

def generate_simple_questions(context, num_questions=25):
    """Generate simple text questions without multiple choice options"""
    if not OPENROUTER_API_KEY:
        raise Exception("Missing OPENROUTER_API_KEY. Set it in your deployment environment.")

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

def generate_multiple_choice_questions(context, num_questions=25):
    """Generate multiple choice questions with distractors"""
    
    # First, generate question-answer pairs
    qa_pairs = generate_question_answer_pairs(context, num_questions)
    
    multiple_choice_questions = []
    
    for qa_pair in qa_pairs:
        question = qa_pair.get('question', '')
        answer = qa_pair.get('answer', '')
        
        if question and answer:
            # Generate distractors using our hybrid approach
            distractors = distractor_gen.generate_distractors(
                correct_answer=answer,
                context=context,
                num_distractors=3
            )
            
            # Create formatted multiple choice question
            mc_question = create_multiple_choice_question(
                question=question,
                correct_answer=answer,
                distractors=distractors
            )
            
            multiple_choice_questions.append(mc_question)
    
    return multiple_choice_questions[:num_questions]

def generate_question_answer_pairs(context, num_questions=25):
    """Generate question-answer pairs from context using OpenRouter"""
    if not OPENROUTER_API_KEY:
        raise Exception("Missing OPENROUTER_API_KEY. Set it in your deployment environment.")
    prompt = f"""Based on the following context, generate {num_questions} question-answer pairs. 
    Format each pair as: Q: [question] A: [short, specific answer]
    
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

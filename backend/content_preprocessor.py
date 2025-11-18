"""
Advanced content preprocessing module for enhanced text extraction from PDFs.
Handles tables, images, structured content, and provides content analysis.
"""

import re
import os
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import logging

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Warning: pdfplumber not installed. Advanced PDF processing not available.")

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    print("Warning: PyPDF2 not installed. Basic PDF processing not available.")

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from nltk.tag import pos_tag
    NLTK_AVAILABLE = True
    
    # Test if NLTK data is accessible before trying to use it
    try:
        # Test basic functionality without downloading
        stopwords.words('english')[:5]  # Just test access
        sent_tokenize("Test sentence.")
        pos_tag(['test'])
    except Exception as nltk_error:
        print(f"NLTK data not accessible: {nltk_error}")
        NLTK_AVAILABLE = False
        
except (ImportError, Exception) as e:
    print(f"NLTK not available: {e}")
    NLTK_AVAILABLE = False
    print("Warning: NLTK not installed. Advanced text analysis not available.")

@dataclass
class ExtractedContent:
    """Container for extracted content with metadata"""
    text: str
    tables: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    headings: List[str]
    bullet_points: List[str]
    definitions: List[Dict[str, str]]
    key_terms: List[str]
    page_count: int
    content_type: str
    quality_score: float
    metadata: Dict[str, Any]

class ContentPreprocessor:
    """Advanced content preprocessing with enhanced PDF extraction"""
    
    def __init__(self):
        self.setup_logging()
        
        # Text cleaning patterns
        self.cleanup_patterns = [
            (r'\s+', ' '),  # Multiple whitespace to single space
            (r'\n\s*\n\s*\n', '\n\n'),  # Multiple newlines to double newline
            (r'[^\w\s\.\,\!\?\:\;\-\(\)\[\]\{\}\"\'\/\@\#\$\%\&\*\+\=\<\>\|\\]', ''),  # Remove special chars
            (r'(?i)copyright\s+©?\s*\d{4}.*', ''),  # Remove copyright notices
            (r'(?i)page\s+\d+\s*of\s*\d+', ''),  # Remove page numbers
            (r'(?i)footer.*|header.*', ''),  # Remove headers/footers
        ]
        
        # Heading detection patterns
        self.heading_patterns = [
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS headings
            r'^\d+\.\s+[A-Z][^.]*$',  # Numbered headings
            r'^Chapter\s+\d+.*',  # Chapter headings
            r'^Section\s+\d+.*',  # Section headings
            r'^\*\*[^*]+\*\*$',  # Markdown-style bold
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*:$',  # Title case with colon
        ]
        
        # Definition patterns
        self.definition_patterns = [
            r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is|are|refers to|means|defined as)\s+([^.]*)\.',
            r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:\s*([^.]*)\.',
            r'The\s+term\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+describes\s+([^.]*)\.',
            r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+can\s+be\s+defined\s+as\s+([^.]*)\.',
        ]
        
        # Key term indicators
        self.key_term_indicators = [
            r'\*\*([^*]+)\*\*',  # Bold text
            r'_([^_]+)_',  # Italic text
            r'`([^`]+)`',  # Code/monospace
            r'"([^"]+)"',  # Quoted terms
            r'\b[A-Z]{2,}\b',  # Acronyms
        ]

    def setup_logging(self):
        """Setup logging for content preprocessing"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def extract_from_file(self, file_path: str) -> ExtractedContent:
        """
        Main extraction method that routes to appropriate handler
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            ExtractedContent object with all extracted information
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self.extract_from_pdf(file_path)
        elif file_ext in ['.txt', '.md']:
            return self.extract_from_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

    def extract_from_pdf(self, file_path: str) -> ExtractedContent:
        """Extract content from PDF with advanced processing"""
        if PDFPLUMBER_AVAILABLE:
            return self._extract_with_pdfplumber(file_path)
        elif PYPDF2_AVAILABLE:
            return self._extract_with_pypdf2(file_path)
        else:
            raise ImportError("No PDF processing library available")

    def _extract_with_pdfplumber(self, file_path: str) -> ExtractedContent:
        """Enhanced PDF extraction using pdfplumber"""
        text_content = []
        tables = []
        images = []
        page_count = 0
        
        try:
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                    
                    # Extract tables
                    page_tables = page.extract_tables()
                    for table_idx, table in enumerate(page_tables):
                        if table:
                            processed_table = self._process_table(table, page_num, table_idx)
                            tables.append(processed_table)
                    
                    # Extract images (metadata only - actual image processing would require additional libraries)
                    if hasattr(page, 'images'):
                        for img_idx, img in enumerate(page.images):
                            image_info = {
                                'page': page_num + 1,
                                'index': img_idx,
                                'bbox': img.get('bbox', []),
                                'width': img.get('width', 0),
                                'height': img.get('height', 0),
                                'name': img.get('name', f'image_{page_num}_{img_idx}')
                            }
                            images.append(image_info)
                            
        except Exception as e:
            self.logger.error(f"Error extracting from PDF with pdfplumber: {e}")
            # Fallback to PyPDF2 if available
            if PYPDF2_AVAILABLE:
                return self._extract_with_pypdf2(file_path)
            raise
        
        # Combine and process text
        full_text = '\n'.join(text_content)
        return self._process_extracted_content(full_text, tables, images, page_count, 'pdf')

    def _extract_with_pypdf2(self, file_path: str) -> ExtractedContent:
        """Fallback PDF extraction using PyPDF2"""
        text_content = []
        page_count = 0
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                        
        except Exception as e:
            self.logger.error(f"Error extracting from PDF with PyPDF2: {e}")
            raise
        
        full_text = '\n'.join(text_content)
        return self._process_extracted_content(full_text, [], [], page_count, 'pdf')

    def extract_from_text(self, file_path: str) -> ExtractedContent:
        """Extract content from text files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        text = file.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Unable to decode text file")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        content_type = 'markdown' if file_ext == '.md' else 'text'
        
        return self._process_extracted_content(text, [], [], 1, content_type)

    def _process_table(self, table: List[List[str]], page_num: int, table_idx: int) -> Dict[str, Any]:
        """Process extracted table data"""
        processed_table = {
            'page': page_num + 1,
            'index': table_idx,
            'rows': len(table),
            'columns': len(table[0]) if table else 0,
            'data': table,
            'headers': table[0] if table else [],
            'text_representation': ''
        }
        
        # Create text representation
        if table:
            text_rows = []
            for row in table:
                if row and any(cell for cell in row if cell):  # Skip empty rows
                    clean_row = [str(cell).strip() if cell else '' for cell in row]
                    text_rows.append(' | '.join(clean_row))
            processed_table['text_representation'] = '\n'.join(text_rows)
        
        return processed_table

    def _process_extracted_content(self, text: str, tables: List[Dict], images: List[Dict], 
                                 page_count: int, content_type: str) -> ExtractedContent:
        """Process and analyze extracted content"""
        
        # Clean text
        cleaned_text = self._clean_text(text)
        
        # Extract structured elements
        headings = self._extract_headings(cleaned_text)
        bullet_points = self._extract_bullet_points(cleaned_text)
        definitions = self._extract_definitions(cleaned_text)
        key_terms = self._extract_key_terms(cleaned_text)
        
        # Add table text to main content
        table_texts = []
        for table in tables:
            if table.get('text_representation'):
                table_texts.append(f"Table {table['index'] + 1}:")
                table_texts.append(table['text_representation'])
        
        if table_texts:
            cleaned_text += '\n\n' + '\n'.join(table_texts)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(cleaned_text, tables, images, headings)
        
        # Generate metadata
        metadata = self._generate_metadata(cleaned_text, headings, definitions, key_terms)
        
        return ExtractedContent(
            text=cleaned_text,
            tables=tables,
            images=images,
            headings=headings,
            bullet_points=bullet_points,
            definitions=definitions,
            key_terms=key_terms,
            page_count=page_count,
            content_type=content_type,
            quality_score=quality_score,
            metadata=metadata
        )

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Apply cleanup patterns
        for pattern, replacement in self.cleanup_patterns:
            text = re.sub(pattern, replacement, text)
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove page breaks and form feeds
        text = text.replace('\f', '\n').replace('\r', '\n')
        
        return text.strip()

    def _extract_headings(self, text: str) -> List[str]:
        """Extract headings from text using patterns"""
        headings = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check against heading patterns
            for pattern in self.heading_patterns:
                if re.match(pattern, line):
                    headings.append(line)
                    break
            
            # Additional heuristics for headings
            if (len(line) < 100 and  # Not too long
                len(line.split()) <= 8 and  # Not too many words
                line[0].isupper() and  # Starts with capital
                not line.endswith('.') and  # Doesn't end with period
                len(line) > 3):  # Not too short
                
                # Check if it's likely a heading (short, contains important words)
                important_words = ['chapter', 'section', 'introduction', 'conclusion', 
                                 'overview', 'summary', 'analysis', 'methodology', 'results']
                if any(word in line.lower() for word in important_words):
                    if line not in headings:
                        headings.append(line)
        
        return headings

    def _extract_bullet_points(self, text: str) -> List[str]:
        """Extract bullet points and list items"""
        bullet_points = []
        lines = text.split('\n')
        
        bullet_patterns = [
            r'^\s*[•·▪▫‣⁃]\s+(.+)',  # Unicode bullets
            r'^\s*[\-\*\+]\s+(.+)',  # ASCII bullets
            r'^\s*\d+[\.\)]\s+(.+)',  # Numbered lists
            r'^\s*[a-zA-Z][\.\)]\s+(.+)',  # Lettered lists
        ]
        
        for line in lines:
            for pattern in bullet_patterns:
                match = re.match(pattern, line)
                if match:
                    bullet_points.append(match.group(1).strip())
                    break
        
        return bullet_points

    def _extract_definitions(self, text: str) -> List[Dict[str, str]]:
        """Extract definitions using patterns"""
        definitions = []
        
        for pattern in self.definition_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                
                # Quality filters
                if (len(term) > 2 and len(term) < 50 and
                    len(definition) > 10 and len(definition) < 300 and
                    not any(char in term for char in '()[]{}') and
                    definition.count(' ') >= 2):  # At least 3 words
                    
                    definitions.append({
                        'term': term,
                        'definition': definition
                    })
        
        # Remove duplicates
        seen_terms = set()
        unique_definitions = []
        for def_dict in definitions:
            term_lower = def_dict['term'].lower()
            if term_lower not in seen_terms:
                seen_terms.add(term_lower)
                unique_definitions.append(def_dict)
        
        return unique_definitions

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms and important concepts"""
        key_terms = []
        
        # Extract terms using patterns
        for pattern in self.key_term_indicators:
            matches = re.finditer(pattern, text)
            for match in matches:
                term = match.group(1).strip()
                if len(term) > 2 and len(term) < 50:
                    key_terms.append(term)
        
        # Use NLTK for additional term extraction if available
        if NLTK_AVAILABLE:
            try:
                # Extract proper nouns and important terms
                sentences = sent_tokenize(text)
                for sentence in sentences[:50]:  # Limit for performance
                    words = word_tokenize(sentence)
                    pos_tags = pos_tag(words)
                    
                    for word, pos in pos_tags:
                        # Extract proper nouns, nouns, and technical terms
                        if (pos in ['NNP', 'NNPS', 'NN', 'NNS'] and 
                            len(word) > 3 and 
                            word.isalpha() and
                            word[0].isupper()):
                            key_terms.append(word)
            except Exception as e:
                self.logger.warning(f"NLTK processing failed: {e}")
        
        # Remove duplicates and filter
        unique_terms = []
        seen_terms = set()
        
        for term in key_terms:
            term_lower = term.lower()
            if (term_lower not in seen_terms and
                len(term) > 2 and
                not term.lower() in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all']):
                seen_terms.add(term_lower)
                unique_terms.append(term)
        
        return unique_terms[:50]  # Limit number of key terms

    def _calculate_quality_score(self, text: str, tables: List[Dict], images: List[Dict], 
                               headings: List[str]) -> float:
        """Calculate content quality score based on various metrics"""
        score = 0.0
        max_score = 10.0
        
        # Text length and completeness (0-2 points)
        text_length = len(text.split())
        if text_length > 500:
            score += 2.0
        elif text_length > 200:
            score += 1.5
        elif text_length > 50:
            score += 1.0
        else:
            score += 0.5
        
        # Structural elements (0-2 points)
        if len(headings) > 0:
            score += min(0.5 * len(headings), 1.5)
        if len(tables) > 0:
            score += min(0.3 * len(tables), 0.5)
        
        # Content diversity (0-2 points)
        sentences = len(re.findall(r'[.!?]+', text))
        if sentences > 20:
            score += 1.0
        elif sentences > 10:
            score += 0.7
        elif sentences > 5:
            score += 0.4
        
        # Educational indicators (0-2 points)
        educational_keywords = ['definition', 'example', 'theory', 'concept', 'principle', 
                              'method', 'analysis', 'study', 'research', 'conclusion']
        keyword_count = sum(1 for keyword in educational_keywords if keyword in text.lower())
        score += min(keyword_count * 0.2, 1.5)
        
        # Technical content indicators (0-2 points)
        if re.search(r'\d+\.\d+|\d+%|Figure \d+|Table \d+', text):
            score += 1.0
        if len(re.findall(r'[A-Z]{2,}', text)) > 5:  # Acronyms
            score += 0.5
        if any(char in text for char in ['α', 'β', 'γ', '∆', '∑', '∫']):  # Mathematical symbols
            score += 0.5
        
        return min(score, max_score) / max_score

    def _generate_metadata(self, text: str, headings: List[str], definitions: List[Dict], 
                          key_terms: List[str]) -> Dict[str, Any]:
        """Generate metadata about the extracted content"""
        
        word_count = len(text.split())
        sentence_count = len(re.findall(r'[.!?]+', text))
        
        # Estimate reading level (simple approximation)
        if sentence_count > 0:
            avg_sentence_length = word_count / sentence_count
            if avg_sentence_length > 20:
                reading_level = 'Advanced'
            elif avg_sentence_length > 15:
                reading_level = 'Intermediate'
            else:
                reading_level = 'Basic'
        else:
            reading_level = 'Unknown'
        
        # Detect subject areas based on keywords
        subject_keywords = {
            'science': ['experiment', 'hypothesis', 'research', 'data', 'analysis', 'study'],
            'mathematics': ['equation', 'formula', 'theorem', 'proof', 'calculate', 'function'],
            'history': ['century', 'war', 'empire', 'civilization', 'ancient', 'modern'],
            'literature': ['author', 'novel', 'character', 'theme', 'symbolism', 'narrative'],
            'technology': ['computer', 'software', 'digital', 'network', 'algorithm', 'system'],
            'business': ['market', 'profit', 'strategy', 'management', 'economics', 'finance']
        }
        
        detected_subjects = []
        text_lower = text.lower()
        for subject, keywords in subject_keywords.items():
            if sum(1 for keyword in keywords if keyword in text_lower) >= 2:
                detected_subjects.append(subject)
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'paragraph_count': len([p for p in text.split('\n\n') if p.strip()]),
            'heading_count': len(headings),
            'definition_count': len(definitions),
            'key_term_count': len(key_terms),
            'avg_sentence_length': round(word_count / sentence_count, 1) if sentence_count > 0 else 0,
            'reading_level': reading_level,
            'detected_subjects': detected_subjects,
            'has_structured_content': len(headings) > 0 or len(definitions) > 0,
            'content_richness': 'High' if word_count > 1000 else 'Medium' if word_count > 300 else 'Low'
        }

def create_content_preprocessor() -> ContentPreprocessor:
    """Factory function to create a content preprocessor instance"""
    return ContentPreprocessor()

# Convenience function for backward compatibility
def extract_text_from_file_advanced(file_path: str) -> str:
    """
    Enhanced text extraction that maintains backward compatibility
    but provides improved content processing
    """
    preprocessor = create_content_preprocessor()
    try:
        extracted = preprocessor.extract_from_file(file_path)
        
        # Combine main text with structured content
        full_content = [extracted.text]
        
        # Add headings context
        if extracted.headings:
            full_content.append("\n=== Key Topics ===")
            full_content.extend(extracted.headings)
        
        # Add definitions context
        if extracted.definitions:
            full_content.append("\n=== Definitions ===")
            for def_item in extracted.definitions[:10]:  # Limit to avoid overwhelming
                full_content.append(f"{def_item['term']}: {def_item['definition']}")
        
        # Add key terms context
        if extracted.key_terms:
            full_content.append(f"\n=== Key Terms ===")
            full_content.append(", ".join(extracted.key_terms[:20]))  # Limit to top 20
        
        return "\n".join(full_content)
        
    except Exception as e:
        # Fallback to basic extraction
        print(f"Advanced extraction failed: {e}")
        from utils import extract_text_from_file
        return extract_text_from_file(file_path)
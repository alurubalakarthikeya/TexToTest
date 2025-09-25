import re
import random
from typing import List, Dict, Set, Tuple
from collections import defaultdict

class DistractorGenerator:
    def __init__(self):
        # Define entity patterns for rule-based extraction
        self.entity_patterns = {
            'people': [
                r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # First Last names
                r'\b(?:Dr|Professor|Mr|Ms|Mrs)\.? [A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b',  # Titles
                r'\b[A-Z][a-z]+(?:son|sen|stein|berg|mann|ski|owski|enko|ova|ez|es)\b',  # Common surname patterns
            ],
            'places': [
                r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*(?:\s(?:City|Town|Village|County|State|Province|Country|University|College|Institute|Hospital|School))\b',
                r'\b(?:New|Old|North|South|East|West|Upper|Lower|Great|Little)\s[A-Z][a-z]+\b',
                r'\b[A-Z][a-z]+(?:land|burg|ville|town|shire|ford|field|wood|mount|hill|dale|port|beach)\b',
            ],
            'concepts': [
                r'\b[A-Z][a-z]*(?:ism|ology|ography|ometry|ics|tion|sion|ness|ment|ship|hood|dom)\b',
                r'\b(?:theory|principle|law|rule|method|process|system|model|framework|approach)\s(?:of\s)?[A-Z][a-z]+\b',
                r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\s(?:theorem|principle|law|effect|syndrome|disorder)\b',
            ],
            'dates': [
                r'\b(?:19|20)\d{2}\b',  # Years
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2},?\s(?:19|20)?\d{2}\b',
                r'\b\d{1,2}(?:st|nd|rd|th)?\s(?:century|millennium)\b',
            ],
            'numbers': [
                r'\b\d+(?:\.\d+)?\s?(?:percent|%|million|billion|thousand|hundred)\b',
                r'\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion)\b',
            ]
        }
        
        # Common word endings for pattern-based variations
        self.spelling_variations = {
            'tion': ['sion', 'cion'],
            'ance': ['ence'],
            'ant': ['ent'],
            'ible': ['able'],
            'ize': ['ise'],
            'or': ['er'],
            'phy': ['fee', 'fi'],
            'ly': ['ley', 'li'],
        }
        
        # Common letter substitutions for near-homophones
        self.phonetic_substitutions = {
            'ph': 'f', 'f': 'ph',
            'c': 'k', 'k': 'c',
            'ei': 'ie', 'ie': 'ei',
            'ou': 'ow', 'ow': 'ou',
            'i': 'y', 'y': 'i',
            's': 'z', 'z': 's',
        }

    def extract_entities(self, text: str) -> Dict[str, Set[str]]:
        """Extract entities using rule-based patterns"""
        entities = defaultdict(set)
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match.strip()) > 2:  # Filter out very short matches
                        entities[entity_type].add(match.strip())
        
        return dict(entities)

    def generate_heuristic_distractors(self, correct_answer: str, context: str, entity_type: str = None) -> List[str]:
        """Generate distractors from the same semantic domain"""
        entities = self.extract_entities(context)
        distractors = []
        
        # If entity type is not specified, try to infer it
        if not entity_type:
            entity_type = self._infer_entity_type(correct_answer, entities)
        
        # Get candidates from the same category
        if entity_type and entity_type in entities:
            candidates = list(entities[entity_type])
            # Remove the correct answer if it appears in candidates
            candidates = [c for c in candidates if c.lower() != correct_answer.lower()]
            
            # Select random distractors from the same category
            num_distractors = min(2, len(candidates))
            if num_distractors > 0:
                distractors.extend(random.sample(candidates, num_distractors))
        
        return distractors

    def generate_pattern_based_distractors(self, correct_answer: str) -> List[str]:
        """Generate distractors based on spelling/phonetic patterns"""
        distractors = []
        
        # Generate spelling variations
        spelling_distractor = self._create_spelling_variation(correct_answer)
        if spelling_distractor and spelling_distractor != correct_answer:
            distractors.append(spelling_distractor)
        
        # Generate phonetic variations
        phonetic_distractor = self._create_phonetic_variation(correct_answer)
        if phonetic_distractor and phonetic_distractor != correct_answer:
            distractors.append(phonetic_distractor)
        
        # Generate orthographic variations (letter swaps, additions, deletions)
        ortho_distractor = self._create_orthographic_variation(correct_answer)
        if ortho_distractor and ortho_distractor != correct_answer:
            distractors.append(ortho_distractor)
        
        return distractors

    def _infer_entity_type(self, answer: str, entities: Dict[str, Set[str]]) -> str:
        """Infer the entity type of the correct answer"""
        for entity_type, entity_set in entities.items():
            if any(answer.lower() in entity.lower() or entity.lower() in answer.lower() 
                   for entity in entity_set):
                return entity_type
        
        # Fallback: use pattern matching on the answer itself
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, answer, re.IGNORECASE):
                    return entity_type
        
        return 'concepts'  # Default fallback

    def _create_spelling_variation(self, word: str) -> str:
        """Create a spelling variation based on common patterns"""
        for ending, variations in self.spelling_variations.items():
            if word.lower().endswith(ending):
                variation = random.choice(variations)
                return word[:-len(ending)] + variation
        return None

    def _create_phonetic_variation(self, word: str) -> str:
        """Create a phonetic variation"""
        word_lower = word.lower()
        for original, replacement in self.phonetic_substitutions.items():
            if original in word_lower:
                # Replace first occurrence
                new_word = word_lower.replace(original, replacement, 1)
                # Maintain original capitalization pattern
                return self._match_capitalization(new_word, word)
        return None

    def _create_orthographic_variation(self, word: str) -> str:
        """Create orthographic variations (swaps, additions, deletions)"""
        if len(word) < 3:
            return None
        
        variations = []
        
        # Letter swapping (transpose adjacent letters)
        if len(word) > 3:
            for i in range(len(word) - 1):
                chars = list(word)
                chars[i], chars[i + 1] = chars[i + 1], chars[i]
                variations.append(''.join(chars))
        
        # Letter deletion
        if len(word) > 4:
            for i in range(1, len(word) - 1):  # Don't delete first or last letter
                variation = word[:i] + word[i + 1:]
                variations.append(variation)
        
        # Letter addition (double a letter)
        if len(word) > 2:
            for i in range(1, len(word)):
                variation = word[:i] + word[i] + word[i:]
                variations.append(variation)
        
        return random.choice(variations) if variations else None

    def _match_capitalization(self, new_word: str, original: str) -> str:
        """Match the capitalization pattern of the original word"""
        if not new_word:
            return new_word
        
        result = []
        for i, char in enumerate(new_word):
            if i < len(original):
                if original[i].isupper():
                    result.append(char.upper())
                else:
                    result.append(char.lower())
            else:
                result.append(char.lower())
        
        return ''.join(result)

    def generate_distractors(self, correct_answer: str, context: str, num_distractors: int = 3) -> List[str]:
        """Generate distractors using the hybrid approach"""
        all_distractors = []
        
        # Generate heuristic distractors (domain-relevant)
        heuristic_distractors = self.generate_heuristic_distractors(correct_answer, context)
        all_distractors.extend(heuristic_distractors)
        
        # Generate pattern-based distractors (confusing variations)
        pattern_distractors = self.generate_pattern_based_distractors(correct_answer)
        all_distractors.extend(pattern_distractors)
        
        # Remove duplicates and the correct answer
        unique_distractors = []
        seen = set()
        for distractor in all_distractors:
            if (distractor.lower() not in seen and 
                distractor.lower() != correct_answer.lower() and
                len(distractor.strip()) > 0):
                unique_distractors.append(distractor)
                seen.add(distractor.lower())
        
        # If we don't have enough distractors, generate some generic ones
        while len(unique_distractors) < num_distractors:
            generic_distractor = self._generate_generic_distractor(correct_answer, unique_distractors)
            if generic_distractor:
                unique_distractors.append(generic_distractor)
            else:
                break
        
        return unique_distractors[:num_distractors]

    def _generate_generic_distractor(self, correct_answer: str, existing_distractors: List[str]) -> str:
        """Generate a generic distractor when specific methods fail"""
        generic_options = [
            f"Not {correct_answer}",
            f"Alternative to {correct_answer}",
            f"{correct_answer} variant",
            f"Similar to {correct_answer}",
            "None of the above",
            "All of the above",
        ]
        
        for option in generic_options:
            if option not in existing_distractors:
                return option
        
        return None

def create_multiple_choice_question(question: str, correct_answer: str, distractors: List[str]) -> Dict:
    """Create a formatted multiple choice question with short options.

    - Prefer single-word options; cap to a very short phrase when necessary.
    - Deduplicate after normalization; backfill with short tokens if needed.
    - Preserve correctness after normalization/shuffle.
    """

    def normalize_option(text: str, max_words: int = 2, max_chars: int = 24) -> str:
        if not text:
            return ""
        # Strip quotes and brackets
        t = re.sub(r'[\"\'\(\)\[\]\{\}]', '', str(text)).strip()
        # Split on sentence/phrase delimiters and take the first chunk
        t = re.split(r'[\n\r\.;:,.\u2013\u2014\-\u2014/]', t)[0].strip() or str(text).strip()
        # Tokenize by whitespace
        tokens = [tok for tok in re.split(r'\s+', t) if tok]
        if not tokens:
            return ""
        # If too many words, prefer a single salient token
        if len(tokens) > max_words:
            # Prefer capitalized or alphabetic tokens, then longest
            cand = None
            alpha_tokens = [tok for tok in tokens if re.match(r'^[A-Za-z][A-Za-z\-]*$', tok)]
            cap_tokens = [tok for tok in alpha_tokens if tok[0].isupper()]
            if cap_tokens:
                cand = max(cap_tokens, key=len)
            elif alpha_tokens:
                cand = max(alpha_tokens, key=len)
            else:
                cand = tokens[0]
            tokens = [cand]
        # Rejoin and hard-cap length
        out = ' '.join(tokens).strip()
        if len(out) > max_chars:
            out = out[:max_chars].rstrip()
        # Ensure mostly single word by removing trailing minor words
        out_tokens = out.split()
        if len(out_tokens) > 2:
            out = out_tokens[0]
        return out

    def short_fallbacks(correct: str) -> List[str]:
        pool = [
            "Alpha", "Beta", "Gamma", "Delta", "Sigma", "Omega",
            "Kappa", "Theta", "Zeta", "Eta", "Iota"
        ]
        # Avoid using the (normalized) correct as fallback
        c = normalize_option(correct)
        return [p for p in pool if p.lower() != (c or '').lower()]

    # Build (text, is_correct) pairs
    pairs = [(correct_answer, True)] + [(d, False) for d in (distractors or [])]
    # Normalize all options to be short
    norm_pairs: List[Tuple[str, bool]] = []
    seen_lower = set()
    for txt, is_ok in pairs:
        norm = normalize_option(txt)
        if not norm:
            continue
        key = norm.lower()
        if key in seen_lower:
            continue
        seen_lower.add(key)
        norm_pairs.append((norm, is_ok))

    # Ensure the correct answer exists; if not, add normalized correct
    if not any(flag for _, flag in norm_pairs):
        c = normalize_option(correct_answer) or str(correct_answer).strip()[:24]
        if c and c.lower() not in seen_lower:
            norm_pairs.insert(0, (c, True))

    # Backfill short fallbacks to reach 4 options
    fb = short_fallbacks(correct_answer)
    for token in fb:
        if len(norm_pairs) >= 4:
            break
        if token.lower() not in seen_lower:
            norm_pairs.append((token, False))
            seen_lower.add(token.lower())

    # If still fewer than 4, synthesize tiny variants of correct
    while len(norm_pairs) < 4:
        base = (normalize_option(correct_answer) or "Opt")
        variant = base + random.choice(["X", "Prime", "Max", "Pro"])[:3]
        if variant.lower() not in seen_lower:
            norm_pairs.append((variant, False))
            seen_lower.add(variant.lower())

    # Shuffle and trim to 4
    random.shuffle(norm_pairs)
    norm_pairs = norm_pairs[:4]

    # Determine correct option letter
    correct_index = next((i for i, (_, flag) in enumerate(norm_pairs) if flag), 0)
    correct_option = chr(65 + correct_index)

    # Format options map
    formatted_options = {chr(65 + i): txt for i, (txt, _) in enumerate(norm_pairs)}

    return {
        'question': question,
        'options': formatted_options,
        'correct_answer': correct_option,
        'explanation': f"The correct answer is {correct_option}: {formatted_options[correct_option]}"
    }
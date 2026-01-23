from typing import List
import re
from collections import Counter
from models.models import KeyTerm
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy

class KeyTermsExtractor:
    """Extract and rank important terms from legal documents"""
    
    def __init__(self):
        self.nlp = None
        self._load_nlp_model()
    
    def _load_nlp_model(self):
        """Load spaCy NLP model"""
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except OSError:
            import subprocess
            subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
            self.nlp = spacy.load('en_core_web_sm')
    
    def extract_key_terms(self, text: str, max_terms: int = 20) -> List[KeyTerm]:
        """
        Extract key terms from document
        
        Args:
            text: Document text
            max_terms: Maximum number of terms to extract
            
        Returns:
            List of KeyTerm objects
        """
        key_terms = []
        
        # Extract named entities
        entities = self._extract_entities(text)
        key_terms.extend(entities)
        
        # Extract important phrases using TF-IDF
        important_phrases = self._extract_important_phrases(text, max_terms)
        key_terms.extend(important_phrases)
        
        # Extract monetary values
        monetary_values = self._extract_monetary_values(text)
        key_terms.extend(monetary_values)
        
        # Extract dates
        dates = self._extract_dates(text)
        key_terms.extend(dates)
        
        # Sort by importance score and limit
        key_terms.sort(key=lambda x: x.importance_score, reverse=True)
        
        return key_terms[:max_terms]
    
    def _extract_entities(self, text: str) -> List[KeyTerm]:
        """Extract named entities using spaCy"""
        doc = self.nlp(text)
        entities = []
        
        # Count entity occurrences
        entity_counts = Counter()
        entity_contexts = {}
        
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PERSON', 'GPE', 'LAW', 'DATE', 'MONEY']:
                entity_counts[ent.text] += 1
                
                # Store context (sentence containing the entity)
                if ent.text not in entity_contexts:
                    entity_contexts[ent.text] = []
                
                # Get sentence containing entity
                sent = ent.sent.text.strip()
                if sent not in entity_contexts[ent.text]:
                    entity_contexts[ent.text].append(sent)
        
        # Create KeyTerm objects
        for entity, count in entity_counts.most_common(10):
            # Get entity type
            entity_type = None
            for ent in doc.ents:
                if ent.text == entity:
                    entity_type = ent.label_
                    break
            
            # Calculate importance (based on frequency)
            importance = min(count * 10, 100)
            
            entities.append(KeyTerm(
                text=entity,
                category=entity_type or 'ENTITY',
                frequency=count,
                importance_score=importance,
                context=entity_contexts[entity][:3]  # Keep top 3 contexts
            ))
        
        return entities
    
    def _extract_important_phrases(self, text: str, max_phrases: int = 10) -> List[KeyTerm]:
        """Extract important phrases using TF-IDF"""
        # Split into sentences
        sentences = text.split('.')
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if len(sentences) < 2:
            return []
        
        try:
            # Use TF-IDF to find important phrases
            vectorizer = TfidfVectorizer(
                max_features=max_phrases,
                ngram_range=(2, 4),  # 2-4 word phrases
                stop_words='english'
            )
            
            tfidf_matrix = vectorizer.fit_transform(sentences)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get phrase scores
            phrase_scores = tfidf_matrix.sum(axis=0).A1
            
            # Create KeyTerm objects
            phrases = []
            for idx, phrase in enumerate(feature_names):
                score = phrase_scores[idx]
                
                # Find contexts
                contexts = [s for s in sentences if phrase in s.lower()][:2]
                
                phrases.append(KeyTerm(
                    text=phrase.title(),
                    category='PHRASE',
                    frequency=len(contexts),
                    importance_score=min(score * 100, 100),
                    context=contexts
                ))
            
            return phrases
        
        except Exception as e:
            print(f"Error extracting phrases: {e}")
            return []
    
    def _extract_monetary_values(self, text: str) -> List[KeyTerm]:
        """Extract monetary values from text"""
        # Pattern for monetary values
        money_pattern = r'\$[\d,]+(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars|USD|EUR|GBP)'
        
        matches = re.finditer(money_pattern, text, re.IGNORECASE)
        
        monetary_values = []
        seen = set()
        
        for match in matches:
            value = match.group()
            if value not in seen:
                seen.add(value)
                
                # Find context
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end].strip()
                
                monetary_values.append(KeyTerm(
                    text=value,
                    category='MONEY',
                    frequency=1,
                    importance_score=80,  # High importance for monetary values
                    context=[context]
                ))
        
        return monetary_values[:5]  # Limit to top 5
    
    def _extract_dates(self, text: str) -> List[KeyTerm]:
        """Extract dates from text"""
        doc = self.nlp(text)
        
        dates = []
        seen = set()
        
        for ent in doc.ents:
            if ent.label_ == 'DATE' and ent.text not in seen:
                seen.add(ent.text)
                
                # Get context
                sent = ent.sent.text.strip()
                
                dates.append(KeyTerm(
                    text=ent.text,
                    category='DATE',
                    frequency=1,
                    importance_score=70,  # High importance for dates
                    context=[sent]
                ))
        
        return dates[:5]  # Limit to top 5

"""
Search Service for Legal Document Review Assistant
Provides full-text search and filtering capabilities across all processed documents
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import re


class SearchService:
    """Service for searching and filtering legal documents"""
    
    def __init__(self, processed_folder: str):
        """
        Initialize search service
        
        Args:
            processed_folder: Path to folder containing processed documents
        """
        self.processed_folder = Path(processed_folder)
    
    def search(
        self,
        query: str = "",
        risk_levels: Optional[List[str]] = None,
        document_types: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        sort_by: str = "relevance",
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search documents with advanced filtering
        
        Args:
            query: Search query string
            risk_levels: Filter by risk levels (low, medium, high, critical)
            document_types: Filter by document types
            date_from: Start date for filtering (ISO format)
            date_to: End date for filtering (ISO format)
            search_fields: Specific fields to search in (content, clauses, issues, recommendations)
            sort_by: Sort results by (relevance, date, risk_score)
            limit: Maximum number of results to return
            
        Returns:
            Dictionary containing search results and metadata
        """
        all_documents = self._load_all_documents()
        
        # Apply filters
        filtered_docs = self._apply_filters(
            all_documents,
            risk_levels=risk_levels,
            document_types=document_types,
            date_from=date_from,
            date_to=date_to
        )
        
        # Apply search query
        if query:
            search_results = self._search_documents(
                filtered_docs,
                query,
                search_fields=search_fields or ["content", "clauses", "issues", "recommendations"]
            )
        else:
            search_results = [
                {"document": doc, "score": 0, "matches": []}
                for doc in filtered_docs
            ]
        
        # Sort results
        sorted_results = self._sort_results(search_results, sort_by)
        
        # Limit results
        limited_results = sorted_results[:limit]
        
        return {
            "query": query,
            "total_results": len(sorted_results),
            "returned_results": len(limited_results),
            "results": limited_results,
            "filters_applied": {
                "risk_levels": risk_levels,
                "document_types": document_types,
                "date_from": date_from,
                "date_to": date_to
            }
        }
    
    def get_search_suggestions(self) -> Dict[str, List[str]]:
        """
        Get search suggestions based on indexed documents
        
        Returns:
            Dictionary containing suggestions for document types, risk levels, and common terms
        """
        all_documents = self._load_all_documents()
        
        document_types = set()
        risk_levels = set()
        clause_types = set()
        
        for doc in all_documents:
            # Collect document types
            if doc.get("document_type"):
                document_types.add(doc["document_type"])
            
            # Collect risk levels
            if doc.get("risk_level"):
                risk_levels.add(doc["risk_level"])
            
            # Collect clause types
            for clause in doc.get("clauses", []):
                if clause.get("type"):
                    clause_types.add(clause["type"])
        
        return {
            "document_types": sorted(list(document_types)),
            "risk_levels": sorted(list(risk_levels)),
            "clause_types": sorted(list(clause_types)),
            "search_fields": ["content", "clauses", "issues", "recommendations", "summary"]
        }
    
    def _load_all_documents(self) -> List[Dict[str, Any]]:
        """Load all processed documents from the processed folder"""
        documents = []
        
        if not self.processed_folder.exists():
            return documents
        
        for json_file in self.processed_folder.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
                    documents.append(doc_data)
            except Exception as e:
                print(f"Error loading document {json_file}: {e}")
                continue
        
        return documents
    
    def _apply_filters(
        self,
        documents: List[Dict[str, Any]],
        risk_levels: Optional[List[str]] = None,
        document_types: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Apply filters to document list"""
        filtered = documents
        
        # Filter by risk level
        if risk_levels:
            risk_levels_lower = [r.lower() for r in risk_levels]
            filtered = [
                doc for doc in filtered
                if doc.get("risk_level", "").lower() in risk_levels_lower
            ]
        
        # Filter by document type
        if document_types:
            filtered = [
                doc for doc in filtered
                if any(dt.lower() in doc.get("document_type", "").lower() for dt in document_types)
            ]
        
        # Filter by date range
        if date_from or date_to:
            filtered = self._filter_by_date(filtered, date_from, date_to)
        
        return filtered
    
    def _filter_by_date(
        self,
        documents: List[Dict[str, Any]],
        date_from: Optional[str],
        date_to: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Filter documents by date range"""
        filtered = []
        
        for doc in documents:
            doc_date_str = doc.get("processed_at")
            if not doc_date_str:
                continue
            
            try:
                doc_date = datetime.fromisoformat(doc_date_str.replace('Z', '+00:00'))
                
                if date_from:
                    from_date = datetime.fromisoformat(date_from)
                    if doc_date < from_date:
                        continue
                
                if date_to:
                    to_date = datetime.fromisoformat(date_to)
                    if doc_date > to_date:
                        continue
                
                filtered.append(doc)
            except Exception:
                continue
        
        return filtered
    
    def _search_documents(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        search_fields: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Search documents for query string
        
        Returns list of dicts with document, score, and matches
        """
        query_lower = query.lower()
        query_terms = re.findall(r'\w+', query_lower)
        
        results = []
        
        for doc in documents:
            score = 0
            matches = []
            
            # Search in content
            if "content" in search_fields:
                content = doc.get("content", "").lower()
                content_score, content_matches = self._score_text(content, query_lower, query_terms)
                score += content_score * 1.0  # Base weight
                matches.extend([{"field": "content", "text": m} for m in content_matches])
            
            # Search in clauses
            if "clauses" in search_fields:
                for clause in doc.get("clauses", []):
                    clause_text = f"{clause.get('type', '')} {clause.get('text', '')}".lower()
                    clause_score, clause_matches = self._score_text(clause_text, query_lower, query_terms)
                    score += clause_score * 1.5  # Higher weight for clauses
                    matches.extend([{"field": "clause", "text": m, "type": clause.get('type')} for m in clause_matches])
            
            # Search in issues
            if "issues" in search_fields:
                for issue in doc.get("issues", []):
                    issue_text = f"{issue.get('type', '')} {issue.get('description', '')}".lower()
                    issue_score, issue_matches = self._score_text(issue_text, query_lower, query_terms)
                    score += issue_score * 1.3
                    matches.extend([{"field": "issue", "text": m} for m in issue_matches])
            
            # Search in recommendations
            if "recommendations" in search_fields:
                for rec in doc.get("recommendations", []):
                    rec_lower = rec.lower()
                    rec_score, rec_matches = self._score_text(rec_lower, query_lower, query_terms)
                    score += rec_score * 1.2
                    matches.extend([{"field": "recommendation", "text": m} for m in rec_matches])
            
            # Search in summary
            if "summary" in search_fields:
                summary = doc.get("summary", {})
                summary_text = f"{summary.get('purpose', '')} {summary.get('key_points', '')}".lower()
                summary_score, summary_matches = self._score_text(summary_text, query_lower, query_terms)
                score += summary_score * 1.1
                matches.extend([{"field": "summary", "text": m} for m in summary_matches])
            
            # Only include documents with matches
            if score > 0:
                results.append({
                    "document": doc,
                    "score": score,
                    "matches": matches[:10]  # Limit matches to top 10
                })
        
        return results
    
    def _score_text(self, text: str, query: str, query_terms: List[str]) -> tuple:
        """
        Score text based on query match
        
        Returns (score, list of matching snippets)
        """
        score = 0
        matches = []
        
        # Exact phrase match (highest score)
        if query in text:
            score += 10
            matches.append(self._extract_snippet(text, query))
        
        # Individual term matches
        for term in query_terms:
            if term in text:
                term_count = text.count(term)
                score += term_count * 2
                if len(matches) < 5:  # Limit snippets
                    matches.append(self._extract_snippet(text, term))
        
        return score, matches
    
    def _extract_snippet(self, text: str, match_term: str, context_chars: int = 100) -> str:
        """Extract a snippet of text around the match term"""
        match_pos = text.find(match_term)
        if match_pos == -1:
            return ""
        
        start = max(0, match_pos - context_chars)
        end = min(len(text), match_pos + len(match_term) + context_chars)
        
        snippet = text[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet.strip()
    
    def _sort_results(self, results: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
        """Sort search results"""
        if sort_by == "relevance":
            return sorted(results, key=lambda x: x["score"], reverse=True)
        
        elif sort_by == "date":
            return sorted(
                results,
                key=lambda x: x["document"].get("processed_at", ""),
                reverse=True
            )
        
        elif sort_by == "risk_score":
            return sorted(
                results,
                key=lambda x: x["document"].get("risk_score", 0),
                reverse=True
            )
        
        return results

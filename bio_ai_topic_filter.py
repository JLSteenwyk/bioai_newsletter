"""Utilities for enforcing Bio+AI relevance across content sources."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Set
import re

# Keywords that strongly indicate an AI framing without implying biology on their own.
AI_KEYWORDS: Set[str] = {
    'ai',
    'artificial intelligence',
    'machine learning',
    'deep learning',
    'neural network',
    'neural networks',
    'transformer',
    'transformers',
    'large language model',
    'large language models',
    'llm',
    'llms',
    'foundation model',
    'foundation models',
    'reinforcement learning',
    'computer vision',
    'natural language processing',
    'nlp',
    'self-supervised learning',
    'unsupervised learning',
    'multimodal',
    'reasoning model',
    'generative ai',
    'ai agent',
    'ai agents',
    'autonomous agent',
    'autonomous agents',
    'ai safety',
    'responsible ai',
    'model fine-tuning',
    'fine-tuning',
    'few-shot learning',
    'transfer learning',
    'graph neural network',
    'graph neural networks',
}

# Keywords that indicate biological or life-science framing without necessarily invoking AI.
BIOLOGY_KEYWORDS: Set[str] = {
    'biology',
    'biological',
    'biologist',
    'biologists',
    'genomics',
    'genome',
    'genomic',
    'genetic',
    'genetics',
    'dna',
    'rna',
    'protein',
    'proteins',
    'proteomic',
    'proteomics',
    'transcriptomic',
    'transcriptomics',
    'metabolomic',
    'metabolomics',
    'cell',
    'cells',
    'cellular',
    'clinical',
    'clinic',
    'medicine',
    'medical',
    'healthcare',
    'biomedical',
    'life science',
    'life sciences',
    'drug discovery',
    'drug development',
    'therapeutics',
    'therapeutic',
    'disease',
    'diseases',
    'pathology',
    'epidemiology',
    'immunology',
    'immunotherapy',
    'microbiome',
    'synthetic biology',
    'bioengineering',
    'biotechnology',
    'biotech',
    'laboratory',
    'lab',
}

# Terms that inherently describe an AI+biology intersection (they count toward both sides).
HYBRID_KEYWORDS: Set[str] = {
    'bioai',
    'bio-ai',
    'ai in biology',
    'ai for biology',
    'ai-powered biology',
    'ai-driven biology',
    'ai in medicine',
    'ai for medicine',
    'ai in healthcare',
    'ai for healthcare',
    'ai in genomics',
    'ai for genomics',
    'computational biology',
    'computational genomics',
    'computational medicine',
    'bioinformatics',
    'digital pathology',
    'clinical ai',
    'medical ai',
    'healthcare ai',
    'precision medicine',
    'personalized medicine',
    'molecular dynamics',
    'protein folding',
    'alphafold',
    'ai drug discovery',
    'ai-powered drug discovery',
    'ai-driven drug discovery',
    'ai-enabled drug discovery',
    'ai drug development',
    'ai-enabled diagnostics',
    'ai diagnostics',
    'data-driven biology',
    'machine-learning biology',
    'machine learning for biology',
    'machine learning in biology',
    'machine learning for medicine',
    'machine learning in medicine',
    'ml for biology',
    'ml for medicine',
    'ai in biotech',
    'ai for biotech',
    'generative biology',
    'generative biotech',
}


def _compile_keyword_patterns(keywords: Iterable[str]) -> dict[str, re.Pattern[str]]:
    return {
        keyword: re.compile(r'(?<!\w)' + re.escape(keyword) + r'(?!\w)')
        for keyword in keywords
    }


AI_PATTERNS = _compile_keyword_patterns(AI_KEYWORDS)
BIO_PATTERNS = _compile_keyword_patterns(BIOLOGY_KEYWORDS)
HYBRID_PATTERNS = _compile_keyword_patterns(HYBRID_KEYWORDS)


@dataclass
class TopicMatch:
    """Represents the Bio+AI keyword matches discovered in a text."""

    ai_terms: Set[str]
    biology_terms: Set[str]
    hybrid_terms: Set[str]

    @property
    def has_ai(self) -> bool:
        return bool(self.ai_terms or self.hybrid_terms)

    @property
    def has_biology(self) -> bool:
        return bool(self.biology_terms or self.hybrid_terms)

    @property
    def is_bio_ai(self) -> bool:
        return self.has_ai and self.has_biology

    @property
    def keywords(self) -> List[str]:
        combined = self.ai_terms | self.biology_terms | self.hybrid_terms
        return sorted(combined)


def _find_matches(text: str, patterns: dict[str, re.Pattern[str]]) -> Set[str]:
    matches: Set[str] = set()
    if not text:
        return matches

    lowered = text.lower()
    for keyword, pattern in patterns.items():
        if pattern.search(lowered):
            matches.add(keyword)
    return matches


def analyze_text_for_bio_ai(text: str) -> TopicMatch:
    """Return the Bio+AI keyword matches found within ``text``."""
    hybrid = _find_matches(text, HYBRID_PATTERNS)

    ai_hits = _find_matches(text, AI_PATTERNS)
    bio_hits = _find_matches(text, BIO_PATTERNS)

    if hybrid:
        ai_hits |= hybrid
        bio_hits |= hybrid

    return TopicMatch(ai_terms=ai_hits, biology_terms=bio_hits, hybrid_terms=hybrid)


def is_bio_ai_relevant(text: str) -> bool:
    """Convenience helper to check whether ``text`` references both AI and biology."""
    return analyze_text_for_bio_ai(text).is_bio_ai

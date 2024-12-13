
import re
from typing import List

NOISE_PATTERNS = [
    r'JavaScript must be enabled',
    r'Please enable JavaScript',
    r'Subscribe to read more',
    r'Subscribe now',
    r'Sign (up|in)',
    r'Log in',
    r'Cookie Policy',
    r'Privacy Policy',
    r'Advertisement',
    r'Related Articles',
    r'Share this article',
    r'Follow us on',
    r'\S+@\S+\.\S+',  # Email addresses
    r'https?://\S+',  # URLs
]

def clean_text(text: str) -> str:
    """Clean extracted text by removing common noise patterns."""
    combined_pattern = '|'.join(NOISE_PATTERNS)
    paragraphs = text.split('\n')
    cleaned_paragraphs = []
    
    for p in paragraphs:
        if (
            not re.search(combined_pattern, p, re.IGNORECASE) and
            len(p.split()) >= 4 and
            len(set(p.split())) / len(p.split()) >= 0.4
        ):
            cleaned_paragraphs.append(p.strip())
    
    return '\n\n'.join(p for p in cleaned_paragraphs if p)
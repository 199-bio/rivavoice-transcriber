"""
Text utilities for transcript processing
"""

from typing import List, Tuple
import re


def tokenize(text: str) -> List[str]:
    """Split text into words/tokens, preserving punctuation"""
    # Split by whitespace while keeping punctuation attached
    tokens = re.findall(r'\S+', text.strip())
    return tokens


def find_overlap(tokens1: List[str], tokens2: List[str], max_overlap: int = 10) -> int:
    """
    Find the overlap between end of tokens1 and start of tokens2
    
    Returns the number of overlapping tokens
    """
    if not tokens1 or not tokens2:
        return 0
    
    # Limit search to reasonable overlap size
    max_overlap = min(max_overlap, len(tokens1), len(tokens2))
    
    # Try different overlap sizes, starting from largest
    for overlap_size in range(max_overlap, 0, -1):
        # Get end of first transcript
        end_tokens = tokens1[-overlap_size:]
        # Get start of second transcript
        start_tokens = tokens2[:overlap_size]
        
        # Check if they match
        if end_tokens == start_tokens:
            return overlap_size
    
    return 0


def deduplicate_transcripts(previous: str, current: str) -> str:
    """
    Merge two transcripts, removing duplicate tokens at the boundary
    
    Args:
        previous: Previous transcript text
        current: Current transcript text
        
    Returns:
        Merged transcript with duplicates removed
    """
    if not previous:
        return current
    if not current:
        return previous
    
    # Special handling for ellipsis
    # If previous ends with "..." and current starts with "...", merge them
    if previous.rstrip().endswith("...") and current.lstrip().startswith("..."):
        # Remove leading ellipsis from current
        current = current.lstrip().lstrip(".")
        return previous + " " + current.lstrip()
    
    # Tokenize both transcripts
    prev_tokens = tokenize(previous)
    curr_tokens = tokenize(current)
    
    # Find overlap
    overlap = find_overlap(prev_tokens, curr_tokens)
    
    if overlap > 0:
        # Remove overlapping tokens from current transcript
        curr_tokens = curr_tokens[overlap:]
        
        # If current becomes empty after dedup, return previous
        if not curr_tokens:
            return previous
        
        # Rejoin tokens
        return previous + " " + " ".join(curr_tokens)
    else:
        # No overlap, just concatenate
        return previous + " " + current


def clean_transcript(text: str) -> str:
    """
    Clean up transcript text
    
    - Remove extra whitespace
    - Fix punctuation spacing
    - Remove duplicate words at boundaries
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Fix punctuation spacing (e.g., "word ." -> "word.")
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    
    # Fix spacing after punctuation if missing
    text = re.sub(r'([.,!?;:])([A-Za-z])', r'\1 \2', text)
    
    return text


def ensure_space_before_text(previous: str, current: str) -> str:
    """
    Ensure proper spacing when concatenating text chunks
    
    Args:
        previous: Previous text chunk
        current: Current text chunk to append
        
    Returns:
        Current text with proper spacing
    """
    if not previous or not current:
        return current
    
    # Check if previous text ends with punctuation
    last_char = previous.rstrip()[-1] if previous.rstrip() else ''
    first_char = current.lstrip()[0] if current.lstrip() else ''
    
    # If previous ends with punctuation and current starts with letter, ensure space
    if last_char in '.!?;:,)]}' and first_char.isalpha():
        return ' ' + current.lstrip()
    
    # If previous ends with letter/number and current starts with letter/number, ensure space
    if last_char.isalnum() and first_char.isalnum():
        return ' ' + current.lstrip()
    
    return current


def test_deduplication():
    """Test the deduplication logic"""
    test_cases = [
        # (previous, current, expected)
        ("Hello world", "world how are", "Hello world how are"),
        ("I went to the", "to the store", "I went to the store"),
        ("Um...", "...I think", "Um... I think"),
        ("And then I", "I said hello", "And then I said hello"),
        ("Complete sentence.", "New sentence.", "Complete sentence. New sentence."),
    ]
    
    for prev, curr, expected in test_cases:
        result = deduplicate_transcripts(prev, curr)
        print(f"Previous: '{prev}'")
        print(f"Current:  '{curr}'")
        print(f"Result:   '{result}'")
        print(f"Expected: '{expected}'")
        print(f"Match: {result == expected}")
        print("-" * 40)


if __name__ == "__main__":
    test_deduplication()
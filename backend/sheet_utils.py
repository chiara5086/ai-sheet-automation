import re

def find_column_indices(headers, required_names):
    """
    Find column indices by matching required column names to headers.
    
    This function performs robust matching that:
    - Ignores case (case-insensitive)
    - Ignores extra whitespace
    - Handles regex patterns in required_names
    - Uses exact or substring matching for flexibility
    - Prioritizes more specific (longer) matches over generic ones
    
    Args:
        headers: List of header strings from the sheet
        required_names: List of column names or regex patterns to find
        
    Returns:
        Dictionary mapping required_names to their column indices (or None if not found)
    """
    indices = {}
    used_indices = set()  # Track which column indices have been assigned
    
    # Sort required_names by length (longest first) to prioritize specific matches
    sorted_names = sorted(required_names, key=lambda x: len(x), reverse=True)
    
    for name in sorted_names:
        found = False
        best_match_idx = None
        best_match_score = 0
        
        # Normalize the required name: remove spaces, convert to lowercase
        norm_name = ''.join(name.lower().split())
        
        # Try regex matching first if the name contains regex patterns
        if any(char in name for char in ['[', '(', '*', '+', '?', '^', '$']):
            try:
                pattern = re.compile(name, re.IGNORECASE)
                for idx, header in enumerate(headers):
                    if header and pattern.search(header) and idx not in used_indices:
                        indices[name] = idx
                        used_indices.add(idx)
                        found = True
                        break
            except re.error:
                # If regex is invalid, fall back to substring matching
                pass
        
        # If not found with regex, try matching
        if not found:
            for idx, header in enumerate(headers):
                if not header or idx in used_indices:
                    continue
                
                # Normalize header: remove spaces, convert to lowercase
                norm_header = ''.join(header.lower().split())
                
                # Try exact match first (highest priority)
                if norm_name == norm_header:
                    best_match_idx = idx
                    best_match_score = 100
                    found = True
                    break
                # Then try if normalized name is contained in normalized header
                elif norm_name and norm_name in norm_header:
                    # Score based on how much of the header matches
                    # Prefer matches where the name is a larger portion of the header
                    match_ratio = len(norm_name) / len(norm_header) if norm_header else 0
                    # Also prefer if header starts with the name (more specific)
                    starts_with_bonus = 10 if norm_header.startswith(norm_name) else 0
                    total_score = match_ratio * 100 + starts_with_bonus
                    if total_score > best_match_score:
                        best_match_idx = idx
                        best_match_score = total_score
        
        if best_match_idx is not None:
            indices[name] = best_match_idx
            used_indices.add(best_match_idx)
            found = True
        
        if not found:
            indices[name] = None
    
    return indices

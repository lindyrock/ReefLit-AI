"""Utility functions for ReefLit AI."""

def doi_to_filename(doi: str) -> str:
    """Convert DOI to filename format.
    
    Args:
        doi: DOI string (e.g., '10.3755/jcrs.20.89')
        
    Returns:
        Filename string (e.g., '10.3755_jcrs.20.89')
    """
    return doi.replace('/', '_')

def filename_to_doi(filename: str) -> str:
    """Convert filename to DOI format.
    
    Args:
        filename: Filename string (e.g., '10.3755_jcrs.20.89.txt')
        
    Returns:
        DOI string (e.g., '10.3755/jcrs.20.89')
    """
    # Remove .txt extension if present
    if filename.endswith('.txt'):
        filename = filename[:-4]
    
    # Split into prefix and suffix
    parts = filename.split('_', 1)
    if len(parts) != 2:
        return filename
    
    prefix, suffix = parts
    
    # Handle special cases
    if 'galaxea.g' in suffix:
        # For galaxea.g2020_s3r format
        return f"{prefix}/{suffix}"
    elif 'galaxea.' in suffix and '_' in suffix:
        # For galaxea.21.1_27 format
        return f"{prefix}/{suffix}"
    elif 'journal.' in suffix:
        # For journal.pone.0234567 format
        return f"{prefix}/{suffix}"
    elif 'fmars.' in suffix:
        # For fmars.2020.00001 format
        return f"{prefix}/{suffix}"
    elif 's41598-' in suffix:
        # For s41598-020-63625-0 format
        return f"{prefix}/{suffix}"
    elif 'pnas.' in suffix:
        # For pnas.091092998 format
        return f"{prefix}/{suffix}"
    else:
        # For standard format, replace remaining underscores with forward slashes
        return f"{prefix}/{suffix.replace('_', '/')}" 
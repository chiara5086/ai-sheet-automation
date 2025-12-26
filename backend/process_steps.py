
"""
Process Steps Module
-------------------
Contains modular functions for each process step in the asset sheet automation workflow.
All functions are documented and separated for clarity and maintainability.
"""

def build_description(rows, col_indices):
    """
    Step 1: Build Description
    
    Generates technical descriptions for assets using Perplexity (or OpenAI as fallback) based on asset name,
    technical specifications, and AI Data (if available). Only fills empty 'AI Description' cells.
    Prioritizes Perplexity if API key is available, falls back to OpenAI if not.
    
    Args:
        rows: List of data rows from the sheet
        col_indices: Dictionary mapping column names to their indices
        
    Returns:
        tuple: (updated_rows, errors)
            - updated_rows: List of rows with updated AI Description values
            - errors: List of error messages encountered during processing
    """
    print("DEBUG: build_description function called")
    from openai import OpenAI
    from config import OPENAI_API_KEY, PERPLEXITY_API_KEY
    import re
    
    # Try Perplexity first (since user has credits there), fall back to OpenAI if Perplexity not available
    use_perplexity = False
    api_key_clean = None
    
    if PERPLEXITY_API_KEY:
        api_key_clean = PERPLEXITY_API_KEY.strip()
        # Remove quotes if present
        if api_key_clean.startswith('"') and api_key_clean.endswith('"'):
            api_key_clean = api_key_clean[1:-1].strip()
        if api_key_clean.startswith("'") and api_key_clean.endswith("'"):
            api_key_clean = api_key_clean[1:-1].strip()
        
        # Perplexity API keys start with "pplx-"
        if api_key_clean and len(api_key_clean) > 10:
            if api_key_clean.startswith('pplx-'):
                use_perplexity = True
                key_preview = f"{api_key_clean[:10]}...{api_key_clean[-4:]}" if len(api_key_clean) > 14 else "***"
                print(f"DEBUG: ✅ Using Perplexity API for description generation (key preview: {key_preview}, length: {len(api_key_clean)})")
            else:
                print(f"DEBUG: Perplexity API key found but doesn't start with 'pplx-', trying OpenAI...")
        else:
            print(f"DEBUG: Perplexity API key found but appears invalid (too short), trying OpenAI...")
    
    # Fall back to OpenAI if Perplexity not available
    if not use_perplexity:
        if not OPENAI_API_KEY:
            error_msg = 'Neither Perplexity nor OpenAI API key configured. Please set PERPLEXITY_API_KEY or OPENAI_API_KEY in your .env file.'
            print(f"ERROR: {error_msg}")
            return rows, [error_msg]
        
        api_key_clean = OPENAI_API_KEY.strip()
        # Remove quotes and special characters
        if api_key_clean.startswith('"') and api_key_clean.endswith('"'):
            api_key_clean = api_key_clean[1:-1].strip()
        if api_key_clean.startswith("'") and api_key_clean.endswith("'"):
            api_key_clean = api_key_clean[1:-1].strip()
        if api_key_clean.startswith('<') and api_key_clean.endswith('>'):
            api_key_clean = api_key_clean[1:-1].strip()
        
        # Extract key if embedded in text
        if not api_key_clean.startswith('sk-'):
            match = re.search(r'sk-proj-[a-zA-Z0-9\-]{50,}', api_key_clean) or re.search(r'sk-[a-zA-Z0-9]{20,}', api_key_clean)
            if match:
                api_key_clean = match.group(0)
        
        if not api_key_clean.startswith('sk-'):
            error_msg = f'OpenAI API key format appears invalid. Keys should start with "sk-" or "sk-proj-".'
            print(f"ERROR: {error_msg}")
            return rows, [error_msg]
        
        print(f"DEBUG: Using OpenAI API (key length: {len(api_key_clean)})")
    
    try:
        if use_perplexity:
            print(f"DEBUG: Initializing Perplexity client...")
            client = OpenAI(
                api_key=api_key_clean,
                base_url="https://api.perplexity.ai"
            )
            print(f"DEBUG: Perplexity client initialized successfully")
        else:
            print(f"DEBUG: Initializing OpenAI client...")
            client = OpenAI(api_key=api_key_clean)
            print(f"DEBUG: OpenAI client initialized successfully")
    except Exception as e:
        error_msg = f'Failed to initialize API client: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg]

    errors = []
    
    desc_idx = col_indices.get('AI Description')
    tech_idx = col_indices.get('Technical Specifications')
    ai_data_idx = col_indices.get('AI Data')  # Optional
    asset_idx = None
    
    # Find the asset name/title column (T2/T3/T4) - case-insensitive, ignoring spaces
    for k, idx in col_indices.items():
        if idx is None:
            continue
        norm_key = ''.join(k.lower().split())
        if 'yomoemmodel' in norm_key:
            asset_idx = idx
            print(f"DEBUG: Found asset column using key '{k}' at index {idx}")
            break
    
    print(f"DEBUG: Column indices found:")
    print(f"  Asset (YOM OEM Model): {asset_idx}")
    print(f"  Technical Specifications: {tech_idx}")
    print(f"  AI Data: {ai_data_idx}")
    print(f"  AI Description: {desc_idx}")
    
    if desc_idx is None or tech_idx is None or asset_idx is None:
        error_msg = f'Missing required columns. Found: desc_idx={desc_idx}, tech_idx={tech_idx}, asset_idx={asset_idx}'
        errors.append(error_msg)
        print(f"ERROR: {error_msg}")
        return rows, errors

    def safe_get_cell(row, idx):
        """Safely extract cell value."""
        if idx is None:
            return ''
        if len(row) <= idx:
            return ''
        value = row[idx]
        if value is None:
            return ''
        return str(value).strip()
    
    processed_count = 0
    skipped_filled = 0
    skipped_missing_data = 0
    
    # Collect rows that need processing
    rows_to_process = []
    for i, row in enumerate(rows):
        row_num = i + 3
        # Skip if already filled
        if len(row) > desc_idx and row[desc_idx] and str(row[desc_idx]).strip():
            skipped_filled += 1
            continue
        
        # Get asset name, technical specs, and AI data (optional)
        asset = safe_get_cell(row, asset_idx)
        tech = safe_get_cell(row, tech_idx)
        ai_data = safe_get_cell(row, ai_data_idx)
        
        if not tech:
            skipped_missing_data += 1
            continue
        
        rows_to_process.append((i, row, row_num, asset, tech, ai_data))
    
    total_to_process = len(rows_to_process)
    print(f"DEBUG: Starting to process {total_to_process} rows (out of {len(rows)} total) for description generation...")
    print(f"DEBUG: Skipped {skipped_filled} rows (already filled), {skipped_missing_data} rows (missing data)")
    
    # Process in parallel batches of 20
    import asyncio
    from openai import AsyncOpenAI
    
    async def process_single_row(row_data):
        """Process a single row asynchronously."""
        i, row, row_num, asset, tech, ai_data = row_data
        
        # Build prompt
        raw_input = tech
        if ai_data:
            raw_input += f"\n\n{ai_data}"
        
        prompt = (
            "You are a technical documentation engineer writing for an industrial machinery catalog. "
            "For each item below, generate a single, objective technical description (200–250 words).\n"
            "Rules:\n"
            "- Start with: 'The [Asset Name] is a...' where [Asset Name] MUST be taken verbatim from the Asset Name field. — Do NOT restate or reformat the name.\n"
            "- Infer it from context if not explicit.\n"
            "- Immediately state its primary industrial application (e.g., 'engineered for quarry loading', 'designed for earthmoving in construction sites').\n"
            "- Then describe technical systems in prose: engine, transmission, hydraulics, capacities, dimensions, etc. — only if present in input.\n"
            "- Integrate specs into sentences (e.g., 'Powered by a... delivering... hp').\n"
            "- NEVER use subjective, promotional, or evaluative language (e.g., 'robust', 'powerful', 'efficient', 'top-performing').\n"
            "- Use only facts from 'Raw' or 'Clean' input. Do not invent data.\n"
            "- Output must be one paragraph. No bullets, dashes, markdown, or lists.\n"
            "- Output ONLY the description. No other text.\n\n"
            f"Asset Name: {asset}\n\n"
            f"Raw input:\n{raw_input}"
        )
        
        try:
            model_name = "sonar" if use_perplexity else "gpt-4o-mini"
            async_client = AsyncOpenAI(
                api_key=api_key_clean,
                base_url="https://api.perplexity.ai" if use_perplexity else None
            )
            
            response = await async_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.4
            )
            
            description = response.choices[0].message.content.strip()
            
            # Ensure row is long enough
            while len(row) <= desc_idx:
                row.append("")
            row[desc_idx] = description
            
            return (i, row_num, description, None)
        except Exception as e:
            error_detail = str(e)
            error_code = None
            
            if hasattr(e, 'status_code'):
                error_code = e.status_code
            elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                error_code = e.response.status_code
            
            return (i, row_num, None, (error_code, error_detail))
    
    async def process_batch(batch, batch_num, total_batches):
        """Process a batch of rows in parallel."""
        print(f"DEBUG: Processing batch {batch_num}/{total_batches} ({len(batch)} rows)...")
        tasks = [process_single_row(row_data) for row_data in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    # Process in batches of 20
    BATCH_SIZE = 20
    total_batches = (total_to_process + BATCH_SIZE - 1) // BATCH_SIZE
    
    async def process_all_batches():
        """Process all rows in batches."""
        all_results = []
        for batch_num in range(total_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, total_to_process)
            batch = rows_to_process[start_idx:end_idx]
            
            batch_results = await process_batch(batch, batch_num + 1, total_batches)
            all_results.extend(batch_results)
            
            processed_in_batch = sum(1 for r in batch_results if r and r[2] is not None)
            print(f"DEBUG: Batch {batch_num + 1}/{total_batches} completed: {processed_in_batch}/{len(batch)} rows processed")
        
        return all_results
    
    # Run async processing
    try:
        results = asyncio.run(process_all_batches())
    except Exception as e:
        error_msg = f'Failed to process batches: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg]
    
    # Process results
    for result in results:
        if isinstance(result, Exception):
            errors.append(f'Batch processing error: {str(result)}')
            continue
        
        if result is None:
            continue
        
        i, row_num, description, error_info = result
        
        if error_info:
            error_code, error_detail = error_info
            # Critical errors: stop processing immediately
            if error_code in [400, 401, 429]:
                if error_code == 401:
                    error_msg = f"CRITICAL: API authentication failed. Please check your API key. Error: {error_detail}"
                elif error_code == 400:
                    error_msg = f"CRITICAL: Invalid API request. Error: {error_detail}"
                elif error_code == 429:
                    error_msg = f"CRITICAL: API quota exceeded. Please check your API credits. Error: {error_detail}"
                else:
                    error_msg = f"CRITICAL: API error (code {error_code}). Error: {error_detail}"
                
                print(f"❌ {error_msg}")
                errors.append(error_msg)
                # Stop processing on critical errors
                return rows, errors
            
            # Non-critical errors
            error_msg = f'Row {row_num}: API error: {error_detail}'
            errors.append(error_msg)
            print(f"❌ {error_msg}")
        elif description:
            processed_count += 1
            print(f"✅ Row {row_num}: Successfully generated description ({len(description)} chars)")
    
    print(f"\n📊 Processing Summary:")
    print(f"  - Total rows processed: {len(rows)}")
    print(f"  - Rows with empty AI Description (candidates): {processed_count + skipped_filled}")
    print(f"  - Rows skipped (already have description): {skipped_filled}")
    print(f"  - Rows skipped (missing data): {skipped_missing_data}")
    print(f"  - Rows successfully filled with description: {processed_count - len([e for e in errors if 'Row' in e])}")
    print(f"  - Errors encountered: {len(errors)}")
    
    return rows, errors


def ai_source_comparables(rows, col_indices):
    """
    Step 2: AI Source Comparables
    
    Searches the web for comparable listings using Perplexity.
    Fills the 'AI Comparable Price' column with formatted comparable data.
    Only processes rows where 'AI Comparable Price' is empty.
    
    The function:
    - Uses Perplexity to search the web for comparable listings
    - Returns Condition, Price, and URL for each listing
    - Formats as: "Condition: [condition], Price: [price], URL: [link]"
    - Returns up to 10 recent results
    
    Args:
        rows: List of data rows from the sheet
        col_indices: Dictionary mapping column names to their indices
        
    Returns:
        tuple: (updated_rows, errors)
            - updated_rows: List of rows with updated AI Comparable Price values
            - errors: List of error messages encountered during processing
    """
    print("DEBUG: ai_source_comparables function called")
    from openai import OpenAI
    from config import OPENAI_API_KEY, PERPLEXITY_API_KEY
    import re
    
    # Perplexity is required for web search
    use_perplexity = False
    api_key_clean = None
    
    if PERPLEXITY_API_KEY:
        api_key_clean = PERPLEXITY_API_KEY.strip()
        # Remove quotes if present
        if api_key_clean.startswith('"') and api_key_clean.endswith('"'):
            api_key_clean = api_key_clean[1:-1].strip()
        if api_key_clean.startswith("'") and api_key_clean.endswith("'"):
            api_key_clean = api_key_clean[1:-1].strip()
        
        # Perplexity API keys start with "pplx-"
        if api_key_clean and len(api_key_clean) > 10:
            if api_key_clean.startswith('pplx-'):
                use_perplexity = True
                key_preview = f"{api_key_clean[:10]}...{api_key_clean[-4:]}" if len(api_key_clean) > 14 else "***"
                print(f"DEBUG: ✅ Using Perplexity API for comparables search (key preview: {key_preview}, length: {len(api_key_clean)})")
            else:
                print(f"DEBUG: Perplexity API key found but doesn't start with 'pplx-', trying OpenAI...")
        else:
            print(f"DEBUG: Perplexity API key found but appears invalid (too short), trying OpenAI...")
    
    # Fall back to OpenAI if Perplexity not available (but web search won't work as well)
    if not use_perplexity:
        if not OPENAI_API_KEY:
            error_msg = 'Perplexity API key required for web search. Please set PERPLEXITY_API_KEY in your .env file.'
            print(f"ERROR: {error_msg}")
            return rows, [error_msg]
        
        api_key_clean = OPENAI_API_KEY.strip()
        # Remove quotes and special characters
        if api_key_clean.startswith('"') and api_key_clean.endswith('"'):
            api_key_clean = api_key_clean[1:-1].strip()
        if api_key_clean.startswith("'") and api_key_clean.endswith("'"):
            api_key_clean = api_key_clean[1:-1].strip()
        if api_key_clean.startswith('<') and api_key_clean.endswith('>'):
            api_key_clean = api_key_clean[1:-1].strip()
        
        # Extract key if embedded in text
        if not api_key_clean.startswith('sk-'):
            match = re.search(r'sk-proj-[a-zA-Z0-9\-]{50,}', api_key_clean) or re.search(r'sk-[a-zA-Z0-9]{20,}', api_key_clean)
            if match:
                api_key_clean = match.group(0)
        
        if not api_key_clean.startswith('sk-'):
            error_msg = f'OpenAI API key format appears invalid. Keys should start with "sk-" or "sk-proj-".'
            print(f"ERROR: {error_msg}")
            return rows, [error_msg]
        
        print(f"DEBUG: Using OpenAI API (key length: {len(api_key_clean)}) - Note: web search may be limited")
    
    try:
        if use_perplexity:
            print(f"DEBUG: Initializing Perplexity client...")
            client = OpenAI(
                api_key=api_key_clean,
                base_url="https://api.perplexity.ai"
            )
            print(f"DEBUG: Perplexity client initialized successfully")
        else:
            print(f"DEBUG: Initializing OpenAI client...")
            client = OpenAI(api_key=api_key_clean)
            print(f"DEBUG: OpenAI client initialized successfully")
    except Exception as e:
        error_msg = f'Failed to initialize API client: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg]
    
    errors = []
    
    # Find asset column: any header containing 'yom oem model' (case-insensitive, ignoring ALL spaces)
    asset_idx = None
    for k, idx in col_indices.items():
        if idx is None:
            continue
        norm_key = ''.join(k.lower().split())
        if 'yomoemmodel' in norm_key:
            asset_idx = idx
            print(f"DEBUG: Found asset column using key '{k}' at index {idx}")
            break
    
    # Get other column indices
    tech_idx = col_indices.get('Technical Specifications')
    comparable_idx = col_indices.get('AI Comparable Price')
    
    print(f"DEBUG: Column indices found:")
    print(f"  Asset (YOM OEM Model): {asset_idx}")
    print(f"  Technical Specifications: {tech_idx}")
    print(f"  AI Comparable Price: {comparable_idx}")

    # Check required columns
    if asset_idx is None or tech_idx is None or comparable_idx is None:
        error_msg = f'Missing required columns. Found: asset_idx={asset_idx}, tech_idx={tech_idx}, comparable_idx={comparable_idx}'
        errors.append(error_msg)
        print(f"ERROR: {error_msg}")
        return rows, errors

    def safe_get_cell(row, idx):
        """Safely extract cell value."""
        if idx is None:
            return ''
        if len(row) <= idx:
            return ''
        value = row[idx]
        if value is None:
            return ''
        return str(value).strip()
    
    def is_comparable_cell_empty(row, comparable_idx):
        """Check if AI Comparable Price cell is empty."""
        if comparable_idx is None or len(row) <= comparable_idx:
            return True
        comparable_value = row[comparable_idx]
        if comparable_value is None:
            return True
        return not str(comparable_value).strip()
    
    processed_count = 0
    skipped_filled = 0
    skipped_missing_data = 0
    
    print(f"DEBUG: Starting to process {len(rows)} rows for comparables search...")
    
    # Use Perplexity model for web search
    model_name = "sonar" if use_perplexity else "gpt-4o-mini"
    print(f"DEBUG: Using model: {model_name}")
    
    for i, row in enumerate(rows):
        if i > 0 and i % 10 == 0:
            print(f"DEBUG: Processed {i}/{len(rows)} rows so far...")
        row_num = i + 3  # Row number in sheet (1-indexed, starting from row 3)
        
        # Only process rows where AI Comparable Price cell is EMPTY
        if not is_comparable_cell_empty(row, comparable_idx):
            skipped_filled += 1
            continue
        
        processed_count += 1
        
        # Extract required data
        asset = safe_get_cell(row, asset_idx)
        tech = safe_get_cell(row, tech_idx)
        
        # Skip if required data is missing
        if not asset or not tech:
            skipped_missing_data += 1
            print(f"DEBUG: Row {row_num}: Skipped - missing data (asset: {bool(asset)}, tech: {bool(tech)})")
            continue
        
        # Build prompt matching the original GPT for Sheets format
        prompt = f"""Search the web for this item. For each comparable listing, return ONLY: Condition, Price, and the Listing URL. No extra text. Format each on one line as: Condition: [condition], Price: [price], URL: [link]. Return up to 10 recent results.

Asset: {asset}
Technical Specifications: {tech}"""
        
        try:
            print(f"DEBUG: Row {row_num}: Calling API for comparables search...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a web search assistant. Search for comparable listings and return only Condition, Price, and URL for each listing, formatted as specified."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000  # More tokens for multiple listings
            )
            
            comparable_text = response.choices[0].message.content.strip()
            print(f"DEBUG: Row {row_num}: API response length: {len(comparable_text)} chars")
            
            if comparable_text:
                # Ensure row has enough columns
                while len(row) <= comparable_idx:
                    row.append("")
                
                # Store the comparable data
                row[comparable_idx] = comparable_text
                print(f"✅ Row {row_num}: Successfully found comparables ({len(comparable_text)} chars)")
            else:
                print(f"⚠️ Row {row_num}: No comparables found")
        
        except Exception as e:
            error_detail = str(e)
            error_code = None
            
            # Check for API errors
            if hasattr(e, 'status_code'):
                error_code = e.status_code
            elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                error_code = e.response.status_code
            
            # Critical errors: stop processing immediately
            if error_code in [400, 401, 429]:
                if error_code == 401:
                    error_msg = f"CRITICAL: API authentication failed. Please check your API key. Error: {error_detail}"
                elif error_code == 400:
                    error_msg = f"CRITICAL: Invalid API request (possibly invalid model). Error: {error_detail}"
                elif error_code == 429:
                    error_msg = f"CRITICAL: API quota exceeded. Please check your API credits. Error: {error_detail}"
                else:
                    error_msg = f"CRITICAL: API error (code {error_code}). Error: {error_detail}"
                
                print(f"❌ {error_msg}")
                errors.append(error_msg)
                # Stop processing on critical errors
                return rows, errors
            
            # Non-critical errors: log and continue
            error_msg = f'Row {row_num}: API error: {error_detail}'
            errors.append(error_msg)
            print(f"❌ {error_msg}")
    
    print(f"\n📊 Processing Summary:")
    print(f"  - Total rows processed: {len(rows)}")
    print(f"  - Rows with empty AI Comparable Price (candidates): {processed_count + skipped_filled}")
    print(f"  - Rows skipped (already have comparables): {skipped_filled}")
    print(f"  - Rows skipped (missing data): {skipped_missing_data}")
    print(f"  - Rows successfully filled with comparables: {processed_count - skipped_missing_data - len([e for e in errors if 'Row' in e])}")
    print(f"  - Errors encountered: {len(errors)}")
    
    return rows, errors


def extract_final_price(rows, col_indices):
    """
    Step 3: Extract Price from AI Comparable
    
    Analyzes asset details, technical specifications, and comparable listings using OpenAI
    to extract the most relevant price. Only processes rows where the 'Price' column is empty.
    
    The function:
    - Uses OpenAI to intelligently select the best price from comparable listings
    - Converts prices to USD if needed
    - Validates and normalizes the extracted price
    - Only fills empty Price cells (skips rows that already have a price)
    
    Args:
        rows: List of data rows from the sheet
        col_indices: Dictionary mapping column names to their indices
        
    Returns:
        tuple: (updated_rows, errors, filled_rows)
            - updated_rows: List of rows with updated Price values
            - errors: List of error messages encountered during processing
            - filled_rows: List of row numbers (1-indexed) that were successfully filled
    """
    print("DEBUG: extract_final_price function called")
    from openai import OpenAI
    from config import OPENAI_API_KEY, PERPLEXITY_API_KEY
    import re
    
    print("DEBUG: Imports successful, checking API key...")
    print(f"DEBUG: PERPLEXITY_API_KEY exists: {PERPLEXITY_API_KEY is not None}")
    if PERPLEXITY_API_KEY:
        print(f"DEBUG: PERPLEXITY_API_KEY length: {len(PERPLEXITY_API_KEY)}")
        print(f"DEBUG: PERPLEXITY_API_KEY starts with 'pplx-': {PERPLEXITY_API_KEY.startswith('pplx-')}")
        print(f"DEBUG: PERPLEXITY_API_KEY preview: {PERPLEXITY_API_KEY[:10]}..." if len(PERPLEXITY_API_KEY) > 10 else "DEBUG: PERPLEXITY_API_KEY too short")
    
    # Try Perplexity first, fall back to OpenAI if Perplexity not available
    use_perplexity = False
    api_key_clean = None
    
    if PERPLEXITY_API_KEY:
        api_key_clean = PERPLEXITY_API_KEY.strip()
        # Remove quotes if present
        if api_key_clean.startswith('"') and api_key_clean.endswith('"'):
            api_key_clean = api_key_clean[1:-1].strip()
        if api_key_clean.startswith("'") and api_key_clean.endswith("'"):
            api_key_clean = api_key_clean[1:-1].strip()
        
        # Perplexity API keys start with "pplx-"
        if api_key_clean and len(api_key_clean) > 10:
            if api_key_clean.startswith('pplx-'):
                use_perplexity = True
                key_preview = f"{api_key_clean[:10]}...{api_key_clean[-4:]}" if len(api_key_clean) > 14 else "***"
                print(f"DEBUG: ✅ Using Perplexity API (key preview: {key_preview}, length: {len(api_key_clean)})")
            else:
                print(f"DEBUG: Perplexity API key found but doesn't start with 'pplx-', trying OpenAI...")
        else:
            print(f"DEBUG: Perplexity API key found but appears invalid (too short), trying OpenAI...")
    
    # Fall back to OpenAI if Perplexity not available
    if not use_perplexity:
        if not OPENAI_API_KEY:
            error_msg = 'Neither Perplexity nor OpenAI API key configured. Please set PERPLEXITY_API_KEY or OPENAI_API_KEY in your .env file.'
            print(f"ERROR: {error_msg}")
            return rows, [error_msg], []
        
        api_key_clean = OPENAI_API_KEY.strip()
        # Remove quotes and special characters
        if api_key_clean.startswith('"') and api_key_clean.endswith('"'):
            api_key_clean = api_key_clean[1:-1].strip()
        if api_key_clean.startswith("'") and api_key_clean.endswith("'"):
            api_key_clean = api_key_clean[1:-1].strip()
        if api_key_clean.startswith('<') and api_key_clean.endswith('>'):
            api_key_clean = api_key_clean[1:-1].strip()
        
        # Extract key if embedded in text
        if not api_key_clean.startswith('sk-'):
            match = re.search(r'sk-proj-[a-zA-Z0-9\-]{50,}', api_key_clean) or re.search(r'sk-[a-zA-Z0-9]{20,}', api_key_clean)
            if match:
                api_key_clean = match.group(0)
        
        if not api_key_clean.startswith('sk-'):
            error_msg = f'OpenAI API key format appears invalid. Keys should start with "sk-" or "sk-proj-".'
            print(f"ERROR: {error_msg}")
            return rows, [error_msg], []
        
        print(f"DEBUG: Using OpenAI API (key length: {len(api_key_clean)})")
    
    try:
        if use_perplexity:
            # Perplexity uses OpenAI-compatible API but different base URL
            print(f"DEBUG: Initializing Perplexity client...")
            client = OpenAI(
                api_key=api_key_clean,
                base_url="https://api.perplexity.ai"
            )
            print(f"DEBUG: Perplexity client initialized successfully")
        else:
            print(f"DEBUG: Initializing OpenAI client...")
            client = OpenAI(api_key=api_key_clean)
            print(f"DEBUG: OpenAI client initialized successfully")
    except Exception as e:
        error_msg = f'Failed to initialize API client: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    errors = []
    filled_rows = []

    # Find asset column: any header containing 'yom oem model' (case-insensitive, ignoring ALL spaces)
    # The col_indices dict should already have the correct mapping from routes.py
    # But we need to find it by checking the actual key that was used
    asset_idx = None
    for k, idx in col_indices.items():
        if idx is None:
            continue
        # Check if this key matches the asset pattern
        norm_key = ''.join(k.lower().split())
        if 'yomoemmodel' in norm_key:
            asset_idx = idx
            print(f"DEBUG: Found asset column using key '{k}' at index {idx}")
            break
    
    # Get other column indices - these should be found by name
    tech_idx = col_indices.get('Technical Specifications')
    ai_data_idx = col_indices.get('AI Data')
    comparable_idx = col_indices.get('AI Comparable Price')
    price_idx = col_indices.get('Price')
    
    # Debug: Print what we found
    print(f"DEBUG: Column indices found:")
    print(f"  Asset (YOM OEM Model): {asset_idx}")
    print(f"  Technical Specifications: {tech_idx}")
    print(f"  AI Data: {ai_data_idx}")
    print(f"  AI Comparable Price: {comparable_idx}")
    print(f"  Price: {price_idx}")

    # Check required columns
    if asset_idx is None or tech_idx is None or comparable_idx is None or price_idx is None:
        error_msg = f'Missing required columns. Found: asset_idx={asset_idx}, tech_idx={tech_idx}, comparable_idx={comparable_idx}, price_idx={price_idx}'
        errors.append(error_msg)
        print(f"ERROR: {error_msg}")  # Debug log
        print(f"DEBUG: Available columns: {list(col_indices.keys())}")  # Debug log
        return rows, errors, filled_rows

    print(f"DEBUG: Column indices - Asset: {asset_idx}, Tech: {tech_idx}, Comparable: {comparable_idx}, Price: {price_idx}")  # Debug log

    def normalize_price(price_str):
        """
        Extract numeric price value from various formats.
        Handles currency symbols, commas, and different number formats.
        Returns the price as a float or None if invalid.
        """
        if not price_str:
            return None
        
        # Remove common currency symbols and text
        price_str = str(price_str).strip()
        # Remove currency symbols ($, €, £, etc.)
        price_str = re.sub(r'[$€£¥₹]', '', price_str)
        # Remove commas and spaces
        price_str = re.sub(r'[, ]', '', price_str)
        # Extract first number (handles formats like "USD 50000" or "50000.00 USD")
        match = re.search(r'(\d+\.?\d*)', price_str)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def is_price_cell_empty(row, price_idx):
        """Check if the Price cell is empty or contains only whitespace."""
        if len(row) <= price_idx:
            return True
        price_value = str(row[price_idx]).strip() if row[price_idx] else ''
        return not price_value

    # Helper function to safely extract cell values
    def safe_get_cell(row, idx):
        """Safely extract cell value, handling None, empty strings, and missing indices."""
        if idx is None:
            return ''
        if len(row) <= idx:
            return ''
        value = row[idx]
        if value is None:
            return ''
        # Convert to string and strip whitespace
        return str(value).strip()
    
    processed_count = 0
    skipped_empty_price = 0
    skipped_missing_data = 0
    
    print(f"DEBUG: Starting to process {len(rows)} rows...")

    for i, row in enumerate(rows):
        # Log progress every 10 rows
        if i > 0 and i % 10 == 0:
            print(f"DEBUG: Processed {i}/{len(rows)} rows so far...")
        row_num = i + 3  # Row number in sheet (1-indexed, starting from row 3)
        
        # STEP 1: Only process rows where Price cell is EMPTY (we want to fill empty prices)
        if not is_price_cell_empty(row, price_idx):
            skipped_empty_price += 1
            continue  # Skip rows that already have a price
        
        processed_count += 1
        
        # STEP 2: Extract required data from the row
        # All columns are found by NAME, not by position, so they can be in any order
        asset = safe_get_cell(row, asset_idx)
        tech = safe_get_cell(row, tech_idx)
        ai_data = safe_get_cell(row, ai_data_idx)  # Optional but used if available
        comparable = safe_get_cell(row, comparable_idx)
        
        # STEP 3: Skip if required data is missing (can't extract price without this info)
        # Note: AI Data is optional, but Asset, Tech Specs, and Comparable are required
        if not asset or not tech or not comparable:
            skipped_missing_data += 1
            missing_fields = []
            if not asset: missing_fields.append("Asset")
            if not tech: missing_fields.append("Technical Specifications")
            if not comparable: missing_fields.append("AI Comparable Price")
            # Only log first few to avoid spam
            if skipped_missing_data <= 5:
                print(f"⚠️ Row {row_num}: Skipping - missing: {', '.join(missing_fields)}")
            continue  # Skip rows with missing required data
        
        # Build prompt matching the original GPT for Sheets format
        prompt = (
            "You are an expert in construction equipment valuation. Read the asset details, technical specs, and comparable listings below. "
            "Choose the single most relevant price, convert it to USD if needed, and return ONLY the final USD amount formatted like 'XXXXXX.XX'. "
            "If no relevant price exists, return blank. Do not add any explanation, note, or extra text.\n"
            f"Asset details:\n{asset}\n"
            f"Technical specifications:\n{tech}\n"
            f"Comparable listings found online:\n{comparable}\n"
        )
        
        if ai_data:
            prompt += f"AI Data:\n{ai_data}\n"
        
        try:
            # Use Perplexity model if available, otherwise OpenAI
            if use_perplexity:
                # Perplexity models: Try "sonar" first (as used in original script), fallback to sonar-large-online
                model = "sonar"  # Perplexity model with web search (as used in original script)
            else:
                model = "gpt-4o-mini"  # OpenAI model
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise pricing analyst. Always return only numeric values in USD format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=50,
                temperature=0.1  # Low temperature for consistent, focused responses
            )
            
            price_text = response.choices[0].message.content.strip()
            
            # Handle "NONE" or empty responses
            if not price_text or price_text.upper() in ['NONE', 'N/A', 'NA', '']:
                continue
            
            # Normalize and validate the extracted price
            normalized_price = normalize_price(price_text)
            
            if normalized_price is not None and normalized_price > 0:
                # Format price to 2 decimal places (matching original format XXXXXX.XX)
                formatted_price = f"{normalized_price:.2f}"
                
                # Ensure row is long enough
                while len(row) <= price_idx:
                    row.append("")
                
                # Store the price in the row data
                row[price_idx] = formatted_price
                filled_rows.append(row_num)  # Track which rows we successfully filled
                print(f"✅ Row {row_num}: Successfully extracted price ${formatted_price}")  # Debug log
            else:
                # Only log if we got a response but couldn't parse it
                if price_text:
                    errors.append(f'Row {row_num}: Could not extract valid price from response: "{price_text}"')
                    print(f"⚠️ Row {row_num}: Invalid price format: '{price_text}'")  # Debug log
                    
        except Exception as api_error:
            # Check if it's a critical error that should stop processing
            error_str = str(api_error)
            error_code = getattr(api_error, 'status_code', None) or getattr(api_error.response, 'status_code', None) if hasattr(api_error, 'response') else None
            error_detail = getattr(api_error, 'body', None) or (getattr(api_error.response, 'json', lambda: {})() if hasattr(api_error, 'response') and hasattr(api_error.response, 'json') else {})
            api_name = "Perplexity" if use_perplexity else "OpenAI"
            
            # Check for critical errors (authentication, invalid model, quota exceeded)
            is_critical = False
            critical_msg = ""
            
            if error_code == 401 or 'invalid_api_key' in error_str.lower() or 'incorrect api key' in error_str.lower():
                is_critical = True
                critical_msg = f'{api_name} API key authentication failed.'
            elif error_code == 400 and ('invalid model' in error_str.lower() or 'invalid_model' in str(error_detail).lower()):
                is_critical = True
                critical_msg = f'{api_name} API model "{model}" is invalid. Please check the model name.'
            elif error_code == 429 or 'quota' in error_str.lower() or 'insufficient_quota' in str(error_detail).lower():
                is_critical = True
                critical_msg = f'{api_name} API quota exceeded. Please add credits to your account.'
            
            if is_critical:
                errors.append(critical_msg)
                print(f"\n[CRITICAL ERROR] {critical_msg}")
                print(f"   Error code: {error_code}")
                print(f"   Error details: {error_str}")
                if 'invalid model' in error_str.lower():
                    print(f"   Model used: {model}")
                    if use_perplexity:
                        print("   Check Perplexity docs: https://docs.perplexity.ai/getting-started/models")
                print("   Stopping processing to avoid wasting API calls.\n")
                return rows, errors, filled_rows
            
            # For non-critical errors, log and continue
            error_msg = f'{api_name} API error: Error code: {error_code} - {error_detail}'
            errors.append(f'Row {row_num}: {error_msg}')
            print(f"[WARNING] Row {row_num}: {error_msg}")
            continue
    
    # Summary logging
    print(f"\n📊 Processing Summary:")
    print(f"   - Total rows processed: {len(rows)}")
    print(f"   - Rows with empty Price (candidates): {processed_count}")
    print(f"   - Rows skipped (already have price): {skipped_empty_price}")
    print(f"   - Rows skipped (missing data): {skipped_missing_data}")
    print(f"   - Rows successfully filled with price: {len(filled_rows)}")
    print(f"   - Errors encountered: {len(errors)}\n")
    
    return rows, errors, filled_rows


def ai_source_new_price(rows, col_indices):
    """
    Step 4: AI Source New Price
    
    Searches the web for the current market price of a BRAND NEW unit using Perplexity.
    Only processes rows where the 'Price' column is empty.
    
    The function:
    - Uses Perplexity to search the web for brand new equipment prices
    - Returns only the price in USD format (XXXXXX.XX)
    - Only fills empty Price cells (skips rows that already have a price)
    
    Args:
        rows: List of data rows from the sheet
        col_indices: Dictionary mapping column names to their indices
        
    Returns:
        tuple: (updated_rows, errors, filled_rows)
            - updated_rows: List of rows with updated Price values
            - errors: List of error messages encountered during processing
            - filled_rows: List of row numbers (1-indexed) that were successfully filled
    """
    print("DEBUG: ai_source_new_price function called")
    from openai import OpenAI
    from config import OPENAI_API_KEY, PERPLEXITY_API_KEY
    import re
    
    # Try Perplexity first (required for web search), fall back to OpenAI if Perplexity not available
    use_perplexity = False
    api_key_clean = None
    
    if PERPLEXITY_API_KEY:
        api_key_clean = PERPLEXITY_API_KEY.strip()
        # Remove quotes if present
        if api_key_clean.startswith('"') and api_key_clean.endswith('"'):
            api_key_clean = api_key_clean[1:-1].strip()
        if api_key_clean.startswith("'") and api_key_clean.endswith("'"):
            api_key_clean = api_key_clean[1:-1].strip()
        
        # Perplexity API keys start with "pplx-"
        if api_key_clean and len(api_key_clean) > 10:
            if api_key_clean.startswith('pplx-'):
                use_perplexity = True
                key_preview = f"{api_key_clean[:10]}...{api_key_clean[-4:]}" if len(api_key_clean) > 14 else "***"
                print(f"DEBUG: ✅ Using Perplexity API for new price search (key preview: {key_preview}, length: {len(api_key_clean)})")
            else:
                print(f"DEBUG: Perplexity API key found but doesn't start with 'pplx-', trying OpenAI...")
        else:
            print(f"DEBUG: Perplexity API key found but appears invalid (too short), trying OpenAI...")
    
    # Fall back to OpenAI if Perplexity not available
    if not use_perplexity:
        if not OPENAI_API_KEY:
            error_msg = 'Perplexity API key required for web search. Please set PERPLEXITY_API_KEY in your .env file.'
            print(f"ERROR: {error_msg}")
            return rows, [error_msg], []
        
        api_key_clean = OPENAI_API_KEY.strip()
        # Remove quotes and special characters
        if api_key_clean.startswith('"') and api_key_clean.endswith('"'):
            api_key_clean = api_key_clean[1:-1].strip()
        if api_key_clean.startswith("'") and api_key_clean.endswith("'"):
            api_key_clean = api_key_clean[1:-1].strip()
        if api_key_clean.startswith('<') and api_key_clean.endswith('>'):
            api_key_clean = api_key_clean[1:-1].strip()
        
        # Extract key if embedded in text
        if not api_key_clean.startswith('sk-'):
            match = re.search(r'sk-proj-[a-zA-Z0-9\-]{50,}', api_key_clean) or re.search(r'sk-[a-zA-Z0-9]{20,}', api_key_clean)
            if match:
                api_key_clean = match.group(0)
        
        if not api_key_clean.startswith('sk-'):
            error_msg = f'OpenAI API key format appears invalid. Keys should start with "sk-" or "sk-proj-".'
            print(f"ERROR: {error_msg}")
            return rows, [error_msg], []
        
        print(f"DEBUG: Using OpenAI API (key length: {len(api_key_clean)})")
    
    try:
        if use_perplexity:
            print(f"DEBUG: Initializing Perplexity client...")
            client = OpenAI(
                api_key=api_key_clean,
                base_url="https://api.perplexity.ai"
            )
            print(f"DEBUG: Perplexity client initialized successfully")
        else:
            print(f"DEBUG: Initializing OpenAI client...")
            client = OpenAI(api_key=api_key_clean)
            print(f"DEBUG: OpenAI client initialized successfully")
    except Exception as e:
        error_msg = f'Failed to initialize API client: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    
    errors = []
    filled_rows = []

    # Find asset column: any header containing 'yom oem model' (case-insensitive, ignoring ALL spaces)
    asset_idx = None
    for k, idx in col_indices.items():
        if idx is None:
            continue
        norm_key = ''.join(k.lower().split())
        if 'yomoemmodel' in norm_key:
            asset_idx = idx
            print(f"DEBUG: Found asset column using key '{k}' at index {idx}")
            break
    
    # Get other column indices
    tech_idx = col_indices.get('Technical Specifications')
    ai_data_idx = col_indices.get('AI Data')
    price_idx = col_indices.get('Price')
    
    print(f"DEBUG: Column indices found:")
    print(f"  Asset (YOM OEM Model): {asset_idx}")
    print(f"  Technical Specifications: {tech_idx}")
    print(f"  AI Data: {ai_data_idx}")
    print(f"  Price: {price_idx}")

    # Check required columns
    if asset_idx is None or tech_idx is None or price_idx is None:
        error_msg = f'Missing required columns. Found: asset_idx={asset_idx}, tech_idx={tech_idx}, price_idx={price_idx}'
        errors.append(error_msg)
        print(f"ERROR: {error_msg}")
        return rows, errors, filled_rows

    def normalize_price(price_str):
        """Extract numeric price value from various formats."""
        if not price_str:
            return None
        
        price_str = str(price_str).strip()
        price_str = re.sub(r'[$€£¥₹]', '', price_str)
        price_str = re.sub(r'[, ]', '', price_str)
        match = re.search(r'(\d+\.?\d*)', price_str)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def is_price_cell_empty(row, price_idx):
        """Check if Price cell is empty."""
        if price_idx is None or len(row) <= price_idx:
            return True
        price_value = row[price_idx]
        if price_value is None:
            return True
        return not str(price_value).strip()

    def safe_get_cell(row, idx):
        """Safely extract cell value."""
        if idx is None:
            return ''
        if len(row) <= idx:
            return ''
        value = row[idx]
        if value is None:
            return ''
        return str(value).strip()
    
    processed_count = 0
    skipped_empty_price = 0
    skipped_missing_data = 0
    
    print(f"DEBUG: Starting to process {len(rows)} rows for new price search...")
    print(f"DEBUG: Price column index: {price_idx}")
    
    # Count empty rows first for debugging
    empty_count = 0
    for row in rows:
        if is_price_cell_empty(row, price_idx):
            empty_count += 1
    print(f"DEBUG: Found {empty_count} rows with empty Price column")
    
    # Use Perplexity model for web search
    model_name = "sonar" if use_perplexity else "gpt-4o-mini"
    print(f"DEBUG: Using model: {model_name}")
    
    for i, row in enumerate(rows):
        if i > 0 and i % 10 == 0:
            print(f"DEBUG: Processed {i}/{len(rows)} rows so far...")
        row_num = i + 3  # Row number in sheet (1-indexed, starting from row 3)
        
        # Only process rows where Price cell is EMPTY
        if not is_price_cell_empty(row, price_idx):
            skipped_empty_price += 1
            continue
        
        processed_count += 1
        
        # Extract required data
        asset = safe_get_cell(row, asset_idx)
        tech = safe_get_cell(row, tech_idx)
        ai_data = safe_get_cell(row, ai_data_idx)  # Optional
        
        # Skip if required data is missing
        if not asset or not tech:
            skipped_missing_data += 1
            print(f"DEBUG: Row {row_num}: Skipped - missing data (asset: {bool(asset)}, tech: {bool(tech)})")
            continue
        
        # Build prompt for brand new price search
        prompt = f"""You are an expert in construction equipment valuation. Based ONLY on the asset details below, return the current market price of a BRAND NEW unit in USD. Return ONLY the price formatted exactly like this: 'XXXXXX.XX'. If no explicit new price is available, return blank. Do not add any words, explanations, notes, or symbols. Do not say 'blank', 'N/A', or anything else. Only output the price or nothing.

Asset details: {asset}
Technical specifications: {tech}"""
        
        if ai_data:
            prompt += f"\nAdditional AI data: {ai_data}"
        
        try:
            print(f"DEBUG: Row {row_num}: Calling API for new price search...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are an expert in construction equipment valuation. Return only numeric prices in USD format (XXXXXX.XX), or nothing if unavailable."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            price_text = response.choices[0].message.content.strip()
            print(f"DEBUG: Row {row_num}: API response: '{price_text}'")
            
            # Extract price
            price_value = normalize_price(price_text)
            print(f"DEBUG: Row {row_num}: Normalized price value: {price_value}")
            
            if price_value and price_value > 0:
                # Format as XXXXXX.XX
                formatted_price = f"{price_value:.2f}"
                
                # Ensure row has enough columns
                while len(row) <= price_idx:
                    row.append("")
                
                # Store the price in the row data
                row[price_idx] = formatted_price
                filled_rows.append(row_num)
                print(f"✅ Row {row_num}: Successfully found new price ${formatted_price}")
            else:
                print(f"⚠️ Row {row_num}: No valid new price found (response: '{price_text}', normalized: {price_value})")
        
        except Exception as e:
            error_detail = str(e)
            error_code = None
            
            # Check for API errors
            if hasattr(e, 'status_code'):
                error_code = e.status_code
            elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                error_code = e.response.status_code
            
            # Critical errors: stop processing immediately
            if error_code in [400, 401, 429]:
                if error_code == 401:
                    error_msg = f"CRITICAL: API authentication failed. Please check your API key. Error: {error_detail}"
                elif error_code == 400:
                    error_msg = f"CRITICAL: Invalid API request (possibly invalid model). Error: {error_detail}"
                elif error_code == 429:
                    error_msg = f"CRITICAL: API quota exceeded. Please check your API credits. Error: {error_detail}"
                else:
                    error_msg = f"CRITICAL: API error (code {error_code}). Error: {error_detail}"
                
                print(f"❌ {error_msg}")
                errors.append(error_msg)
                # Stop processing on critical errors
                return rows, errors, filled_rows
            
            # Non-critical errors: log and continue
            error_msg = f'Row {row_num}: API error: {error_detail}'
            errors.append(error_msg)
            print(f"❌ {error_msg}")
    
    print(f"\n📊 Processing Summary:")
    print(f"  - Total rows processed: {len(rows)}")
    print(f"  - Rows with empty Price (candidates): {processed_count + skipped_empty_price}")
    print(f"  - Rows skipped (already have price): {skipped_empty_price}")
    print(f"  - Rows skipped (missing data): {skipped_missing_data}")
    print(f"  - Rows successfully filled with price: {len(filled_rows)}")
    print(f"  - Errors encountered: {len(errors)}")
    
    return rows, errors, filled_rows


def ai_similar_comparable(rows, col_indices):
    """
    Step 5: AI Similar Comparable
    Finds similar asset prices online if no direct comparable found (light orange cell).
    Fills 'Price' only for cells still empty after previous step.
    Returns updated rows and a list of errors, and a list of filled row indices.
    """
    # TODO: Implement similar comparable logic
    pass

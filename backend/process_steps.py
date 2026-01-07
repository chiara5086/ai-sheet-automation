
"""
Process Steps Module
-------------------
Contains modular functions for each process step in the asset sheet automation workflow.
All functions are documented and separated for clarity and maintainability.
"""

import re

def clean_ai_data_response(text):
    """
    Clean AI data response by removing unwanted elements:
    - Navigation links like "(See all... for sale)"
    - Text in square brackets like "[Raw Trusted Data]"
    - Category/MANUFACTURER/MODEL header lines that don't contain specs
    - Any other navigation or meta-text
    """
    if not text:
        return text
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        original_line = line.strip()
        if not original_line:
            continue
        
        # Remove text in square brackets (e.g., "[Raw Trusted Data]")
        line = re.sub(r'\[.*?\]', '', line)
        
        # Remove navigation links in parentheses - be more aggressive
        line = re.sub(r'\(See all.*?\)', '', line, flags=re.IGNORECASE)
        line = re.sub(r'\(See all.*?for sale\)', '', line, flags=re.IGNORECASE)
        line = re.sub(r'\(View.*?\)', '', line, flags=re.IGNORECASE)
        line = re.sub(r'\(.*?for sale.*?\)', '', line, flags=re.IGNORECASE)
        line = re.sub(r'\(.*?Equipment for sale.*?\)', '', line, flags=re.IGNORECASE)
        
        # Remove entire lines that are only category headers without specs
        # These are lines that start with **CATEGORY:**, **MANUFACTURER:**, or **MODEL:** 
        # and don't contain actual specification values
        if re.match(r'^\s*\*\*?(CATEGORY|MANUFACTURER|MODEL):\*\*?\s*', line, re.IGNORECASE):
            # Check if it contains actual specs (numbers, units, etc.)
            has_specs = bool(re.search(r'\d+\s*(hp|kw|lbs|ft|in|gal|gpm|psi|deg|mph|kph|cu\s*(yd|in)|rpm|amps|volts)', line, re.IGNORECASE))
            if not has_specs:
                continue  # Skip this line, it's just a header
        
        # Remove any remaining navigation text patterns
        line = re.sub(r'See all.*?for sale', '', line, flags=re.IGNORECASE)
        line = re.sub(r'See all.*?Equipment', '', line, flags=re.IGNORECASE)
        
        # Clean up any remaining extra spaces
        line = re.sub(r'\s+', ' ', line).strip()
        
        # Remove lines that are too short or are just navigation text
        if len(line) < 3:
            continue
        
        # Only add lines that look like actual specifications
        # They should contain numbers or be bullet points with content
        # Be less strict - accept any line that has content and looks like a spec
        if (line.startswith('-') or line.startswith('*') or 
            re.search(r'\d+', line) or 
            (len(line) > 10 and ':' in line)):  # Also accept lines with colons (spec: value format)
            cleaned_lines.append(line)
    
    # Join lines back together
    cleaned_text = '\n'.join(cleaned_lines)
    
    # Final cleanup: preserve line breaks but clean up excessive spacing
    # Only collapse multiple spaces within a line, not across lines
    lines = cleaned_text.split('\n')
    cleaned_lines_final = []
    for line in lines:
        # Collapse multiple spaces to single space within each line
        line = re.sub(r' +', ' ', line.strip())
        if line:  # Only add non-empty lines
            cleaned_lines_final.append(line)
    
    cleaned_text = '\n'.join(cleaned_lines_final)
    
    # Remove excessive blank lines (more than 2 consecutive newlines)
    cleaned_text = re.sub(r'\n\n\n+', '\n\n', cleaned_text)
    
    return cleaned_text.strip()

async def generate_ai_data(rows, col_indices, session_id=None, custom_prompt=None):
    """
    Step 0: Generate AI Data
    
    Searches for official OEM technical specifications using Gemini.
    Fills the 'AI Data' column with verified technical specifications.
    Only processes rows where 'AI Data' is empty.
    
    Args:
        rows: List of data rows from the sheet
        col_indices: Dictionary mapping column names to their indices
        session_id: Optional session ID for WebSocket progress updates
        custom_prompt: Optional custom prompt to use instead of default
        
    Returns:
        tuple: (updated_rows, errors, stats)
            - updated_rows: List of rows with updated AI Data values
            - errors: List of error messages encountered during processing
            - stats: Dictionary with processing statistics
    """
    print("DEBUG: generate_ai_data function called")
    import google.generativeai as genai
    from config import GEMINI_API_KEY
    import re
    
    # Gemini is required for this step
    if not GEMINI_API_KEY:
        error_msg = 'Gemini API key required. Please set GEMINI_API_KEY in your .env file.'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], {"total": len(rows), "processed": 0, "success": 0, "skipped": 0, "errors_count": 1}
    
    api_key_clean = GEMINI_API_KEY.strip()
    # Remove quotes if present
    if api_key_clean.startswith('"') and api_key_clean.endswith('"'):
        api_key_clean = api_key_clean[1:-1].strip()
    if api_key_clean.startswith("'") and api_key_clean.endswith("'"):
        api_key_clean = api_key_clean[1:-1].strip()
    
    # Gemini API keys start with "AIzaSy"
    if not api_key_clean or len(api_key_clean) <= 10 or not api_key_clean.startswith('AIzaSy'):
        error_msg = 'Invalid Gemini API key. Keys must start with "AIzaSy" and be at least 10 characters long.'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], {"total": len(rows), "processed": 0, "success": 0, "skipped": 0, "errors_count": 1}
    
    key_preview = f"{api_key_clean[:10]}...{api_key_clean[-4:]}" if len(api_key_clean) > 14 else "***"
    print(f"DEBUG: ✅ Using Gemini API for AI Data generation (key preview: {key_preview}, length: {len(api_key_clean)})")
    
    try:
        print(f"DEBUG: Initializing Gemini client...")
        genai.configure(api_key=api_key_clean)
        print(f"DEBUG: Gemini client initialized successfully")
    except Exception as e:
        error_msg = f'Failed to initialize API client: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], {"total": len(rows), "processed": 0, "success": 0, "skipped": 0, "errors_count": 1}
    
    errors = []
    
    # Find asset column: starts with "YOM > OEM > MODEL"
    asset_name_key = 'YOM > OEM > MODEL'
    asset_idx = col_indices.get(asset_name_key)
    if asset_idx is None:
        # Fallback: try to find by pattern matching
        for k, idx in col_indices.items():
            if idx is None:
                continue
            norm_key = ''.join(k.lower().split())
            # Check if it starts with "yom>oem>model"
            if norm_key.startswith('yom>oem>model'):
                asset_idx = idx
                print(f"DEBUG: Found asset column using key '{k}' at index {idx}")
                break
    
    # Get other column indices
    tech_idx = col_indices.get('Raw Trusted Data')
    ai_data_idx = col_indices.get('AI Data')
    
    print(f"DEBUG: Column indices found:")
    print(f"  Asset (YOM > OEM > MODEL): {asset_idx}")
    print(f"  Raw Trusted Data: {tech_idx}")
    print(f"  AI Data: {ai_data_idx}")
    
    # Check required columns
    if asset_idx is None or tech_idx is None or ai_data_idx is None:
        error_msg = f'Missing required columns. Found: asset_idx={asset_idx}, tech_idx={tech_idx}, ai_data_idx={ai_data_idx}'
        errors.append(error_msg)
        print(f"ERROR: {error_msg}")
        return rows, errors, {"total": len(rows), "processed": 0, "success": 0, "skipped": 0, "errors_count": len(errors)}
    
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
    
    def is_ai_data_cell_empty(row, ai_data_idx):
        """Check if AI Data cell is empty."""
        if ai_data_idx is None or len(row) <= ai_data_idx:
            return True
        ai_data_value = row[ai_data_idx]
        if ai_data_value is None:
            return True
        return not str(ai_data_value).strip()
    
    skipped_filled = 0
    skipped_missing_data = 0
    
    # Collect rows that need processing
    rows_to_process = []
    for i, row in enumerate(rows):
        row_num = i + 3
        # Skip if already filled
        if not is_ai_data_cell_empty(row, ai_data_idx):
            skipped_filled += 1
            continue
        
        # Get asset name and technical specs
        asset = safe_get_cell(row, asset_idx)
        tech = safe_get_cell(row, tech_idx)
        
        # Skip if required data is missing
        if not asset:
            skipped_missing_data += 1
            continue
        
        rows_to_process.append((i, row, row_num, asset, tech))
    
    total_to_process = len(rows_to_process)
    print(f"DEBUG: Starting to process {total_to_process} rows (out of {len(rows)} total) for AI Data generation...", flush=True)
    print(f"DEBUG: Skipped {skipped_filled} rows (already filled), {skipped_missing_data} rows (missing data)", flush=True)
    
    # Process in parallel batches of 20
    import asyncio
    
    async def process_single_row(row_data):
        """Process a single row asynchronously."""
        # Check if process was cancelled before processing
        if session_id:
            from websocket_manager import manager
            if manager.is_cancelled(session_id):
                return None  # Return None to skip this row
        
        i, row, row_num, asset, tech = row_data
        
        # Build prompt - use custom if provided, otherwise use default
        if custom_prompt:
            prompt = custom_prompt.replace('{asset}', asset).replace('{tech_specs}', tech)
            prompt = prompt.replace('{ai_data}', '').replace('{comparable}', '')
        else:
            prompt = f"""Search the web for the official OEM technical specifications for the exact model provided.
Use ONLY information that appears explicitly on verified sources such as the OEM's website,
official brochures, or reputable equipment databases.
NO GUESSING, NO INFERENCES, NO ASSUMPTIONS.
If verified information cannot be found, respond only with: 'No official OEM specifications found.'
Otherwise, list the technical specifications in bullet format exactly as published.
Do not convert units, do not rewrite specs, do not add commentary.

CRITICAL FORMATTING REQUIREMENTS:
- Use bullet points with dashes: "- [Spec Name]: [Value]"
- Each specification must be on a separate line
- Use line breaks between different specification categories
- Do NOT use markdown formatting (no **, no *, no bold)
- Do NOT put multiple specs on the same line
- Format example:
  - Engine: 50 hp
  - Weight: 5000 lbs
  - Length: 10 ft

Reference information (these values will be automatically filled from the sheet columns):
Asset Name: {asset}
Raw Trusted Data: {tech}"""
        
        try:
            # Run Gemini API call in executor to make it async-compatible
            loop = asyncio.get_event_loop()
            
            # Gemini doesn't have native async, so we run it in executor
            def call_gemini():
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=8000,  # Increased from 2000 to handle longer responses
                    )
                )
                # Check if response was truncated due to token limit
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        if candidate.finish_reason == 2:  # MAX_TOKENS - response was truncated
                            print(f"DEBUG: Row {row_num}: Warning - Response may be truncated (finish_reason=MAX_TOKENS)")
                        elif candidate.finish_reason == 3:  # SAFETY - blocked by safety filters
                            print(f"DEBUG: Row {row_num}: Warning - Response blocked by safety filters (finish_reason=SAFETY)")
                
                return response.text if response.text else ""
            
            ai_data_text = await loop.run_in_executor(None, call_gemini)
            
            # Check if process was cancelled after processing (before saving)
            if session_id:
                from websocket_manager import manager
                if manager.is_cancelled(session_id):
                    print(f"DEBUG: Row {row_num}: Process cancelled, skipping result", flush=True)
                    return None  # Return None to skip this row
            
            if not ai_data_text:
                print(f"DEBUG: Row {row_num}: Empty response from Gemini - saving empty string")
                # Save empty string instead of skipping
                while len(row) <= ai_data_idx:
                    row.append("")
                row[ai_data_idx] = ""
                return (i, row_num, "", None)
            
            ai_data_text = ai_data_text.strip()
            
            # Log raw response length for debugging
            print(f"DEBUG: Row {row_num}: Gemini raw response length: {len(ai_data_text)} chars")
            if len(ai_data_text) > 0:
                print(f"DEBUG: Row {row_num}: Gemini raw response preview: {ai_data_text[:200]}...")
            
            # Only filter out truly explanatory responses that don't contain any specs
            # But accept "No official OEM specifications found." as valid
            is_explanation = False
            if ai_data_text.lower().strip() != "no official oem specifications found.":
                is_explanation = any(phrase in ai_data_text.lower() for phrase in [
                    "i need to clarify", "i cannot", "limitation", "i appreciate",
                    "according to my instructions", "would you like me",
                    "cannot generate"
                ]) and not any(char.isdigit() for char in ai_data_text)  # Only filter if no numbers (no specs)
            
            if ai_data_text and not is_explanation:
                # Clean the response: remove unwanted elements
                cleaned_text = clean_ai_data_response(ai_data_text)
                
                # Log cleaned response length for debugging
                print(f"DEBUG: Row {row_num}: After cleaning, length: {len(cleaned_text.strip()) if cleaned_text else 0} chars")
                
                # Check if process was cancelled before saving
                if session_id:
                    from websocket_manager import manager
                    if manager.is_cancelled(session_id):
                        print(f"DEBUG: Row {row_num}: Process cancelled, skipping result", flush=True)
                        return None  # Return None to skip this row
                
                # Save ANY response, even if it's short or says "No official OEM specifications found."
                # This ensures all rows are processed
                if cleaned_text and cleaned_text.strip():
                    # Ensure row has enough columns
                    while len(row) <= ai_data_idx:
                        row.append("")
                    row[ai_data_idx] = cleaned_text
                    print(f"DEBUG: Row {row_num}: Successfully saved AI Data ({len(cleaned_text)} chars)")
                    return (i, row_num, cleaned_text, None)
                else:
                    # Even if cleaning removed everything, save the original response
                    # This ensures we don't skip rows
                    while len(row) <= ai_data_idx:
                        row.append("")
                    row[ai_data_idx] = ai_data_text  # Save original if cleaning removed everything
                    print(f"DEBUG: Row {row_num}: Saved original response after cleaning removed content ({len(ai_data_text)} chars)")
                    return (i, row_num, ai_data_text, None)
            else:
                # Check if process was cancelled before saving
                if session_id:
                    from websocket_manager import manager
                    if manager.is_cancelled(session_id):
                        print(f"DEBUG: Row {row_num}: Process cancelled, skipping result", flush=True)
                        return None  # Return None to skip this row
                
                if is_explanation:
                    print(f"DEBUG: Row {row_num}: Response filtered as explanation - but saving anyway to ensure all rows processed")
                    # Save anyway to ensure all rows are processed
                    while len(row) <= ai_data_idx:
                        row.append("")
                    row[ai_data_idx] = ai_data_text
                    return (i, row_num, ai_data_text, None)
                else:
                    # Save empty string if no response
                    while len(row) <= ai_data_idx:
                        row.append("")
                    row[ai_data_idx] = ""
                    return (i, row_num, "", None)
        except Exception as e:
            error_detail = str(e)
            error_code = None
            
            if hasattr(e, 'status_code'):
                error_code = e.status_code
            elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                error_code = e.response.status_code
            
            return (i, row_num, None, (error_code, error_detail))
    
    # Process in batches of 20
    BATCH_SIZE = 20
    total_batches = (total_to_process + BATCH_SIZE - 1) // BATCH_SIZE
    
    # Shared counter for progress updates (thread-safe using asyncio.Lock)
    progress_counter = {"success": 0, "errors": 0}
    progress_lock = asyncio.Lock()
    
    async def process_single_row_with_progress(row_data):
        """Process a single row and send individual progress update."""
        result = await process_single_row(row_data)
        
        # Update counter atomically and send progress update for each completed row
        async with progress_lock:
            if result and result[2] is not None:  # Success
                progress_counter["success"] += 1
            elif result and result[3] is not None:  # Error
                progress_counter["errors"] += 1
            
            # Send individual progress update
            if session_id:
                try:
                    from websocket_manager import manager
                    await manager.broadcast_to_session(session_id, {
                        "type": "progress",
                        "step": "Generate AI Data",
                        "total": len(rows),
                        "processed": progress_counter["success"] + progress_counter["errors"],
                        "success": progress_counter["success"],
                        "errors": progress_counter["errors"],
                        "skipped": skipped_filled,
                    })
                    print(f"DEBUG: Sent progress update: success={progress_counter['success']}, errors={progress_counter['errors']}, total={len(rows)}")
                except Exception as e:
                    print(f"DEBUG: Failed to send progress update: {e}")
        
        return result
    
    async def process_batch(batch, batch_num, total_batches):
        """Process a batch of rows in parallel with individual progress updates."""
        print(f"DEBUG: Processing batch {batch_num}/{total_batches} ({len(batch)} rows)...")
        tasks = [process_single_row_with_progress(row_data) for row_data in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def process_all_batches():
        """Process all rows in batches."""
        all_results = []
        from websocket_manager import manager
        
        for batch_num in range(total_batches):
            # Check if process was cancelled
            if session_id and manager.is_cancelled(session_id):
                print(f"DEBUG: Process cancelled by user, stopping at batch {batch_num + 1}/{total_batches}", flush=True)
                if session_id:
                    await manager.broadcast_to_session(session_id, {
                        "type": "cancelled",
                        "step": "Generate AI Data",
                        "total": len(rows),
                        "processed": progress_counter["success"] + progress_counter["errors"],
                        "success": progress_counter["success"],
                        "errors": progress_counter["errors"],
                        "skipped": skipped_filled,
                        "message": "Process was cancelled by user"
                    })
                break
            
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
        results = await process_all_batches()
    except Exception as e:
        error_msg = f'Failed to process batches: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], {"total": len(rows), "processed": 0, "success": 0, "skipped": skipped_filled + skipped_missing_data, "errors_count": 1}
    
    # Process results
    success_count = 0
    no_data_count = 0  # Count rows that returned no meaningful data after cleaning
    for result in results:
        if isinstance(result, Exception):
            errors.append(f'Batch processing error: {str(result)}')
            continue
        
        if result is None:
            continue
        
        i, row_num, ai_data_text, error_info = result
        
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
                return rows, errors, {
                    "total": len(rows),
                    "processed": total_to_process,
                    "success": success_count,
                    "skipped": skipped_filled + skipped_missing_data,
                    "errors_count": len(errors)
                }
            
            # Non-critical errors
            error_msg = f'Row {row_num}: API error: {error_detail}'
            errors.append(error_msg)
            print(f"❌ {error_msg}")
        elif ai_data_text:
            success_count += 1
            print(f"✅ Row {row_num}: Successfully generated AI Data ({len(ai_data_text)} chars)")
        else:
            # Row processed but no meaningful data after cleaning
            no_data_count += 1
            print(f"⚠️ Row {row_num}: No meaningful data found after processing (may have been filtered out)")
    
    print(f"\n📊 Processing Summary:")
    print(f"  - Total rows processed: {len(rows)}")
    print(f"  - Rows with empty AI Data (candidates): {total_to_process + skipped_filled}")
    print(f"  - Rows skipped (already have AI Data): {skipped_filled}")
    print(f"  - Rows skipped (missing data): {skipped_missing_data}")
    print(f"  - Rows successfully filled with AI Data: {success_count}")
    print(f"  - Rows with no meaningful data after cleaning: {no_data_count}")
    print(f"  - Errors encountered: {len(errors)}")
    
    return rows, errors, {
        "total": len(rows),
        "processed": total_to_process,
        "success": success_count,
        "skipped": skipped_filled + skipped_missing_data + no_data_count,
        "errors_count": len(errors)
    }


async def build_description(rows, col_indices, session_id=None, custom_prompt=None):
    """
    Step 1: Build Description
    
    Generates technical descriptions for assets using Perplexity (or OpenAI as fallback) based on asset name,
    Raw Trusted Data, and AI Data (if it has data). Only fills empty 'Script Technical Description' cells.
    Prioritizes Perplexity if API key is available, falls back to OpenAI if not.
    
    The 'AI Data' column is mandatory (must exist), but is only included in the prompt if it contains data.
    
    Args:
        rows: List of data rows from the sheet
        col_indices: Dictionary mapping column names to their indices
        
    Returns:
        tuple: (updated_rows, errors)
            - updated_rows: List of rows with updated Script Technical Description values
            - errors: List of error messages encountered during processing
    """
    print("DEBUG: build_description function called")
    from openai import OpenAI
    from config import PERPLEXITY_API_KEY
    import re
    
    # Perplexity is required for all steps
    if not PERPLEXITY_API_KEY:
        error_msg = 'Perplexity API key required. Please set PERPLEXITY_API_KEY in your .env file.'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg]
    
    api_key_clean = PERPLEXITY_API_KEY.strip()
    # Remove quotes if present
    if api_key_clean.startswith('"') and api_key_clean.endswith('"'):
        api_key_clean = api_key_clean[1:-1].strip()
    if api_key_clean.startswith("'") and api_key_clean.endswith("'"):
        api_key_clean = api_key_clean[1:-1].strip()
    
    # Perplexity API keys start with "pplx-"
    if not api_key_clean or len(api_key_clean) <= 10 or not api_key_clean.startswith('pplx-'):
        error_msg = 'Invalid Perplexity API key. Keys must start with "pplx-" and be at least 10 characters long.'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg]
    
    key_preview = f"{api_key_clean[:10]}...{api_key_clean[-4:]}" if len(api_key_clean) > 14 else "***"
    print(f"DEBUG: ✅ Using Perplexity API for description generation (key preview: {key_preview}, length: {len(api_key_clean)})")
    
    try:
        print(f"DEBUG: Initializing Perplexity client...")
        client = OpenAI(
            api_key=api_key_clean,
            base_url="https://api.perplexity.ai"
        )
        print(f"DEBUG: Perplexity client initialized successfully")
    except Exception as e:
        error_msg = f'Failed to initialize API client: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg]

    errors = []
    
    desc_idx = col_indices.get('Script Technical Description')
    tech_idx = col_indices.get('Raw Trusted Data')
    ai_data_idx = col_indices.get('AI Data')  # Now mandatory
    asset_idx = None
    
    # Find the asset name/title column - starts with "YOM > OEM > MODEL"
    asset_name_key = 'YOM > OEM > MODEL'
    asset_idx = col_indices.get(asset_name_key)
    if asset_idx is None:
        # Fallback: try to find by pattern matching
        for k, idx in col_indices.items():
            if idx is None:
                continue
            norm_key = ''.join(k.lower().split())
            # Check if it starts with "yom>oem>model"
            if norm_key.startswith('yom>oem>model'):
                asset_idx = idx
                print(f"DEBUG: Found asset column using key '{k}' at index {idx}")
                break
    
    print(f"DEBUG: Column indices found:")
    print(f"  Asset (YOM > OEM > MODEL): {asset_idx}")
    print(f"  Raw Trusted Data: {tech_idx}")
    print(f"  AI Data: {ai_data_idx}")
    print(f"  Script Technical Description: {desc_idx}")
    
    # Import websocket manager for progress updates
    from websocket_manager import manager
    
    if desc_idx is None or tech_idx is None or asset_idx is None or ai_data_idx is None:
        error_msg = f'Missing required columns. Found: desc_idx={desc_idx}, tech_idx={tech_idx}, asset_idx={asset_idx}, ai_data_idx={ai_data_idx}'
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
        # Skip if already filled - improved empty cell detection
        desc_value = safe_get_cell(row, desc_idx)
        if desc_value and desc_value.strip():
            skipped_filled += 1
            continue
        
        # Get asset name, technical specs, and AI data (column is mandatory, but only used if it has data)
        asset = safe_get_cell(row, asset_idx)
        tech = safe_get_cell(row, tech_idx)
        ai_data = safe_get_cell(row, ai_data_idx)
        
        # Only tech is required to have data; AI Data column must exist but can be empty
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
        # Check if process was cancelled before processing
        if session_id:
            from websocket_manager import manager
            if manager.is_cancelled(session_id):
                return None  # Return None to skip this row
        
        i, row, row_num, asset, tech, ai_data = row_data
        
        # Log that AI Data is being used (for first row only to avoid spam)
        if i == 0 and ai_data:
            print(f"DEBUG: ✅ Confirmed: AI Data is being used in prompt (sample length: {len(ai_data)} chars)")
            print(f"DEBUG: ✅ Sample AI Data preview: {ai_data[:100]}..." if len(ai_data) > 100 else f"DEBUG: ✅ AI Data: {ai_data}")
        elif i == 0 and not ai_data:
            print(f"DEBUG: ℹ️ AI Data column exists but is empty for this row - will not be included in prompt")
        
        # Build prompt - use custom if provided, otherwise use default
        # AI Data column is mandatory, but only include it in prompt if it has data
        if ai_data:
            raw_input = f"{tech}\n\n{ai_data}"
        else:
            raw_input = tech
        
        if custom_prompt:
            # Replace variables in custom prompt
            # Only include AI Data if it has data
            if ai_data:
                prompt = custom_prompt.replace('{asset}', asset).replace('{tech_specs}', tech).replace('{ai_data}', f"\n\n{ai_data}")
            else:
                prompt = custom_prompt.replace('{asset}', asset).replace('{tech_specs}', tech).replace('{ai_data}', '')
            # Remove any remaining variable placeholders if not used
            prompt = prompt.replace('{comparable}', '')
        else:
            # Default prompt - matches frontend PromptEditor.js
            ai_data_section = f"\nAI Data: {ai_data}" if ai_data else ""
            prompt = f"""You are a technical documentation engineer writing for an industrial machinery catalog. For each item below, generate a single, objective technical description (200–250 words).
Rules:
- Start with: 'The [Asset Name] is a...' where [Asset Name] MUST be taken verbatim from the Asset Name field. — Do NOT restate or reformat the name.
- Infer it from context if not explicit.
- Immediately state its primary industrial application (e.g., 'engineered for quarry loading', 'designed for earthmoving in construction sites').
- Then describe technical systems in prose: engine, transmission, hydraulics, capacities, dimensions, etc. — only if present in input.
- Integrate specs into sentences (e.g., 'Powered by a... delivering... hp').
- NEVER use subjective, promotional, or evaluative language (e.g., 'robust', 'powerful', 'efficient', 'top-performing').
- Use only facts from 'Raw' or 'Clean' input. Do not invent data.
- Output must be one paragraph. No bullets, dashes, markdown, or lists.
- Output ONLY the description. No other text.

Reference information (these values will be automatically filled from the sheet columns):
Asset Name: {asset}
Raw Trusted Data: {tech}{ai_data_section}"""
        
        try:
            model_name = "sonar"
            async_client = AsyncOpenAI(
                api_key=api_key_clean,
                base_url="https://api.perplexity.ai"
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
    
    # Process in batches of 20
    BATCH_SIZE = 20
    total_batches = (total_to_process + BATCH_SIZE - 1) // BATCH_SIZE
    
    # Shared counter for progress updates (thread-safe using asyncio.Lock)
    import asyncio
    progress_counter = {"success": 0, "errors": 0}
    progress_lock = asyncio.Lock()
    
    async def process_single_row_with_progress(row_data):
        """Process a single row and send individual progress update."""
        result = await process_single_row(row_data)
        
        # Update counter atomically and send progress update for each completed row
        async with progress_lock:
            if result and result[2] is not None:  # Success
                progress_counter["success"] += 1
            elif result and result[3] is not None:  # Error
                progress_counter["errors"] += 1
            
            # Send individual progress update
            if session_id:
                try:
                    await manager.broadcast_to_session(session_id, {
                        "type": "progress",
                        "step": "Build Description",
                        "total": len(rows),
                        "processed": progress_counter["success"] + progress_counter["errors"],
                        "success": progress_counter["success"],
                        "errors": progress_counter["errors"],
                        "skipped": skipped_filled,
                    })
                    print(f"DEBUG: Sent progress update: success={progress_counter['success']}, errors={progress_counter['errors']}, total={len(rows)}")
                except Exception as e:
                    print(f"DEBUG: Failed to send progress update: {e}")
        
        return result
    
    async def process_batch(batch, batch_num, total_batches):
        """Process a batch of rows in parallel with individual progress updates."""
        print(f"DEBUG: Processing batch {batch_num}/{total_batches} ({len(batch)} rows)...")
        tasks = [process_single_row_with_progress(row_data) for row_data in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def process_all_batches():
        """Process all rows in batches."""
        all_results = []
        from websocket_manager import manager
        
        for batch_num in range(total_batches):
            # Check if process was cancelled
            if session_id and manager.is_cancelled(session_id):
                print(f"DEBUG: Process cancelled by user, stopping at batch {batch_num + 1}/{total_batches}", flush=True)
                if session_id:
                    await manager.broadcast_to_session(session_id, {
                        "type": "cancelled",
                        "step": "Build Description",
                        "total": len(rows),
                        "processed": progress_counter["success"] + progress_counter["errors"],
                        "success": progress_counter["success"],
                        "errors": progress_counter["errors"],
                        "skipped": skipped_filled,
                        "message": "Process was cancelled by user"
                    })
                break
            
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
        results = await process_all_batches()
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
    print(f"  - Rows with empty Script Technical Description (candidates): {processed_count + skipped_filled}")
    print(f"  - Rows skipped (already have description): {skipped_filled}")
    print(f"  - Rows skipped (missing data): {skipped_missing_data}")
    print(f"  - Rows successfully filled with description: {processed_count - len([e for e in errors if 'Row' in e])}")
    print(f"  - Errors encountered: {len(errors)}")
    
    return rows, errors


async def ai_source_comparables(rows, col_indices, custom_prompt=None, session_id=None):
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
    from config import PERPLEXITY_API_KEY
    import re
    
    # Perplexity is required for all steps
    if not PERPLEXITY_API_KEY:
        error_msg = 'Perplexity API key required. Please set PERPLEXITY_API_KEY in your .env file.'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], {"total": len(rows), "processed": 0, "success": 0, "skipped": 0, "errors_count": 1}
    
    api_key_clean = PERPLEXITY_API_KEY.strip()
    # Remove quotes if present
    if api_key_clean.startswith('"') and api_key_clean.endswith('"'):
        api_key_clean = api_key_clean[1:-1].strip()
    if api_key_clean.startswith("'") and api_key_clean.endswith("'"):
        api_key_clean = api_key_clean[1:-1].strip()
    
    # Perplexity API keys start with "pplx-"
    if not api_key_clean or len(api_key_clean) <= 10 or not api_key_clean.startswith('pplx-'):
        error_msg = 'Invalid Perplexity API key. Keys must start with "pplx-" and be at least 10 characters long.'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], {"total": len(rows), "processed": 0, "success": 0, "skipped": 0, "errors_count": 1}
    
    key_preview = f"{api_key_clean[:10]}...{api_key_clean[-4:]}" if len(api_key_clean) > 14 else "***"
    print(f"DEBUG: ✅ Using Perplexity API for comparables search (key preview: {key_preview}, length: {len(api_key_clean)})")
    
    try:
        print(f"DEBUG: Initializing Perplexity client...")
        client = OpenAI(
            api_key=api_key_clean,
            base_url="https://api.perplexity.ai"
        )
        print(f"DEBUG: Perplexity client initialized successfully")
    except Exception as e:
        error_msg = f'Failed to initialize API client: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg]
    
    errors = []
    
    # Find asset column: starts with "YOM > OEM > MODEL"
    asset_name_key = 'YOM > OEM > MODEL'
    asset_idx = col_indices.get(asset_name_key)
    if asset_idx is None:
        # Fallback: try to find by pattern matching
        for k, idx in col_indices.items():
            if idx is None:
                continue
            norm_key = ''.join(k.lower().split())
            # Check if it starts with "yom>oem>model"
            if norm_key.startswith('yom>oem>model'):
                asset_idx = idx
                print(f"DEBUG: Found asset column using key '{k}' at index {idx}")
                break
    
    # Get other column indices
    tech_idx = col_indices.get('Raw Trusted Data')
    ai_data_idx = col_indices.get('AI Data')
    comparable_idx = col_indices.get('AI Comparable Price')
    
    print(f"DEBUG: Column indices found:")
    print(f"  Asset (YOM > OEM > MODEL): {asset_idx}")
    print(f"  Raw Trusted Data: {tech_idx}")
    print(f"  AI Data: {ai_data_idx}")
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
    
    skipped_filled = 0
    skipped_missing_data = 0
    
    # Collect rows that need processing
    rows_to_process = []
    for i, row in enumerate(rows):
        row_num = i + 3
        # Skip if already filled
        if not is_comparable_cell_empty(row, comparable_idx):
            skipped_filled += 1
            continue
        
        # Get asset name, technical specs, and AI data
        asset = safe_get_cell(row, asset_idx)
        tech = safe_get_cell(row, tech_idx)
        ai_data = safe_get_cell(row, ai_data_idx)
        
        # Skip if required data is missing
        if not asset or not tech:
            skipped_missing_data += 1
            continue
        
        rows_to_process.append((i, row, row_num, asset, tech, ai_data))
    
    total_to_process = len(rows_to_process)
    print(f"DEBUG: Starting to process {total_to_process} rows (out of {len(rows)} total) for comparables search...")
    print(f"DEBUG: Skipped {skipped_filled} rows (already filled), {skipped_missing_data} rows (missing data)")
    
    # Process in parallel batches of 20
    import asyncio
    from openai import AsyncOpenAI
    
    # Use Perplexity model
    model_name = "sonar"
    print(f"DEBUG: Using model: {model_name}")
    
    async def process_single_row(row_data):
        """Process a single row asynchronously."""
        # Check if process was cancelled before processing
        if session_id:
            from websocket_manager import manager
            if manager.is_cancelled(session_id):
                return None  # Return None to skip this row
        
        i, row, row_num, asset, tech, ai_data = row_data
        
        # Build prompt - use custom if provided, otherwise use default
        if custom_prompt:
            prompt = custom_prompt.replace('{asset}', asset).replace('{tech_specs}', tech)
            if ai_data:
                prompt = prompt.replace('{ai_data}', f"\nAI Data: {ai_data}")
            else:
                prompt = prompt.replace('{ai_data}', '')
            prompt = prompt.replace('{comparable}', '')
        else:
            # Default prompt - matches frontend PromptEditor.js
            ai_data_section = f"\nAI Data: {ai_data}" if ai_data else ""
            prompt = f"""You are an expert in construction equipment valuation. Search the web thoroughly for comparable listings of this equipment. You MUST find and return at least 3-10 comparable listings if they exist online. For each comparable listing found, return ONLY: Condition, Price, and the Listing URL. Format each listing on one line exactly as: Condition: [condition], Price: [price], URL: [link]. 

IMPORTANT: 
- Search multiple equipment marketplaces (Machinery Pete, IronPlanet, eBay, Equipment Trader, etc.)
- Return up to 10 recent results if available
- If a listing doesn't have a price, use "Not listed" or "Call for Price" as the price
- Only return listings that are actually for sale (not just specifications pages)
- If you cannot find any comparables after thorough searching, return a brief explanation

Reference information (these values will be automatically filled from the sheet columns):
Asset Name: {asset}
Raw Trusted Data: {tech}{ai_data_section}"""
        
        try:
            async_client = AsyncOpenAI(
                api_key=api_key_clean,
                base_url="https://api.perplexity.ai"
            )
            
            response = await async_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a construction equipment search tool. Search thoroughly across multiple marketplaces and return ONLY listings in the exact format: Condition: [condition], Price: [price], URL: [link]. If no listings found, return ONLY: 'No comparables found'. Never write explanations, disclaimers, or meta-commentary."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500  # More tokens for multiple listings
            )
            
            comparable_text = response.choices[0].message.content.strip()
            
            # Filter out explanatory responses
            is_explanation = any(phrase in comparable_text.lower() for phrase in [
                "i need to clarify", "i cannot", "limitation", "i appreciate", 
                "i need to", "according to my instructions", "would you like me",
                "cannot generate", "do not contain", "search results provided"
            ])
            
            # Check if response follows the expected format
            has_valid_format = "condition:" in comparable_text.lower() and "price:" in comparable_text.lower()
            
            if comparable_text and not is_explanation and (has_valid_format or comparable_text.lower().startswith("no comparables found")):
                # Ensure row has enough columns
                while len(row) <= comparable_idx:
                    row.append("")
                row[comparable_idx] = comparable_text
                return (i, row_num, comparable_text, None)
            else:
                return (i, row_num, None, None)  # No comparables found, but not an error
        except Exception as e:
            error_detail = str(e)
            error_code = None
            
            if hasattr(e, 'status_code'):
                error_code = e.status_code
            elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                error_code = e.response.status_code
            
            return (i, row_num, None, (error_code, error_detail))
    
    # Process in batches of 20
    BATCH_SIZE = 20
    total_batches = (total_to_process + BATCH_SIZE - 1) // BATCH_SIZE
    
    # Shared counter for progress updates (thread-safe using asyncio.Lock)
    progress_counter = {"success": 0, "errors": 0}
    progress_lock = asyncio.Lock()
    
    async def process_single_row_with_progress(row_data):
        """Process a single row and send individual progress update."""
        result = await process_single_row(row_data)
        
        # Update counter atomically and send progress update for each completed row
        async with progress_lock:
            if result and result[2] is not None:  # Success
                progress_counter["success"] += 1
            elif result and result[3] is not None:  # Error
                progress_counter["errors"] += 1
            
            # Send individual progress update
            if session_id:
                try:
                    from websocket_manager import manager
                    await manager.broadcast_to_session(session_id, {
                        "type": "progress",
                        "step": "AI Source Comparables",
                        "total": len(rows),
                        "processed": progress_counter["success"] + progress_counter["errors"],
                        "success": progress_counter["success"],
                        "errors": progress_counter["errors"],
                        "skipped": skipped_filled,
                    })
                    print(f"DEBUG: Sent progress update: success={progress_counter['success']}, errors={progress_counter['errors']}, total={len(rows)}")
                except Exception as e:
                    print(f"DEBUG: Failed to send progress update: {e}")
        
        return result
    
    async def process_batch(batch, batch_num, total_batches):
        """Process a batch of rows in parallel with individual progress updates."""
        print(f"DEBUG: Processing batch {batch_num}/{total_batches} ({len(batch)} rows)...")
        tasks = [process_single_row_with_progress(row_data) for row_data in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def process_all_batches():
        """Process all rows in batches."""
        all_results = []
        from websocket_manager import manager
        
        for batch_num in range(total_batches):
            # Check if process was cancelled
            if session_id and manager.is_cancelled(session_id):
                print(f"DEBUG: Process cancelled by user, stopping at batch {batch_num + 1}/{total_batches}", flush=True)
                if session_id:
                    await manager.broadcast_to_session(session_id, {
                        "type": "cancelled",
                        "step": "AI Source Comparables",
                        "total": len(rows),
                        "processed": progress_counter["success"] + progress_counter["errors"],
                        "success": progress_counter["success"],
                        "errors": progress_counter["errors"],
                        "skipped": skipped_filled,
                        "message": "Process was cancelled by user"
                    })
                break
            
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
        results = await process_all_batches()
    except Exception as e:
        error_msg = f'Failed to process batches: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], {"total": len(rows), "processed": 0, "success": 0, "skipped": skipped_filled + skipped_missing_data, "errors_count": 1}
    
    # Process results
    success_count = 0
    for result in results:
        if isinstance(result, Exception):
            errors.append(f'Batch processing error: {str(result)}')
            continue
        
        if result is None:
            continue
        
        i, row_num, comparable_text, error_info = result
        
        if error_info:
            error_code, error_detail = error_info
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
                return rows, errors, {
                    "total": len(rows),
                    "processed": total_to_process,
                    "success": success_count,
                    "skipped": skipped_filled + skipped_missing_data,
                    "errors_count": len(errors)
                }
            
            # Non-critical errors
            error_msg = f'Row {row_num}: API error: {error_detail}'
            errors.append(error_msg)
            print(f"❌ {error_msg}")
        elif comparable_text:
            success_count += 1
            print(f"✅ Row {row_num}: Successfully found comparables ({len(comparable_text)} chars)")
    
    print(f"\n📊 Processing Summary:")
    print(f"  - Total rows processed: {len(rows)}")
    print(f"  - Rows with empty AI Comparable Price (candidates): {total_to_process + skipped_filled}")
    print(f"  - Rows skipped (already have comparables): {skipped_filled}")
    print(f"  - Rows skipped (missing data): {skipped_missing_data}")
    print(f"  - Rows successfully filled with comparables: {success_count}")
    print(f"  - Errors encountered: {len(errors)}")
    
    return rows, errors, {
        "total": len(rows),
        "processed": total_to_process,
        "success": success_count,
        "skipped": skipped_filled + skipped_missing_data,
        "errors_count": len(errors)
    }


async def extract_final_price(rows, col_indices, custom_prompt=None, session_id=None):
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
    from config import PERPLEXITY_API_KEY
    import re
    
    # Perplexity is required for all steps
    if not PERPLEXITY_API_KEY:
        error_msg = 'Perplexity API key required. Please set PERPLEXITY_API_KEY in your .env file.'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    
    api_key_clean = PERPLEXITY_API_KEY.strip()
    # Remove quotes if present
    if api_key_clean.startswith('"') and api_key_clean.endswith('"'):
        api_key_clean = api_key_clean[1:-1].strip()
    if api_key_clean.startswith("'") and api_key_clean.endswith("'"):
        api_key_clean = api_key_clean[1:-1].strip()
    
    # Perplexity API keys start with "pplx-"
    if not api_key_clean or len(api_key_clean) <= 10 or not api_key_clean.startswith('pplx-'):
        error_msg = 'Invalid Perplexity API key. Keys must start with "pplx-" and be at least 10 characters long.'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    
    key_preview = f"{api_key_clean[:10]}...{api_key_clean[-4:]}" if len(api_key_clean) > 14 else "***"
    print(f"DEBUG: ✅ Using Perplexity API for price extraction (key preview: {key_preview}, length: {len(api_key_clean)})")
    
    try:
        print(f"DEBUG: Initializing Perplexity client...")
        client = OpenAI(
            api_key=api_key_clean,
            base_url="https://api.perplexity.ai"
        )
        print(f"DEBUG: Perplexity client initialized successfully")
    except Exception as e:
        error_msg = f'Failed to initialize API client: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    errors = []
    filled_rows = []

    # Find asset column: starts with "YOM > OEM > MODEL"
    asset_name_key = 'YOM > OEM > MODEL'
    asset_idx = col_indices.get(asset_name_key)
    if asset_idx is None:
        # Fallback: try to find by pattern matching
        for k, idx in col_indices.items():
            if idx is None:
                continue
            norm_key = ''.join(k.lower().split())
            # Check if it starts with "yom>oem>model"
            if norm_key.startswith('yom>oem>model'):
                asset_idx = idx
                print(f"DEBUG: Found asset column using key '{k}' at index {idx}")
                break
    
    # Get other column indices - these should be found by name
    tech_idx = col_indices.get('Raw Trusted Data')
    ai_data_idx = col_indices.get('AI Data')
    comparable_idx = col_indices.get('AI Comparable Price')
    price_idx = col_indices.get('Price')
    
    # Debug: Print what we found
    print(f"DEBUG: Column indices found:")
    print(f"  Asset (YOM > OEM > MODEL): {asset_idx}")
    print(f"  Raw Trusted Data: {tech_idx}")
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
    
    skipped_empty_price = 0
    skipped_missing_data = 0
    
    # Collect rows that need processing
    rows_to_process = []
    for i, row in enumerate(rows):
        row_num = i + 3
        # Skip if already filled
        if not is_price_cell_empty(row, price_idx):
            skipped_empty_price += 1
            continue
        
        # Extract required data
        asset = safe_get_cell(row, asset_idx)
        tech = safe_get_cell(row, tech_idx)
        ai_data = safe_get_cell(row, ai_data_idx)
        comparable = safe_get_cell(row, comparable_idx)
        
        # Skip if required data is missing
        if not asset or not tech or not comparable:
            skipped_missing_data += 1
            continue
        
        rows_to_process.append((i, row, row_num, asset, tech, ai_data, comparable))
    
    total_to_process = len(rows_to_process)
    print(f"DEBUG: Starting to process {total_to_process} rows (out of {len(rows)} total) for price extraction...")
    print(f"DEBUG: Skipped {skipped_empty_price} rows (already filled), {skipped_missing_data} rows (missing data)")
    
    # Process in parallel batches of 20
    import asyncio
    from openai import AsyncOpenAI
    
    async def process_single_row(row_data):
        """Process a single row asynchronously."""
        if session_id:
            from websocket_manager import manager
            if manager.is_cancelled(session_id):
                return None
        
        i, row, row_num, asset, tech, ai_data, comparable = row_data
        
        # Build prompt
        if custom_prompt:
            prompt = custom_prompt.replace('{asset}', asset).replace('{tech_specs}', tech).replace('{comparable}', comparable)
            if ai_data:
                prompt = prompt.replace('{ai_data}', f"\nAI Data:\n{ai_data}\n")
            else:
                prompt = prompt.replace('{ai_data}', '')
        else:
            # Default prompt - matches frontend PromptEditor.js
            ai_data_section = f"\nAI Data: {ai_data}" if ai_data else ""
            prompt = f"""You are an expert in construction equipment valuation. Read the asset details, technical specs, and comparable listings below. Choose the single most relevant price, convert it to USD if needed, and return ONLY the final USD amount formatted like 'XXXXXX.XX'. If no relevant price exists, return blank. Do not add any explanation, note, or extra text.

Reference information (these values will be automatically filled from the sheet columns):
Asset Name: {asset}
Raw Trusted Data: {tech}
AI Comparable Price: {comparable}{ai_data_section}"""
        
        try:
            model = "sonar"
            async_client = AsyncOpenAI(
                api_key=api_key_clean,
                base_url="https://api.perplexity.ai"
            )
            
            response = await async_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a precise pricing analyst. Always return only numeric values in USD format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            price_text = response.choices[0].message.content.strip()
            
            if not price_text or price_text.upper() in ['NONE', 'N/A', 'NA', '']:
                return (i, row_num, None, None)
            
            normalized_price = normalize_price(price_text)
            
            if normalized_price is not None and normalized_price > 0:
                formatted_price = f"{normalized_price:.2f}"
                while len(row) <= price_idx:
                    row.append("")
                row[price_idx] = formatted_price
                return (i, row_num, formatted_price, None)
            else:
                return (i, row_num, None, (None, f'Could not extract valid price from: "{price_text}"'))
        except Exception as e:
            error_code = getattr(e, 'status_code', None)
            error_detail = str(e)
            return (i, row_num, None, (error_code, error_detail))
    
    # Process in batches of 20
    BATCH_SIZE = 20
    total_batches = (total_to_process + BATCH_SIZE - 1) // BATCH_SIZE
    
    progress_counter = {"success": 0, "errors": 0}
    progress_lock = asyncio.Lock()
    
    async def process_single_row_with_progress(row_data):
        """Process a single row and send individual progress update."""
        result = await process_single_row(row_data)
        
        async with progress_lock:
            if result and result[2] is not None:  # Success
                progress_counter["success"] += 1
            elif result and result[3] is not None:  # Error
                progress_counter["errors"] += 1
            
            if session_id:
                try:
                    from websocket_manager import manager
                    await manager.broadcast_to_session(session_id, {
                        "type": "progress",
                        "step": "Extract price from AI Comparable",
                        "total": len(rows),
                        "processed": progress_counter["success"] + progress_counter["errors"],
                        "success": progress_counter["success"],
                        "errors": progress_counter["errors"],
                        "skipped": skipped_empty_price,
                    })
                except Exception as e:
                    print(f"DEBUG: Failed to send progress update: {e}")
        
        return result
    
    async def process_batch(batch, batch_num, total_batches):
        """Process a batch of rows in parallel."""
        print(f"DEBUG: Processing batch {batch_num}/{total_batches} ({len(batch)} rows)...")
        tasks = [process_single_row_with_progress(row_data) for row_data in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def process_all_batches():
        """Process all rows in batches."""
        all_results = []
        from websocket_manager import manager
        
        for batch_num in range(total_batches):
            if session_id and manager.is_cancelled(session_id):
                print(f"DEBUG: Process cancelled by user, stopping at batch {batch_num + 1}/{total_batches}", flush=True)
                break
            
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
        results = await process_all_batches()
    except Exception as e:
        error_msg = f'Failed to process batches: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    
    # Process results
    for result in results:
        if isinstance(result, Exception):
            errors.append(f'Batch processing error: {str(result)}')
            continue
        
        if result is None:
            continue
        
        i, row_num, price_value, error_info = result
        
        if error_info:
            error_code, error_detail = error_info
            # Critical errors
            if error_code in [400, 401, 429]:
                api_name = "Perplexity"
                if error_code == 401:
                    error_msg = f'{api_name} API key authentication failed.'
                elif error_code == 400:
                    error_msg = f'{api_name} API model is invalid.'
                elif error_code == 429:
                    error_msg = f'{api_name} API quota exceeded.'
                else:
                    error_msg = f'{api_name} API error (code {error_code}).'
                
                errors.append(error_msg)
                print(f"❌ {error_msg}")
                return rows, errors, filled_rows
            
            # Non-critical errors
            errors.append(f'Row {row_num}: {error_detail}')
        elif price_value:
            filled_rows.append(row_num)
            print(f"✅ Row {row_num}: Successfully extracted price ${price_value}")
    
    # Summary logging
    print(f"\n📊 Processing Summary:")
    print(f"   - Total rows processed: {len(rows)}")
    print(f"   - Rows with empty Price (candidates): {total_to_process}")
    print(f"   - Rows skipped (already have price): {skipped_empty_price}")
    print(f"   - Rows skipped (missing data): {skipped_missing_data}")
    print(f"   - Rows successfully filled with price: {len(filled_rows)}")
    print(f"   - Errors encountered: {len(errors)}\n")
    
    return rows, errors, filled_rows


async def ai_source_new_price(rows, col_indices, custom_prompt=None, session_id=None):
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
    from config import PERPLEXITY_API_KEY
    import re
    
    # Perplexity is required for all steps
    if not PERPLEXITY_API_KEY:
        error_msg = 'Perplexity API key required. Please set PERPLEXITY_API_KEY in your .env file.'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    
    api_key_clean = PERPLEXITY_API_KEY.strip()
    # Remove quotes if present
    if api_key_clean.startswith('"') and api_key_clean.endswith('"'):
        api_key_clean = api_key_clean[1:-1].strip()
    if api_key_clean.startswith("'") and api_key_clean.endswith("'"):
        api_key_clean = api_key_clean[1:-1].strip()
    
    # Perplexity API keys start with "pplx-"
    if not api_key_clean or len(api_key_clean) <= 10 or not api_key_clean.startswith('pplx-'):
        error_msg = 'Invalid Perplexity API key. Keys must start with "pplx-" and be at least 10 characters long.'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    
    key_preview = f"{api_key_clean[:10]}...{api_key_clean[-4:]}" if len(api_key_clean) > 14 else "***"
    print(f"DEBUG: ✅ Using Perplexity API for new price search (key preview: {key_preview}, length: {len(api_key_clean)})")
    
    try:
        print(f"DEBUG: Initializing Perplexity client...")
        client = OpenAI(
            api_key=api_key_clean,
            base_url="https://api.perplexity.ai"
        )
        print(f"DEBUG: Perplexity client initialized successfully")
    except Exception as e:
        error_msg = f'Failed to initialize API client: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    
    errors = []
    filled_rows = []

    # Find asset column: starts with "YOM > OEM > MODEL"
    asset_name_key = 'YOM > OEM > MODEL'
    asset_idx = col_indices.get(asset_name_key)
    if asset_idx is None:
        # Fallback: try to find by pattern matching
        for k, idx in col_indices.items():
            if idx is None:
                continue
            norm_key = ''.join(k.lower().split())
            # Check if it starts with "yom>oem>model"
            if norm_key.startswith('yom>oem>model'):
                asset_idx = idx
                print(f"DEBUG: Found asset column using key '{k}' at index {idx}")
                break
    
    # Get other column indices
    tech_idx = col_indices.get('Raw Trusted Data')
    ai_data_idx = col_indices.get('AI Data')
    price_idx = col_indices.get('Price')
    
    print(f"DEBUG: Column indices found:")
    print(f"  Asset (YOM > OEM > MODEL): {asset_idx}")
    print(f"  Raw Trusted Data: {tech_idx}")
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
    
    skipped_empty_price = 0
    skipped_missing_data = 0
    
    # Collect rows that need processing
    rows_to_process = []
    for i, row in enumerate(rows):
        row_num = i + 3
        # Skip if already filled
        if not is_price_cell_empty(row, price_idx):
            skipped_empty_price += 1
            continue
        
        # Extract required data
        asset = safe_get_cell(row, asset_idx)
        tech = safe_get_cell(row, tech_idx)
        ai_data = safe_get_cell(row, ai_data_idx)
        
        # Skip if required data is missing
        if not asset or not tech:
            skipped_missing_data += 1
            continue
        
        rows_to_process.append((i, row, row_num, asset, tech, ai_data))
    
    total_to_process = len(rows_to_process)
    print(f"DEBUG: Starting to process {total_to_process} rows (out of {len(rows)} total) for new price search...")
    print(f"DEBUG: Skipped {skipped_empty_price} rows (already filled), {skipped_missing_data} rows (missing data)")
    
    # Process in parallel batches of 20
    import asyncio
    from openai import AsyncOpenAI
    
    model_name = "sonar"
    print(f"DEBUG: Using model: {model_name}")
    
    async def process_single_row(row_data):
        """Process a single row asynchronously."""
        if session_id:
            from websocket_manager import manager
            if manager.is_cancelled(session_id):
                return None
        
        i, row, row_num, asset, tech, ai_data = row_data
        
        # Build prompt
        if custom_prompt:
            prompt = custom_prompt.replace('{asset}', asset).replace('{tech_specs}', tech)
            if ai_data:
                prompt = prompt.replace('{ai_data}', f"\nAdditional AI data: {ai_data}")
            else:
                prompt = prompt.replace('{ai_data}', '')
            prompt = prompt.replace('{comparable}', '')
        else:
            # Default prompt - matches frontend PromptEditor.js
            ai_data_section = f"\nAI Data: {ai_data}" if ai_data else ""
            prompt = f"""You are an expert in construction equipment valuation. Based ONLY on the asset details below, return the current market price of a BRAND NEW unit in USD. Return ONLY the price formatted exactly like this: 'XXXXXX.XX'. If no explicit new price is available, return blank. Do not add any words, explanations, notes, or symbols. Do not say 'blank', 'N/A', or anything else. Only output the price or nothing.

Reference information (these values will be automatically filled from the sheet columns):
Asset Name: {asset}
Raw Trusted Data: {tech}{ai_data_section}"""
        
        try:
            async_client = AsyncOpenAI(
                api_key=api_key_clean,
                base_url="https://api.perplexity.ai"
            )
            
            response = await async_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are an expert in construction equipment valuation. Return only numeric prices in USD format (XXXXXX.XX), or nothing if unavailable."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            price_text = response.choices[0].message.content.strip()
            price_value = normalize_price(price_text)
            
            if price_value and price_value > 0:
                formatted_price = f"{price_value:.2f}"
                while len(row) <= price_idx:
                    row.append("")
                row[price_idx] = formatted_price
                return (i, row_num, formatted_price, None)
            else:
                return (i, row_num, None, None)
        except Exception as e:
            error_code = getattr(e, 'status_code', None)
            error_detail = str(e)
            return (i, row_num, None, (error_code, error_detail))
    
    # Process in batches of 20
    BATCH_SIZE = 20
    total_batches = (total_to_process + BATCH_SIZE - 1) // BATCH_SIZE
    
    progress_counter = {"success": 0, "errors": 0}
    progress_lock = asyncio.Lock()
    
    async def process_single_row_with_progress(row_data):
        """Process a single row and send individual progress update."""
        result = await process_single_row(row_data)
        
        async with progress_lock:
            if result and result[2] is not None:  # Success
                progress_counter["success"] += 1
            elif result and result[3] is not None:  # Error
                progress_counter["errors"] += 1
            
            if session_id:
                try:
                    from websocket_manager import manager
                    await manager.broadcast_to_session(session_id, {
                        "type": "progress",
                        "step": "AI Source New Price",
                        "total": len(rows),
                        "processed": progress_counter["success"] + progress_counter["errors"],
                        "success": progress_counter["success"],
                        "errors": progress_counter["errors"],
                        "skipped": skipped_empty_price,
                    })
                except Exception as e:
                    print(f"DEBUG: Failed to send progress update: {e}")
        
        return result
    
    async def process_batch(batch, batch_num, total_batches):
        """Process a batch of rows in parallel."""
        print(f"DEBUG: Processing batch {batch_num}/{total_batches} ({len(batch)} rows)...")
        tasks = [process_single_row_with_progress(row_data) for row_data in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def process_all_batches():
        """Process all rows in batches."""
        all_results = []
        from websocket_manager import manager
        
        for batch_num in range(total_batches):
            if session_id and manager.is_cancelled(session_id):
                print(f"DEBUG: Process cancelled by user, stopping at batch {batch_num + 1}/{total_batches}", flush=True)
                break
            
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
        results = await process_all_batches()
    except Exception as e:
        error_msg = f'Failed to process batches: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    
    # Process results
    for result in results:
        if isinstance(result, Exception):
            errors.append(f'Batch processing error: {str(result)}')
            continue
        
        if result is None:
            continue
        
        i, row_num, price_value, error_info = result
        
        if error_info:
            error_code, error_detail = error_info
            # Critical errors
            if error_code in [400, 401, 429]:
                if error_code == 401:
                    error_msg = f"CRITICAL: API authentication failed. Please check your API key. Error: {error_detail}"
                elif error_code == 400:
                    error_msg = f"CRITICAL: Invalid API request (possibly invalid model). Error: {error_detail}"
                elif error_code == 429:
                    error_msg = f"CRITICAL: API quota exceeded. Please check your API credits. Error: {error_detail}"
                else:
                    error_msg = f"CRITICAL: API error (code {error_code}). Error: {error_detail}"
                
                errors.append(error_msg)
                print(f"❌ {error_msg}")
                return rows, errors, filled_rows
            
            # Non-critical errors
            errors.append(f'Row {row_num}: API error: {error_detail}')
        elif price_value:
            filled_rows.append(row_num)
            print(f"✅ Row {row_num}: Successfully found new price ${price_value}")
    
    print(f"\n📊 Processing Summary:")
    print(f"  - Total rows processed: {len(rows)}")
    print(f"  - Rows with empty Price (candidates): {total_to_process + skipped_empty_price}")
    print(f"  - Rows skipped (already have price): {skipped_empty_price}")
    print(f"  - Rows skipped (missing data): {skipped_missing_data}")
    print(f"  - Rows successfully filled with price: {len(filled_rows)}")
    print(f"  - Errors encountered: {len(errors)}")
    
    return rows, errors, filled_rows


async def ai_similar_comparable(rows, col_indices, custom_prompt=None, session_id=None):
    """
    Step 5: AI Similar Comparable
    Finds similar asset prices online based on technical specifications and AI Data.
    Fills 'Price' only for cells still empty after previous step.
    Returns updated rows and a list of errors, and a list of filled row indices.
    """
    print("DEBUG: ai_similar_comparable function called")
    from openai import OpenAI
    from config import PERPLEXITY_API_KEY
    import re
    
    # Perplexity is required for all steps
    if not PERPLEXITY_API_KEY:
        error_msg = 'Perplexity API key required. Please set PERPLEXITY_API_KEY in your .env file.'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    
    api_key_clean = PERPLEXITY_API_KEY.strip()
    # Remove quotes if present
    if api_key_clean.startswith('"') and api_key_clean.endswith('"'):
        api_key_clean = api_key_clean[1:-1].strip()
    if api_key_clean.startswith("'") and api_key_clean.endswith("'"):
        api_key_clean = api_key_clean[1:-1].strip()
    
    # Perplexity API keys start with "pplx-"
    if not api_key_clean or len(api_key_clean) <= 10 or not api_key_clean.startswith('pplx-'):
        error_msg = 'Invalid Perplexity API key. Keys must start with "pplx-" and be at least 10 characters long.'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    
    key_preview = f"{api_key_clean[:10]}...{api_key_clean[-4:]}" if len(api_key_clean) > 14 else "***"
    print(f"DEBUG: ✅ Using Perplexity API for similar comparables search (key preview: {key_preview}, length: {len(api_key_clean)})")
    
    try:
        client = OpenAI(api_key=api_key_clean, base_url="https://api.perplexity.ai")
        print(f"DEBUG: Perplexity client initialized successfully")
    except Exception as e:
        error_msg = f'Failed to initialize API client: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    
    errors = []
    filled_rows = []
    
    # Find column indices
    price_idx = col_indices.get('Price')
    asset_name_key = 'YOM > OEM > MODEL'
    asset_idx = col_indices.get(asset_name_key)
    if asset_idx is None:
        # Fallback: try to find by pattern matching
        for k, idx in col_indices.items():
            if idx is None:
                continue
            norm_key = ''.join(k.lower().split())
            # Check if it starts with "yom>oem>model"
            if norm_key.startswith('yom>oem>model'):
                asset_idx = idx
                break
    tech_idx = col_indices.get('Raw Trusted Data')
    ai_data_idx = col_indices.get('AI Data')
    
    if price_idx is None or asset_idx is None or tech_idx is None:
        error_msg = f'Missing required columns. Found: price_idx={price_idx}, asset_idx={asset_idx}, tech_idx={tech_idx}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    
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
    
    skipped_empty_price = 0
    skipped_missing_data = 0
    
    # Collect rows that need processing
    rows_to_process = []
    for i, row in enumerate(rows):
        row_num = i + 3
        # Skip if already filled
        if not is_price_cell_empty(row, price_idx):
            skipped_empty_price += 1
            continue
        
        # Extract required data
        asset = safe_get_cell(row, asset_idx)
        tech = safe_get_cell(row, tech_idx)
        ai_data = safe_get_cell(row, ai_data_idx)
        
        # Skip if required data is missing
        if not asset or not tech:
            skipped_missing_data += 1
            continue
        
        rows_to_process.append((i, row, row_num, asset, tech, ai_data))
    
    total_to_process = len(rows_to_process)
    print(f"DEBUG: Starting to process {total_to_process} rows (out of {len(rows)} total) for similar comparables search...")
    print(f"DEBUG: Skipped {skipped_empty_price} rows (already filled), {skipped_missing_data} rows (missing data)")
    
    # Process in parallel batches of 20
    import asyncio
    from openai import AsyncOpenAI
    
    model_name = "sonar"
    print(f"DEBUG: Using model: {model_name}")
    
    async def process_single_row(row_data):
        """Process a single row asynchronously."""
        if session_id:
            from websocket_manager import manager
            if manager.is_cancelled(session_id):
                return None
        
        i, row, row_num, asset, tech, ai_data = row_data
        
        # Build prompt
        if custom_prompt:
            prompt = custom_prompt.replace('{asset}', asset).replace('{tech_specs}', tech)
            if ai_data:
                prompt = prompt.replace('{ai_data}', f"\nAI Data: {ai_data}")
            else:
                prompt = prompt.replace('{ai_data}', '')
            prompt = prompt.replace('{comparable}', '')
        else:
            # Default prompt - matches frontend PromptEditor.js
            ai_data_section = f"\nAI Data: {ai_data}" if ai_data else ""
            prompt = f"""You are an expert in construction equipment valuation. Search for similar equipment based on the Raw Trusted Data and AI Data provided below. Find comparable assets that match the specifications and characteristics. For each similar asset found, return ONLY: Condition, Price, and the Listing URL. Format each on one line as: Condition: [condition], Price: [price], URL: [link]. Return up to 10 recent results. If no similar assets are found, return blank.

Reference information (these values will be automatically filled from the sheet columns):
Asset Name: {asset}
Raw Trusted Data: {tech}{ai_data_section}"""
        
        try:
            async_client = AsyncOpenAI(
                api_key=api_key_clean,
                base_url="https://api.perplexity.ai"
            )
            
            response = await async_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a web search assistant. Search for similar equipment listings and return only Condition, Price, and URL for each listing, formatted as specified."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            similar_text = response.choices[0].message.content.strip()
            
            # Extract price from similar comparables
            price_value = None
            if similar_text:
                price_patterns = [
                    r'\$[\d,]+\.?\d*',
                    r'USD\s*[\d,]+\.?\d*',
                    r'[\d,]+\.?\d*\s*USD',
                    r'Price:\s*\$?[\d,]+\.?\d*',
                ]
                
                for pattern in price_patterns:
                    matches = re.findall(pattern, similar_text, re.IGNORECASE)
                    if matches:
                        price_str = matches[0]
                        price_str = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
                        try:
                            price_value = float(price_str)
                            break
                        except ValueError:
                            continue
            
            if price_value:
                while len(row) <= price_idx:
                    row.append("")
                row[price_idx] = f"{price_value:.2f}"
                return (i, row_num, f"{price_value:.2f}", None)
            else:
                return (i, row_num, None, None)
        except Exception as e:
            error_code = getattr(e, 'status_code', None)
            error_detail = str(e)
            return (i, row_num, None, (error_code, error_detail))
    
    # Process in batches of 20
    BATCH_SIZE = 20
    total_batches = (total_to_process + BATCH_SIZE - 1) // BATCH_SIZE
    
    progress_counter = {"success": 0, "errors": 0}
    progress_lock = asyncio.Lock()
    
    async def process_single_row_with_progress(row_data):
        """Process a single row and send individual progress update."""
        result = await process_single_row(row_data)
        
        async with progress_lock:
            if result and result[2] is not None:  # Success
                progress_counter["success"] += 1
            elif result and result[3] is not None:  # Error
                progress_counter["errors"] += 1
            
            if session_id:
                try:
                    from websocket_manager import manager
                    await manager.broadcast_to_session(session_id, {
                        "type": "progress",
                        "step": "AI Similar Comparable",
                        "total": len(rows),
                        "processed": progress_counter["success"] + progress_counter["errors"],
                        "success": progress_counter["success"],
                        "errors": progress_counter["errors"],
                        "skipped": skipped_empty_price,
                    })
                except Exception as e:
                    print(f"DEBUG: Failed to send progress update: {e}")
        
        return result
    
    async def process_batch(batch, batch_num, total_batches):
        """Process a batch of rows in parallel."""
        print(f"DEBUG: Processing batch {batch_num}/{total_batches} ({len(batch)} rows)...")
        tasks = [process_single_row_with_progress(row_data) for row_data in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def process_all_batches():
        """Process all rows in batches."""
        all_results = []
        from websocket_manager import manager
        
        for batch_num in range(total_batches):
            if session_id and manager.is_cancelled(session_id):
                print(f"DEBUG: Process cancelled by user, stopping at batch {batch_num + 1}/{total_batches}", flush=True)
                break
            
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
        results = await process_all_batches()
    except Exception as e:
        error_msg = f'Failed to process batches: {str(e)}'
        print(f"ERROR: {error_msg}")
        return rows, [error_msg], []
    
    # Process results
    for result in results:
        if isinstance(result, Exception):
            errors.append(f'Batch processing error: {str(result)}')
            continue
        
        if result is None:
            continue
        
        i, row_num, price_value, error_info = result
        
        if error_info:
            error_code, error_detail = error_info
            # Critical errors
            if error_code in [400, 401, 429]:
                if error_code == 401:
                    error_msg = f"CRITICAL: API authentication failed. Please check your API key."
                elif error_code == 400:
                    error_msg = f"CRITICAL: Invalid API request."
                elif error_code == 429:
                    error_msg = f"CRITICAL: API quota exceeded."
                else:
                    error_msg = f"CRITICAL: API error (code {error_code})."
                
                errors.append(error_msg)
                print(f"❌ {error_msg}")
                return rows, errors, filled_rows
            
            # Non-critical errors
            errors.append(f'Row {row_num}: API error: {error_detail}')
        elif price_value:
            filled_rows.append(row_num)
            print(f"✅ Row {row_num}: Successfully found similar comparable price: ${price_value}")
    
    print(f"\n📊 Processing Summary:")
    print(f"  - Total rows processed: {len(rows)}")
    print(f"  - Rows with empty Price (candidates): {total_to_process + skipped_empty_price}")
    print(f"  - Rows skipped (already have price): {skipped_empty_price}")
    print(f"  - Rows skipped (missing data): {skipped_missing_data}")
    print(f"  - Rows successfully filled with price: {len(filled_rows)}")
    print(f"  - Errors encountered: {len(errors)}")
    
    return rows, errors, filled_rows

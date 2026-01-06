
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from google_sheets import get_sheet_data, update_sheet_data
import re
from sheet_utils import find_column_indices
from process_steps import build_description
from websocket_manager import manager
from database import save_history, get_history, get_history_by_sheet, save_or_update_process, get_active_processes, delete_process
from typing import Optional


def get_column_letter(col_idx):
    """
    Convert a zero-based column index to Google Sheets column letter (A, B, ..., Z, AA, AB, ...).
    
    Args:
        col_idx: Zero-based column index
        
    Returns:
        Column letter(s) as string (e.g., 'A', 'Z', 'AA', 'AB')
    """
    result = ""
    col_idx += 1  # Convert to 1-based
    while col_idx > 0:
        col_idx -= 1
        result = chr(65 + (col_idx % 26)) + result
        col_idx //= 26
    return result



router = APIRouter()

# Pydantic model for process step request
class ProcessRequest(BaseModel):
    sheetId: str
    step: str
    sheet_name: str = None
    session_id: str = None  # For WebSocket updates
    custom_prompt: str = None  # Custom prompt to use instead of default

# Pydantic model for history request
class HistoryRequest(BaseModel):
    sheet_name: str
    step: Optional[str] = None
    message: str
    timestamp: str
    time: str

# Simple test endpoint to verify POST requests work
@router.post("/test-process")
async def test_process():
    import sys
    import os
    import logging
    logger = logging.getLogger(__name__)
    
    msg = "\n" + "="*70 + "\nTEST PROCESS ENDPOINT CALLED\n" + "="*70 + "\n"
    
    # Try every way to output
    try:
        os.write(1, msg.encode('utf-8'))
        os.write(2, msg.encode('utf-8'))
    except:
        pass
    
    sys.stdout.write(msg)
    sys.stdout.flush()
    sys.stderr.write(msg)
    sys.stderr.flush()
    
    logger.info(msg)
    
    return {"status": "ok", "message": "Test process endpoint works"}

def extract_sheet_id(sheet_url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
    if match:
        return match.group(1)
    return None

def find_structured_data_tab(sheet_id):
    """Find the first tab that starts with 'Structured Data'."""
    print(f"DEBUG: find_structured_data_tab called for sheet_id: {sheet_id}", flush=True)
    try:
        from google_sheets import get_service
        print(f"DEBUG: Getting service...", flush=True)
        service = get_service()
        print(f"DEBUG: Fetching sheet metadata...", flush=True)
        sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        print(f"DEBUG: Sheet metadata received", flush=True)
        sheets = sheet_metadata.get('sheets', [])
        print(f"DEBUG: Found {len(sheets)} sheets", flush=True)
        for sheet in sheets:
            title = sheet.get('properties', {}).get('title', '')
            if title.startswith('Structured Data'):
                print(f"DEBUG: Found Structured Data tab: {title}", flush=True)
                return title
        print(f"DEBUG: No Structured Data tab found", flush=True)
        return None
    except Exception as e:
        print(f"ERROR: Exception in find_structured_data_tab: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return None

@router.get("/sheet-preview")
def sheet_preview(sheet_url: str = Query(..., description="Google Sheet URL"), sheet_name: str = None):
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        raise HTTPException(status_code=400, detail="Invalid Google Sheet URL")
    
    # Auto-detect Structured Data tab if not provided
    if not sheet_name:
        sheet_name = find_structured_data_tab(sheet_id)
        print(f"DEBUG: Auto-detected tab: {sheet_name}")
    
    # Use a large range to read all rows (Google Sheets API only returns rows with data)
    range_name = f"{sheet_name}!A2:Z100000" if sheet_name else "A2:Z100000"
    data = get_sheet_data(sheet_id, range_name)
    return {
        "headers": data[0] if data else [], 
        "rows": data[1:] if len(data) > 1 else [],
        "sheet_name": sheet_name  # Return detected sheet name
    }

@router.post("/process")
async def process_step(request: ProcessRequest):
    import sys
    import logging
    logger = logging.getLogger(__name__)
    
    # Force immediate output
    sys.stdout.write(f"\n{'='*60}\n")
    sys.stdout.write(f"DEBUG: /process endpoint called\n")
    sys.stdout.write(f"DEBUG: Step: {request.step}\n")
    sys.stdout.write(f"DEBUG: Sheet ID: {request.sheetId}\n")
    sys.stdout.write(f"DEBUG: Sheet name: {request.sheet_name}\n")
    sys.stdout.write(f"{'='*60}\n\n")
    sys.stdout.flush()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"DEBUG: /process endpoint called")
    logger.info(f"DEBUG: Step: {request.step}")
    logger.info(f"DEBUG: Sheet ID: {request.sheetId}")
    logger.info(f"DEBUG: Sheet name: {request.sheet_name}")
    logger.info(f"{'='*60}\n")
    
    try:
        sheetId = request.sheetId
        step = request.step
        sheet_name = request.sheet_name
        
        # Auto-detect Structured Data tab if not provided
        if not sheet_name:
            print(f"DEBUG: sheet_name is None, calling find_structured_data_tab...", flush=True)
            sheet_name = find_structured_data_tab(sheetId)
            print(f"DEBUG: Auto-detected tab for process: {sheet_name}", flush=True)
        else:
            print(f"DEBUG: Using provided sheet_name: {sheet_name}", flush=True)
        
        if not sheet_name:
            raise HTTPException(status_code=400, detail="Could not find 'Structured Data' tab in sheet")
        
        # Fetch headers and rows (headers in row 2, data from row 3)
        # Use a large range to read all rows (Google Sheets API only returns rows with data)
        range_name = f"{sheet_name}!A2:Z100000"
        print(f"DEBUG: Reading from range: {range_name}", flush=True)
        print(f"DEBUG: Calling get_sheet_data...", flush=True)
        data = get_sheet_data(sheetId, range_name)
        print(f"DEBUG: get_sheet_data completed, got {len(data) if data else 0} rows", flush=True)
        if not data or len(data) < 2:
            raise HTTPException(status_code=400, detail="Sheet missing headers or data.")
        headers = data[0]
        rows = data[1:]
        
        # Send initial progress update via WebSocket
        if request.session_id:
            await manager.broadcast_to_session(request.session_id, {
                "type": "progress",
                "step": step,
                "total": len(rows),
                "processed": 0,
                "success": 0,
                "errors": 0,
                "skipped": 0,
            })
        
        # Debug: Print all headers
        print(f"\nDEBUG: Total headers found: {len(headers)}", flush=True)
        print(f"DEBUG: First 10 headers: {headers[:10]}", flush=True)
        print(f"DEBUG: All headers with indices:", flush=True)
        for idx, header in enumerate(headers):
            print(f"  [{idx}] '{header}'", flush=True)

        # Select required columns per step
        if step == "Generate AI Data":
            required_names = [
                r"YOM > OEM > MODEL",  # Asset name column starts with this
                r"Raw Trusted Data",  # Previously "Technical Specifications"
                r"AI Data"  # Column to fill
            ]
        elif step == "Build Description":
            required_names = [
                r"YOM > OEM > MODEL",  # Asset name column starts with this
                r"Raw Trusted Data",  # Previously "Technical Specifications"
                r"AI Data",  # Now mandatory
                r"Script Technical Description"  # Previously "AI Description"
            ]
        elif step == "AI Source Comparables":
            required_names = [
                r"YOM > OEM > MODEL",  # Asset name column starts with this
                r"Raw Trusted Data",  # Previously "Technical Specifications"
                r"AI Comparable Price"  # Column to fill
            ]
        elif step == "Extract price from AI Comparable":
            # Required columns for price extraction - search by exact name or flexible pattern
            # We search by name, not by position, so columns can be in any order
            required_names = [
                r"YOM > OEM > MODEL",  # Asset name column starts with this
                r"Raw Trusted Data",  # Previously "Technical Specifications"
                r"AI Comparable Price",  # Exact or partial match
                r"Price"  # Must be exact "Price" (not "AI Comparable Price")
            ]
            # AI Data is optional but recommended, so check if present
            if any(re.search(r"AI Data", h, re.IGNORECASE) for h in headers):
                required_names.append(r"AI Data")
        elif step == "AI Similar Comparable":
            required_names = [
                r"YOM > OEM > MODEL",  # Asset name column starts with this
                r"Raw Trusted Data",  # Previously "Technical Specifications"
                r"Price"  # Column to fill
            ]
            # AI Data is optional but recommended
            if any(re.search(r"AI Data", h, re.IGNORECASE) for h in headers):
                required_names.append(r"AI Data")
        else:
            required_names = [
                r"YOM > OEM > MODEL",  # Asset name column starts with this
                r"Raw Trusted Data",  # Previously "Technical Specifications"
                r"AI Data",
                r"Script Technical Description",  # Previously "AI Description"
                r"AI Comparable Price",
                r"Price"
            ]

        col_indices = find_column_indices(headers, required_names)
        
        # Debug: Print all found columns
        print(f"DEBUG: Found columns:", flush=True)
        for name, idx in col_indices.items():
            if idx is not None:
                print(f"  - '{name}': index {idx} (header: '{headers[idx] if idx < len(headers) else 'N/A'}')", flush=True)
            else:
                print(f"  - '{name}': NOT FOUND", flush=True)
        
        # Check for required columns (AI Data is now mandatory for Build Description)
        if step == "Build Description":
            # For Build Description, AI Data is mandatory
            truly_required = required_names
        else:
            # For other steps, AI Data is optional
            truly_required = [n for n in required_names if n != r"AI Data"]
        missing = [k for k in truly_required if col_indices.get(k) is None]
        if missing:
            return {"status": "error", "missing_headers": missing, "available_headers": headers}

        # Run the selected process step
        errors = []
        updated_rows = rows
        custom_prompt = request.custom_prompt  # Get custom prompt if provided
        
        if step == "Generate AI Data":
            print(f"\n{'='*60}", flush=True)
            print(f"DEBUG: Starting Generate AI Data", flush=True)
            print(f"DEBUG: Processing {len(rows)} rows", flush=True)
            print(f"{'='*60}\n", flush=True)
            from process_steps import generate_ai_data
            updated_rows, errors, ai_data_stats = await generate_ai_data(rows, col_indices, custom_prompt=custom_prompt, session_id=request.session_id)
            print(f"\nDEBUG: generate_ai_data completed. {len(errors)} errors\n", flush=True)
            
            # Store stats for response BEFORE writing to sheet (so we can send WebSocket message early)
            ai_data_stats_dict = ai_data_stats
            
            # Send WebSocket complete message EARLY, before writing to sheet
            # This ensures the message is sent while WebSocket connections are still open
            if request.session_id and ai_data_stats_dict:
                stats = ai_data_stats_dict
                filled = stats.get("success", 0)
                errors_count = stats.get("errors_count", 0)
                skipped = stats.get("skipped", 0)
                
                complete_message = {
                    "type": "complete",
                    "step": step,
                    "total": len(rows),
                    "processed": filled,
                    "success": filled,
                    "errors": errors_count,
                    "skipped": skipped,
                }
                print(f"DEBUG: Sending WebSocket complete message EARLY to session {request.session_id}: {complete_message}", flush=True)
                has_connection = manager.has_active_connection(request.session_id)
                print(f"DEBUG: Active connections for session {request.session_id}: {has_connection}", flush=True)
                
                if has_connection:
                    try:
                        import asyncio
                        await asyncio.sleep(0.1)
                        await manager.broadcast_to_session(request.session_id, complete_message)
                        print(f"DEBUG: WebSocket complete message sent successfully (early)", flush=True)
                    except Exception as e:
                        print(f"ERROR: Failed to send WebSocket complete message (early): {e}", flush=True)
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"WARNING: No active WebSocket connections for session {request.session_id} (early send), message not sent", flush=True)
            
            # Write back only the AI Data column
            ai_data_idx = col_indices.get('AI Data')
            if ai_data_idx is not None:
                col_letter = get_column_letter(ai_data_idx)
                start_row = 3
                end_row = start_row + len(updated_rows) - 1
                out_range = f"{sheet_name}!{col_letter}{start_row}:{col_letter}{end_row}" if sheet_name else f"{col_letter}{start_row}:{col_letter}{end_row}"
                values = [[row[ai_data_idx] if len(row) > ai_data_idx else ""] for row in updated_rows]
                
                # Count how many non-empty values we're writing
                non_empty_count = sum(1 for v in values if v and v[0] and str(v[0]).strip())
                print(f"DEBUG: Writing AI Data to sheet: {non_empty_count} non-empty values out of {len(values)} total", flush=True)
                print(f"DEBUG: Range: {out_range}, Column: {col_letter}", flush=True)
                
                try:
                    update_sheet_data(sheetId, out_range, values)
                    print(f"✅ Successfully wrote AI Data to sheet", flush=True)
                except Exception as e:
                    error_msg = f'Failed to write AI Data to sheet: {str(e)}'
                    print(f"❌ ERROR: {error_msg}", flush=True)
                    errors.append(error_msg)
                    import traceback
                    traceback.print_exc()
            else:
                print(f"WARNING: AI Data column index not found, cannot write to sheet", flush=True)
            
        elif step == "Build Description":
            # Count rows that were already filled before processing
            desc_idx = col_indices.get('Script Technical Description')
            already_filled_count = 0
            if desc_idx is not None:
                for row in rows:
                    if len(row) > desc_idx:
                        desc_value = str(row[desc_idx]).strip() if row[desc_idx] else ""
                        if desc_value:
                            already_filled_count += 1
            
            updated_rows, errors = await build_description(rows, col_indices, session_id=request.session_id, custom_prompt=custom_prompt)
            # Write back only the description column
            if desc_idx is not None:
                col_letter = get_column_letter(desc_idx)
                # Calculate the range: from row 3 to row (3 + number of rows - 1)
                start_row = 3
                end_row = start_row + len(updated_rows) - 1
                out_range = f"{sheet_name}!{col_letter}{start_row}:{col_letter}{end_row}" if sheet_name else f"{col_letter}{start_row}:{col_letter}{end_row}"
                values = [[row[desc_idx] if len(row) > desc_idx else ""] for row in updated_rows]
                update_sheet_data(sheetId, out_range, values)
            
            # Calculate stats for Build Description
            # Count rows that now have a description (after processing)
            total_filled_after = 0
            if desc_idx is not None:
                for row in updated_rows:
                    if len(row) > desc_idx:
                        desc_value = str(row[desc_idx]).strip() if row[desc_idx] else ""
                        if desc_value:
                            total_filled_after += 1
            
            # Newly filled = total filled after - already filled before
            newly_filled_count = total_filled_after - already_filled_count
            
            # Store stats for response
            build_description_stats = {
                "total": len(rows),
                "filled": newly_filled_count,  # Only newly filled in this run
                "skipped": already_filled_count,  # Already had description before
                "errors_count": len(errors)
            }
        elif step == "AI Source Comparables":
            print(f"\n{'='*60}", flush=True)
            print(f"DEBUG: Starting AI Source Comparables", flush=True)
            print(f"DEBUG: Processing {len(rows)} rows", flush=True)
            print(f"{'='*60}\n", flush=True)
            from process_steps import ai_source_comparables
            updated_rows, errors, comparables_stats = await ai_source_comparables(rows, col_indices, custom_prompt=custom_prompt, session_id=request.session_id)
            print(f"\nDEBUG: ai_source_comparables completed. {len(errors)} errors\n", flush=True)
            # Store stats for response BEFORE writing to sheet (so we can send WebSocket message early)
            comparables_stats_dict = comparables_stats
            
            # Send WebSocket complete message EARLY, before writing to sheet
            # This ensures the message is sent while WebSocket connections are still open
            if request.session_id and comparables_stats_dict:
                stats = comparables_stats_dict
                filled = stats.get("success", 0)
                errors_count = stats.get("errors_count", 0)
                skipped = stats.get("skipped", 0)
                
                complete_message = {
                    "type": "complete",
                    "step": step,
                    "total": len(rows),
                    "processed": filled,
                    "success": filled,
                    "errors": errors_count,
                    "skipped": skipped,
                }
                print(f"DEBUG: Sending WebSocket complete message EARLY to session {request.session_id}: {complete_message}", flush=True)
                has_connection = manager.has_active_connection(request.session_id)
                print(f"DEBUG: Active connections for session {request.session_id}: {has_connection}", flush=True)
                
                if has_connection:
                    try:
                        import asyncio
                        await asyncio.sleep(0.1)
                        await manager.broadcast_to_session(request.session_id, complete_message)
                        print(f"DEBUG: WebSocket complete message sent successfully (early)", flush=True)
                    except Exception as e:
                        print(f"ERROR: Failed to send WebSocket complete message (early): {e}", flush=True)
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"WARNING: No active WebSocket connections for session {request.session_id} (early send), message not sent", flush=True)
            
            # Write back only the AI Comparable Price column
            comparable_idx = col_indices.get('AI Comparable Price')
            if comparable_idx is not None:
                col_letter = get_column_letter(comparable_idx)
                start_row = 3
                end_row = start_row + len(updated_rows) - 1
                out_range = f"{sheet_name}!{col_letter}{start_row}:{col_letter}{end_row}" if sheet_name else f"{col_letter}{start_row}:{col_letter}{end_row}"
                values = [[row[comparable_idx] if len(row) > comparable_idx else ""] for row in updated_rows]
                update_sheet_data(sheetId, out_range, values)
                print(f"DEBUG: Wrote {len(updated_rows)} comparable entries to column {col_letter}", flush=True)
        elif step == "Extract price from AI Comparable":
            print(f"\n{'='*60}", flush=True)
            print(f"DEBUG: Starting Extract price from AI Comparable", flush=True)
            print(f"DEBUG: Processing {len(rows)} rows", flush=True)
            print(f"{'='*60}\n", flush=True)
            from process_steps import extract_final_price
            updated_rows, errors, filled_rows = await extract_final_price(rows, col_indices, custom_prompt=custom_prompt, session_id=request.session_id)
            print(f"\nDEBUG: extract_final_price completed. Filled {len(filled_rows)} rows, {len(errors)} errors\n", flush=True)
            # Write back only the price column - but only update rows that were actually filled
            price_idx = col_indices.get('Price')
            filled_rows_list = filled_rows
            
            # Count empty price rows before processing (for stats)
            empty_before = 0
            if price_idx is not None:
                for row in rows:
                    if len(row) <= price_idx or not row[price_idx] or not str(row[price_idx]).strip():
                        empty_before += 1
            
            if price_idx is not None and filled_rows:
                col_letter = get_column_letter(price_idx)
                print(f"DEBUG: Writing {len(filled_rows)} prices to column {col_letter}", flush=True)  # Debug log
                
                # Update each filled row individually for accuracy
                for row_num in filled_rows:
                    # Convert sheet row number to array index (row 3 = index 0)
                    array_idx = row_num - 3
                    if 0 <= array_idx < len(updated_rows):
                        row = updated_rows[array_idx]
                        price_value = row[price_idx] if len(row) > price_idx else ""
                        if price_value:  # Only update if we have a value
                            cell_range = f"{sheet_name}!{col_letter}{row_num}" if sheet_name else f"{col_letter}{row_num}"
                            try:
                                update_sheet_data(sheetId, cell_range, [[price_value]])
                                # Apply light blue color (#c9daf8) for Extract price step
                                from google_sheets import format_cell_color
                                format_cell_color(sheetId, sheet_name, col_letter, row_num, '#c9daf8')
                                print(f"DEBUG: Updated row {row_num} with price {price_value} (light blue)", flush=True)  # Debug log
                            except Exception as e:
                                errors.append(f'Row {row_num}: Failed to write to sheet: {str(e)}')
                                print(f"ERROR: Failed to update row {row_num}: {e}", flush=True)  # Debug log
            else:
                print(f"DEBUG: No rows to fill. Empty rows before: {empty_before}, Filled rows: {len(filled_rows) if filled_rows else 0}", flush=True)
        elif step == "AI Source New Price":
            print(f"\n{'='*60}", flush=True)
            print(f"DEBUG: Starting AI Source New Price", flush=True)
            print(f"DEBUG: Processing {len(rows)} rows", flush=True)
            print(f"{'='*60}\n", flush=True)
            from process_steps import ai_source_new_price
            updated_rows, errors, filled_rows = await ai_source_new_price(rows, col_indices, custom_prompt=custom_prompt, session_id=request.session_id)
            print(f"\nDEBUG: ai_source_new_price completed. Filled {len(filled_rows)} rows, {len(errors)} errors\n", flush=True)
            # Write back only the price column - but only update rows that were actually filled
            price_idx = col_indices.get('Price')
            filled_rows_list = filled_rows
            
            # Count empty price rows before processing (for stats)
            empty_before = 0
            if price_idx is not None:
                for row in rows:
                    if len(row) <= price_idx or not row[price_idx] or not str(row[price_idx]).strip():
                        empty_before += 1
            
            if price_idx is not None and filled_rows:
                col_letter = get_column_letter(price_idx)
                print(f"DEBUG: Writing {len(filled_rows)} new prices to column {col_letter}", flush=True)  # Debug log
                
                # Update each filled row individually for accuracy
                for row_num in filled_rows:
                    # Convert sheet row number to array index (row 3 = index 0)
                    array_idx = row_num - 3
                    if 0 <= array_idx < len(updated_rows):
                        row = updated_rows[array_idx]
                        price_value = row[price_idx] if len(row) > price_idx else ""
                        if price_value:  # Only update if we have a value
                            cell_range = f"{sheet_name}!{col_letter}{row_num}" if sheet_name else f"{col_letter}{row_num}"
                            try:
                                update_sheet_data(sheetId, cell_range, [[price_value]])
                                # Apply light yellow color (#fff2cc) for AI Source New Price step
                                from google_sheets import format_cell_color
                                format_cell_color(sheetId, sheet_name, col_letter, row_num, '#fff2cc')
                                print(f"DEBUG: Updated row {row_num} with new price {price_value} (light yellow)", flush=True)  # Debug log
                            except Exception as e:
                                errors.append(f'Row {row_num}: Failed to write to sheet: {str(e)}')
                                print(f"ERROR: Failed to update row {row_num}: {e}", flush=True)  # Debug log
            else:
                print(f"DEBUG: No rows to fill. Empty rows before: {empty_before}, Filled rows: {len(filled_rows) if filled_rows else 0}", flush=True)
        elif step == "AI Similar Comparable":
            print(f"\n{'='*60}", flush=True)
            print(f"DEBUG: Starting AI Similar Comparable", flush=True)
            print(f"DEBUG: Processing {len(rows)} rows", flush=True)
            print(f"{'='*60}\n", flush=True)
            from process_steps import ai_similar_comparable
            updated_rows, errors, filled_rows = await ai_similar_comparable(rows, col_indices, custom_prompt=custom_prompt, session_id=request.session_id)
            print(f"\nDEBUG: ai_similar_comparable completed. Filled {len(filled_rows)} rows, {len(errors)} errors\n", flush=True)
            # Write back only the price column - but only update rows that were actually filled
            price_idx = col_indices.get('Price')
            filled_rows_list = filled_rows
            
            # Count empty price rows before processing (for stats)
            empty_before = 0
            if price_idx is not None:
                for row in rows:
                    if len(row) <= price_idx or not row[price_idx] or not str(row[price_idx]).strip():
                        empty_before += 1
            
            if price_idx is not None and filled_rows:
                col_letter = get_column_letter(price_idx)
                print(f"DEBUG: Writing {len(filled_rows)} similar comparable prices to column {col_letter}", flush=True)
                
                # Update each filled row individually for accuracy
                for row_num in filled_rows:
                    # Convert sheet row number to array index (row 3 = index 0)
                    array_idx = row_num - 3
                    if 0 <= array_idx < len(updated_rows):
                        row = updated_rows[array_idx]
                        price_value = row[price_idx] if len(row) > price_idx else ""
                        if price_value:  # Only update if we have a value
                            cell_range = f"{sheet_name}!{col_letter}{row_num}" if sheet_name else f"{col_letter}{row_num}"
                            try:
                                update_sheet_data(sheetId, cell_range, [[price_value]])
                                # Apply light orange color (#e2c69b) for AI Similar Comparable step
                                from google_sheets import format_cell_color
                                format_cell_color(sheetId, sheet_name, col_letter, row_num, '#e2c69b')
                                print(f"DEBUG: Updated row {row_num} with similar comparable price {price_value} (light orange)", flush=True)
                            except Exception as e:
                                errors.append(f'Row {row_num}: Failed to write to sheet: {str(e)}')
                                print(f"ERROR: Failed to update row {row_num}: {e}", flush=True)
            else:
                print(f"DEBUG: No rows to fill. Empty rows before: {empty_before}, Filled rows: {len(filled_rows) if filled_rows else 0}", flush=True)
        else:
            return {"status": "error", "detail": f"Step '{step}' not implemented."}

        # Find any rows where Price is still empty
        price_idx = col_indices.get('Price')
        empty_prices = []
        if price_idx is not None:
            for i, row in enumerate(updated_rows):
                if len(row) <= price_idx or not row[price_idx]:
                    empty_prices.append(i+3)  # Row number in sheet

        # Prepare response
        response_data = {
            "status": "ok",
            "step": step,
            "errors": errors,
            "empty_price_rows": empty_prices
        }
        
        # Add stats based on step type
        if step == "Generate AI Data" and 'ai_data_stats_dict' in locals():
            response_data["stats"] = ai_data_stats_dict
        elif step == "Build Description" and 'build_description_stats' in locals():
            response_data["stats"] = build_description_stats
        elif step == "AI Source Comparables" and 'comparables_stats_dict' in locals():
            response_data["stats"] = comparables_stats_dict
        elif step in ["Extract price from AI Comparable", "AI Source New Price", "AI Similar Comparable"] and 'filled_rows_list' in locals():
            response_data["filled_rows"] = filled_rows_list
            # Add stats for better frontend feedback
            response_data["stats"] = {
                "total_rows": len(rows),
                "empty_before": empty_before if 'empty_before' in locals() else len(empty_prices),
                "filled": len(filled_rows_list),
                "empty_after": len(empty_prices),
                "errors_count": len(errors)
            }
        
        # Send completion update via WebSocket with final stats
        # NOTE: For "AI Source Comparables" and "Generate AI Data", the message is already sent early (before writing to sheet)
        # For other steps, send it here
        if request.session_id and step not in ["AI Source Comparables", "Generate AI Data"]:
            stats = response_data.get("stats", {})
            # Calculate skipped: rows that were already filled before processing
            # For Build Description: skipped = total - filled (newly filled) - errors
            # For Generate AI Data: use stats from the function
            # For other steps: use stats.skipped if available, otherwise calculate
            if step == "Build Description":
                filled = stats.get("filled", 0)
                errors_count = stats.get("errors_count", 0)
                skipped = len(rows) - filled - errors_count
            elif step == "Generate AI Data":
                filled = stats.get("success", 0)
                errors_count = stats.get("errors_count", 0)
                skipped = stats.get("skipped", 0)
            else:
                filled = stats.get("filled", 0) or len(response_data.get("filled_rows", []))
                errors_count = stats.get("errors_count", 0) or len(errors)
                skipped = stats.get("skipped", 0) or (len(rows) - filled - errors_count)
            
            complete_message = {
                "type": "complete",
                "step": step,
                "total": len(rows),
                "processed": filled,
                "success": filled,
                "errors": errors_count,
                "skipped": skipped,
            }
            print(f"DEBUG: Sending WebSocket complete message to session {request.session_id}: {complete_message}", flush=True)
            # Check if there are active connections before sending
            has_connection = manager.has_active_connection(request.session_id)
            print(f"DEBUG: Active connections for session {request.session_id}: {has_connection}", flush=True)
            
            if has_connection:
                try:
                    # Small delay to ensure WebSocket is ready
                    import asyncio
                    await asyncio.sleep(0.1)
                    await manager.broadcast_to_session(request.session_id, complete_message)
                    print(f"DEBUG: WebSocket complete message sent successfully", flush=True)
                except Exception as e:
                    print(f"ERROR: Failed to send WebSocket complete message: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
            else:
                print(f"WARNING: No active WebSocket connections for session {request.session_id}, message not sent", flush=True)
        else:
            print(f"WARNING: No session_id provided, skipping WebSocket complete message", flush=True)
        
        # Note: History is saved by frontend when WebSocket 'complete' message is received
        # This ensures the elapsed time is calculated correctly from the process startTime
        
        print(f"DEBUG: Returning response: {response_data}", flush=True)
        return response_data
    
    except Exception as e:
        import traceback
        error_msg = f"Error in process_step: {str(e)}"
        print(f"❌ {error_msg}", flush=True)
        print(f"Traceback:", flush=True)
        traceback.print_exc()
        
        # Send error update via WebSocket
        if request.session_id:
            await manager.broadcast_to_session(request.session_id, {
                "type": "error",
                "step": request.step,
                "message": error_msg,
            })
        
        raise HTTPException(status_code=500, detail=error_msg)


# History endpoints
@router.post("/history")
async def save_history_endpoint(request: HistoryRequest):
    """
    Save a history record to the database
    """
    try:
        history_id = await save_history(
            sheet_name=request.sheet_name,
            step=request.step,
            message=request.message,
            timestamp=request.timestamp,
            time=request.time
        )
        return {"status": "ok", "id": history_id}
    except Exception as e:
        import traceback
        error_msg = f"Error saving history: {str(e)}"
        print(f"❌ {error_msg}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/history")
async def get_history_endpoint(
    limit: int = Query(100, ge=1, le=1000),
    sheet_name: Optional[str] = Query(None)
):
    """
    Retrieve history records from the database
    
    Args:
        limit: Maximum number of records to return (default: 100, max: 1000)
        sheet_name: Optional filter by sheet name
    """
    try:
        if sheet_name:
            history = await get_history(limit=limit, sheet_name=sheet_name)
        else:
            # Return grouped by sheet name
            grouped = await get_history_by_sheet()
            # Convert to list format for compatibility
            history = []
            for sheet, records in grouped.items():
                history.extend(records[:limit])
            # Sort by timestamp descending
            history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            history = history[:limit]
        
        return {"status": "ok", "history": history}
    except Exception as e:
        import traceback
        error_msg = f"Error retrieving history: {str(e)}"
        print(f"❌ {error_msg}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/history/grouped")
async def get_history_grouped_endpoint():
    """
    Retrieve history records grouped by sheet name
    """
    try:
        grouped = await get_history_by_sheet()
        return {"status": "ok", "history": grouped}
    except Exception as e:
        import traceback
        error_msg = f"Error retrieving grouped history: {str(e)}"
        print(f"❌ {error_msg}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@router.delete("/history")
async def clear_history_endpoint():
    """
    Clear all history records (use with caution)
    """
    try:
        from database import clear_history
        await clear_history()
        return {"status": "ok", "message": "History cleared successfully"}
    except Exception as e:
        import traceback
        error_msg = f"Error clearing history: {str(e)}"
        print(f"❌ {error_msg}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/active-sessions")
async def get_active_sessions_endpoint():
    """
    Get list of active session IDs (processes that are currently running)
    """
    try:
        from websocket_manager import manager
        active_sessions = manager.get_active_sessions()
        return {"status": "ok", "active_sessions": active_sessions, "count": len(active_sessions)}
    except Exception as e:
        import traceback
        error_msg = f"Error retrieving active sessions: {str(e)}"
        print(f"❌ {error_msg}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/cancel-process/{session_id}")
async def cancel_process_endpoint(session_id: str):
    """
    Cancel a running process by session_id
    """
    try:
        from websocket_manager import manager
        manager.cancel_session(session_id)
        print(f"DEBUG: Process cancellation requested for session {session_id}", flush=True)
        return {"status": "ok", "message": f"Process {session_id} marked for cancellation"}
    except Exception as e:
        import traceback
        error_msg = f"Error cancelling process: {str(e)}"
        print(f"❌ {error_msg}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/active-processes")
async def get_active_processes_endpoint():
    """
    Get all active and recently completed processes (for shared Monitor)
    """
    try:
        processes = await get_active_processes()
        return {"status": "ok", "processes": processes}
    except Exception as e:
        import traceback
        error_msg = f"Error retrieving active processes: {str(e)}"
        print(f"❌ {error_msg}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

class ActiveProcessRequest(BaseModel):
    process_id: str
    step_name: str
    sheet_name: str
    session_id: str
    stats: dict
    elapsed_time: int = 0
    is_completed: bool = False
    is_active: bool = True
    progress: float = 0
    start_time: int

@router.post("/active-processes")
async def save_active_process_endpoint(request: ActiveProcessRequest):
    """
    Save or update an active process (for shared Monitor)
    """
    try:
        await save_or_update_process(
            process_id=request.process_id,
            step_name=request.step_name,
            sheet_name=request.sheet_name,
            session_id=request.session_id,
            stats=request.stats,
            elapsed_time=request.elapsed_time,
            is_completed=request.is_completed,
            is_active=request.is_active,
            progress=request.progress,
            start_time=request.start_time
        )
        return {"status": "ok"}
    except Exception as e:
        import traceback
        error_msg = f"Error saving active process: {str(e)}"
        print(f"❌ {error_msg}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@router.delete("/active-processes/{process_id}")
async def delete_active_process_endpoint(process_id: str):
    """
    Delete an active process (for shared Monitor)
    """
    try:
        await delete_process(process_id)
        return {"status": "ok"}
    except Exception as e:
        import traceback
        error_msg = f"Error deleting active process: {str(e)}"
        print(f"❌ {error_msg}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

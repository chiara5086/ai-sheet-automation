import os
from dotenv import load_dotenv
from pathlib import Path

# Get the backend directory path
backend_dir = Path(__file__).parent.absolute()
env_file = backend_dir / '.env'

# Load .env file - prioritize the main .env file in backend directory
# load_dotenv() loads in this order: .env.local, .env, then system env vars
# We want to explicitly load .env first, then .env.local if it exists
if env_file.exists():
    load_dotenv(dotenv_path=env_file, override=False)  # Load main .env first
    print(f"DEBUG: Loaded .env from: {env_file}")
else:
    print(f"WARNING: .env file not found at {env_file}")

# Also try .env.local (but don't override if .env already set the values)
env_local_file = backend_dir / '.env.local'
if env_local_file.exists():
    try:
        # Check if file is readable and not empty
        if env_local_file.stat().st_size > 0:
            # Try to load .env.local, but handle encoding errors gracefully
            try:
                load_dotenv(dotenv_path=env_local_file, override=False)  # Don't override existing values
                print(f"DEBUG: Also checked .env.local at: {env_local_file}")
            except UnicodeDecodeError as e:
                print(f"WARNING: .env.local has encoding issues (not UTF-8): {e}")
                print(f"         Skipping .env.local - using .env values only")
            except Exception as e:
                print(f"WARNING: Could not load .env.local: {e}")
                print(f"         Skipping .env.local - using .env values only")
        else:
            print(f"DEBUG: .env.local exists but is empty, skipping")
    except Exception as e:
        print(f"WARNING: Could not check .env.local: {e}")

# Get API keys and strip whitespace (common issue)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    OPENAI_API_KEY = OPENAI_API_KEY.strip()  # Remove leading/trailing whitespace
    # Remove quotes if present (common mistake)
    if OPENAI_API_KEY.startswith('"') and OPENAI_API_KEY.endswith('"'):
        OPENAI_API_KEY = OPENAI_API_KEY[1:-1].strip()
    if OPENAI_API_KEY.startswith("'") and OPENAI_API_KEY.endswith("'"):
        OPENAI_API_KEY = OPENAI_API_KEY[1:-1].strip()
    # Remove angle brackets if present (sometimes copied with formatting)
    if OPENAI_API_KEY.startswith('<') and OPENAI_API_KEY.endswith('>'):
        OPENAI_API_KEY = OPENAI_API_KEY[1:-1].strip()
    # Remove any remaining angle brackets or special characters at start/end
    while OPENAI_API_KEY and OPENAI_API_KEY[0] in ['<', '>', '{', '}', '[', ']', '(', ')']:
        OPENAI_API_KEY = OPENAI_API_KEY[1:].strip()
    while OPENAI_API_KEY and OPENAI_API_KEY[-1] in ['<', '>', '{', '}', '[', ']', '(', ')']:
        OPENAI_API_KEY = OPENAI_API_KEY[:-1].strip()
    
    # OpenAI API keys can be:
    # - Personal keys: sk-... (usually ~51 characters)
    # - Project keys: sk-proj-... (can be 100+ characters)
    # Both are valid, so we accept either format
    if not OPENAI_API_KEY.startswith('sk-'):
        # If it doesn't start with 'sk-', try to extract the actual key
        # Sometimes keys are embedded in other text or have extra formatting
        import re
        # Look for pattern: sk- or sk-proj- followed by alphanumeric characters and hyphens
        match = re.search(r'sk-proj-[a-zA-Z0-9\-]{50,}', OPENAI_API_KEY) or re.search(r'sk-[a-zA-Z0-9]{20,}', OPENAI_API_KEY)
        if match:
            OPENAI_API_KEY = match.group(0)
            print(f"DEBUG: Extracted API key from longer string (original length: {len(os.getenv('OPENAI_API_KEY'))}, extracted length: {len(OPENAI_API_KEY)})")

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
if PERPLEXITY_API_KEY:
    PERPLEXITY_API_KEY = PERPLEXITY_API_KEY.strip()
    if PERPLEXITY_API_KEY.startswith('"') and PERPLEXITY_API_KEY.endswith('"'):
        PERPLEXITY_API_KEY = PERPLEXITY_API_KEY[1:-1].strip()
    if PERPLEXITY_API_KEY.startswith("'") and PERPLEXITY_API_KEY.endswith("'"):
        PERPLEXITY_API_KEY = PERPLEXITY_API_KEY[1:-1].strip()
    
    # Debug logging for Perplexity key
    if PERPLEXITY_API_KEY:
        key_preview = f"{PERPLEXITY_API_KEY[:10]}...{PERPLEXITY_API_KEY[-4:]}" if len(PERPLEXITY_API_KEY) > 14 else "***"
        print(f"[OK] Perplexity API key loaded")
        print(f"   Preview: {key_preview}")
        print(f"   Length: {len(PERPLEXITY_API_KEY)} characters")
        print(f"   Starts with 'pplx-': {PERPLEXITY_API_KEY.startswith('pplx-')}")
    else:
        print("[WARNING] PERPLEXITY_API_KEY found but empty after cleaning")
else:
    print("[ERROR] PERPLEXITY_API_KEY not found in environment variables")

GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    GEMINI_API_KEY = GEMINI_API_KEY.strip()
    # Remove quotes if present
    if GEMINI_API_KEY.startswith('"') and GEMINI_API_KEY.endswith('"'):
        GEMINI_API_KEY = GEMINI_API_KEY[1:-1].strip()
    if GEMINI_API_KEY.startswith("'") and GEMINI_API_KEY.endswith("'"):
        GEMINI_API_KEY = GEMINI_API_KEY[1:-1].strip()
    
    # Debug logging for Gemini key
    if GEMINI_API_KEY:
        key_preview = f"{GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-4:]}" if len(GEMINI_API_KEY) > 14 else "***"
        print(f"[OK] Gemini API key loaded")
        print(f"   Preview: {key_preview}")
        print(f"   Length: {len(GEMINI_API_KEY)} characters")
        print(f"   Starts with 'AIzaSy': {GEMINI_API_KEY.startswith('AIzaSy')}")
    else:
        print("[WARNING] GEMINI_API_KEY found but empty after cleaning")
else:
    print("[ERROR] GEMINI_API_KEY not found in environment variables")

# Debug logging (without exposing the actual key)
print(f"\n{'='*60}")
print("DEBUG: Environment Configuration")
print(f"{'='*60}")

# Check OpenAI key
if OPENAI_API_KEY:
    key_preview = f"{OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-4:]}" if len(OPENAI_API_KEY) > 14 else "***"
    print(f"[OK] OpenAI API key loaded")
    print(f"   Preview: {key_preview}")
    print(f"   Length: {len(OPENAI_API_KEY)} characters")
    print(f"   Type: {'Project key (sk-proj-...)' if OPENAI_API_KEY.startswith('sk-proj-') else 'Personal key (sk-...)' if OPENAI_API_KEY.startswith('sk-') else 'Unknown format'}")
    if not OPENAI_API_KEY.startswith('sk-'):
        print(f"   [WARNING] API key doesn't start with 'sk-' or 'sk-proj-' - this might be incorrect")
else:
    print("[ERROR] OPENAI_API_KEY not found in environment variables")
    print("   Check your .env file in the backend directory")

# Check Perplexity key
print()  # Empty line for readability
if PERPLEXITY_API_KEY:
    key_preview = f"{PERPLEXITY_API_KEY[:10]}...{PERPLEXITY_API_KEY[-4:]}" if len(PERPLEXITY_API_KEY) > 14 else "***"
    print(f"[OK] Perplexity API key loaded")
    print(f"   Preview: {key_preview}")
    print(f"   Length: {len(PERPLEXITY_API_KEY)} characters")
    print(f"   Starts with 'pplx-': {PERPLEXITY_API_KEY.startswith('pplx-')}")
else:
    print("[ERROR] PERPLEXITY_API_KEY not found in environment variables")
    print("   Check your .env file in the backend directory")
    print(f"   Looking for PERPLEXITY_API_KEY in .env at: {env_file}")

# Check Gemini key
print()  # Empty line for readability
if GEMINI_API_KEY:
    key_preview = f"{GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-4:]}" if len(GEMINI_API_KEY) > 14 else "***"
    print(f"[OK] Gemini API key loaded")
    print(f"   Preview: {key_preview}")
    print(f"   Length: {len(GEMINI_API_KEY)} characters")
    print(f"   Starts with 'AIzaSy': {GEMINI_API_KEY.startswith('AIzaSy')}")
else:
    print("[ERROR] GEMINI_API_KEY not found in environment variables")
    print("   Check your .env file in the backend directory")

print(f"{'='*60}\n")

#!/usr/bin/env python
"""
Script para listar los modelos disponibles de Gemini
"""
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

# Load .env file
env_file = backend_dir / '.env'
if env_file.exists():
    load_dotenv(dotenv_path=env_file)

import google.generativeai as genai

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY not found in .env file")
    sys.exit(1)

GEMINI_API_KEY = GEMINI_API_KEY.strip()
if GEMINI_API_KEY.startswith('"') and GEMINI_API_KEY.endswith('"'):
    GEMINI_API_KEY = GEMINI_API_KEY[1:-1].strip()
if GEMINI_API_KEY.startswith("'") and GEMINI_API_KEY.endswith("'"):
    GEMINI_API_KEY = GEMINI_API_KEY[1:-1].strip()

try:
    genai.configure(api_key=GEMINI_API_KEY)
    
    print("=" * 60)
    print("Modelos disponibles de Gemini:")
    print("=" * 60)
    
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"\n[OK] {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description}")
            print(f"   Supported methods: {model.supported_generation_methods}")
    
    print("\n" + "=" * 60)
    print("Recomendación: Usa el nombre corto del modelo (ej: 'gemini-pro')")
    print("=" * 60)
    
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)


#!/usr/bin/env python
"""
Script de prueba para verificar que el backend está funcionando correctamente.
Ejecuta este script para verificar la configuración antes de usar la aplicación.
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_imports():
    """Verifica que todas las dependencias están instaladas."""
    print("=" * 60)
    print("1. Verificando imports...")
    print("=" * 60)
    
    try:
        import fastapi
        print("[OK] FastAPI")
    except ImportError:
        print("[ERROR] FastAPI - Ejecuta: pip install fastapi")
        return False
    
    try:
        import uvicorn
        print("[OK] Uvicorn")
    except ImportError:
        print("[ERROR] Uvicorn - Ejecuta: pip install uvicorn[standard]")
        return False
    
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        print("[OK] Google API Client")
    except ImportError:
        print("[ERROR] Google API Client - Ejecuta: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return False
    
    try:
        from openai import OpenAI
        print("[OK] OpenAI")
    except ImportError:
        print("[ERROR] OpenAI - Ejecuta: pip install openai>=1.0.0")
        return False
    
    try:
        import requests
        print("[OK] Requests")
    except ImportError:
        print("[ERROR] Requests - Ejecuta: pip install requests")
        return False
    
    try:
        from dotenv import load_dotenv
        print("[OK] Python-dotenv")
    except ImportError:
        print("[ERROR] Python-dotenv - Ejecuta: pip install python-dotenv")
        return False
    
    return True

def test_config():
    """Verifica que la configuración está correcta."""
    print("\n" + "=" * 60)
    print("2. Verificando configuración...")
    print("=" * 60)
    
    try:
        import config
        print("[OK] Modulo config cargado")
    except Exception as e:
        print(f"[ERROR] Error cargando config: {e}")
        return False
    
    # Verificar variables de entorno
    from config import OPENAI_API_KEY, PERPLEXITY_API_KEY, GOOGLE_SERVICE_ACCOUNT_JSON
    
    if OPENAI_API_KEY:
        key_preview = f"{OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-4:]}" if len(OPENAI_API_KEY) > 14 else "***"
        print(f"[OK] OPENAI_API_KEY encontrada (preview: {key_preview})")
    else:
        print("[ERROR] OPENAI_API_KEY no encontrada - Agrega OPENAI_API_KEY a backend/.env")
        return False
    
    if PERPLEXITY_API_KEY:
        key_preview = f"{PERPLEXITY_API_KEY[:10]}...{PERPLEXITY_API_KEY[-4:]}" if len(PERPLEXITY_API_KEY) > 14 else "***"
        print(f"[OK] PERPLEXITY_API_KEY encontrada (preview: {key_preview})")
    else:
        print("[WARNING] PERPLEXITY_API_KEY no encontrada - Opcional pero recomendado")
    
    if GOOGLE_SERVICE_ACCOUNT_JSON:
        try:
            import json
            json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
            print("[OK] GOOGLE_SERVICE_ACCOUNT_JSON encontrada y valida")
        except json.JSONDecodeError:
            print("[ERROR] GOOGLE_SERVICE_ACCOUNT_JSON no es un JSON valido")
            return False
    else:
        print("[ERROR] GOOGLE_SERVICE_ACCOUNT_JSON no encontrada - Agrega GOOGLE_SERVICE_ACCOUNT_JSON a backend/.env")
        return False
    
    return True

def test_google_sheets():
    """Verifica que la conexión con Google Sheets funciona."""
    print("\n" + "=" * 60)
    print("3. Verificando conexión con Google Sheets...")
    print("=" * 60)
    
    try:
        from google_sheets import get_service
        service = get_service()
        print("[OK] Servicio de Google Sheets creado correctamente")
        return True
    except Exception as e:
        print(f"[ERROR] Error conectando con Google Sheets: {e}")
        print("   Verifica que GOOGLE_SERVICE_ACCOUNT_JSON es correcta")
        return False

def test_openai():
    """Verifica que la API de OpenAI es accesible."""
    print("\n" + "=" * 60)
    print("4. Verificando API de OpenAI...")
    print("=" * 60)
    
    try:
        from openai import OpenAI
        from config import OPENAI_API_KEY
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        # Hacer una llamada simple para verificar
        models = client.models.list()
        print("[OK] Conexion con OpenAI API exitosa")
        return True
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "authentication" in error_msg.lower():
            print(f"[ERROR] Error de autenticacion con OpenAI: {e}")
            print("   Verifica que tu OPENAI_API_KEY es valida")
        else:
            print(f"[WARNING] Error verificando OpenAI (puede ser temporal): {e}")
        return False

def test_perplexity():
    """Verifica que la API de Perplexity es accesible (opcional)."""
    print("\n" + "=" * 60)
    print("5. Verificando API de Perplexity (opcional)...")
    print("=" * 60)
    
    try:
        from config import PERPLEXITY_API_KEY
        if not PERPLEXITY_API_KEY:
            print("[WARNING] PERPLEXITY_API_KEY no configurada - Saltando verificacion")
            return True
        
        import requests
        
        # Hacer una llamada simple para verificar
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("[OK] Conexion con Perplexity API exitosa")
            return True
        elif response.status_code == 401:
            print("[ERROR] Error de autenticacion con Perplexity")
            print("   Verifica que tu PERPLEXITY_API_KEY es valida")
            return False
        else:
            print(f"[WARNING] Respuesta inesperada de Perplexity: {response.status_code}")
            return False
    except Exception as e:
        print(f"[WARNING] Error verificando Perplexity (puede ser temporal): {e}")
        return True  # No critico

def test_fastapi_app():
    """Verifica que la aplicación FastAPI se puede crear."""
    print("\n" + "=" * 60)
    print("6. Verificando aplicación FastAPI...")
    print("=" * 60)
    
    try:
        from main import app
        print("[OK] Aplicacion FastAPI creada correctamente")
        
        # Verificar rutas
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        print(f"[OK] {len(routes)} rutas registradas")
        return True
    except Exception as e:
        print(f"[ERROR] Error creando aplicacion FastAPI: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecuta todas las pruebas."""
    # Set UTF-8 encoding for Windows
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("\n" + "=" * 60)
    print("PRUEBAS DEL BACKEND - AI Sheet Automation")
    print("=" * 60 + "\n")
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Configuración", test_config()))
    results.append(("Google Sheets", test_google_sheets()))
    results.append(("OpenAI API", test_openai()))
    results.append(("Perplexity API", test_perplexity()))
    results.append(("FastAPI App", test_fastapi_app()))
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK] PASO" if result else "[ERROR] FALLO"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 60)
    if passed == total:
        print(f"[OK] Todas las pruebas pasaron! ({passed}/{total})")
        print("[OK] El backend esta listo para usar")
    else:
        print(f"[WARNING] {passed}/{total} pruebas pasaron")
        print("[ERROR] Revisa los errores arriba antes de continuar")
    print("=" * 60 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


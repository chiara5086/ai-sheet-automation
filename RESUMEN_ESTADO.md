# Resumen del Estado - AI Sheet Automation

## ✅ Estado Actual

### Backend
- **Estado**: ✅ Funcional
- **Puerto**: 9000
- **Framework**: FastAPI
- **Pruebas**: 5/6 pasaron (Perplexity tiene un warning menor)

### Frontend
- **Estado**: ✅ Funcional
- **Puerto**: 3000
- **Framework**: React + Material-UI
- **Estado**: Listo para usar

### Configuración
- ✅ OpenAI API Key configurada
- ✅ Perplexity API Key configurada
- ✅ Google Service Account configurada

## 🚀 Cómo Iniciar la Aplicación

### Opción 1: Script Automático (Windows PowerShell)
```powershell
.\start_servers.ps1
```

### Opción 2: Manual

**Terminal 1 - Backend:**
```bash
cd backend
python run_server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

## 🧪 Verificar Configuración

Antes de usar la aplicación, ejecuta las pruebas:

```bash
cd backend
python test_backend.py
```

## 📋 Funcionalidades Disponibles

1. **Build Description**
   - Genera descripciones técnicas usando Perplexity/OpenAI
   - Requiere: YOM OEM Model, Technical Specifications

2. **AI Source Comparables**
   - Encuentra comparables en el mercado
   - Requiere: YOM OEM Model, Technical Specifications

3. **Extract Price from AI Comparable**
   - Extrae precios de los comparables encontrados
   - Colorea celdas en azul claro (#c9daf8)

4. **AI Source New Price**
   - Genera precios nuevos para productos sin precio
   - Colorea celdas en amarillo claro (#fff2cc)

5. **AI Similar Comparable**
   - (Implementación pendiente o en desarrollo)

## 📝 Notas

- El backend detecta automáticamente la pestaña "Structured Data" en Google Sheets
- Los headers deben estar en la fila 2
- Los datos deben comenzar en la fila 3
- El frontend muestra un historial detallado de todas las operaciones

## 🔧 Solución de Problemas

Si encuentras problemas:

1. **Verifica las pruebas**: `python backend/test_backend.py`
2. **Revisa los logs**: El backend muestra logs detallados en la consola
3. **Consulta TESTING_GUIDE.md**: Guía completa de pruebas y troubleshooting

## 📚 Archivos de Ayuda

- `TESTING_GUIDE.md` - Guía completa de pruebas
- `backend/test_backend.py` - Script de verificación
- `start_servers.ps1` - Script para iniciar servidores (Windows)


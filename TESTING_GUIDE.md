# Guía de Pruebas - AI Sheet Automation

## 📋 Pre-requisitos

Antes de comenzar a probar, asegúrate de tener:

1. **Variables de entorno configuradas** en `backend/.env`:
   - `OPENAI_API_KEY` - Tu clave de API de OpenAI
   - `PERPLEXITY_API_KEY` - Tu clave de API de Perplexity (opcional pero recomendado)
   - `GOOGLE_SERVICE_ACCOUNT_JSON` - JSON de la cuenta de servicio de Google (como string JSON)

2. **Dependencias instaladas**:
   - Backend: `pip install -r backend/requirements.txt`
   - Frontend: `npm install` (en el directorio `frontend`)

## 🚀 Iniciar la Aplicación

### Backend (Puerto 9000)
```bash
cd backend
python run_server.py
```

O alternativamente:
```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 9000 --reload
```

### Frontend (Puerto 3000)
```bash
cd frontend
npm start
```

## ✅ Verificación Inicial

### 1. Verificar Backend
- Abre tu navegador en: `http://localhost:9000`
- Deberías ver: `{"message": "AI Sheet Automation Backend is running"}`
- Health check: `http://localhost:9000/health`
- Deberías ver: `{"status": "ok", "message": "Backend is healthy"}`

### 2. Verificar Frontend
- Abre tu navegador en: `http://localhost:3000`
- Deberías ver la interfaz de AI Sheet Automation

### 3. Verificar Configuración
Ejecuta el script de verificación:
```bash
cd backend
python test_key.py
```

## 🧪 Pruebas de Funcionalidad

### Test 1: Conexión con Google Sheets
1. En el frontend, pega una URL de Google Sheet válida
2. La aplicación debería:
   - Detectar automáticamente la pestaña "Structured Data"
   - Mostrar los headers y las primeras filas en el preview
   - Mostrar un mensaje de éxito en el historial

### Test 2: Build Description
1. Asegúrate de tener una hoja con:
   - Columna "YOM OEM Model T2/T3/T4 Category" (o similar)
   - Columna "Technical Specifications"
   - Columna "AI Description" (puede estar vacía)
2. Haz clic en "Build Description"
3. Verifica:
   - La barra de progreso aparece
   - El tiempo transcurrido se muestra
   - Las descripciones se generan y se escriben en la hoja
   - El historial muestra el resultado

### Test 3: AI Source Comparables
1. Asegúrate de tener:
   - Columna "YOM OEM Model" (o similar)
   - Columna "Technical Specifications"
   - Columna "AI Comparable Price" (puede estar vacía)
2. Haz clic en "AI Source Comparables"
3. Verifica que se llenen los comparables

### Test 4: Extract Price from AI Comparable
1. Asegúrate de tener:
   - Columna "AI Comparable Price" (con datos del paso anterior)
   - Columna "Price" (puede estar vacía)
2. Haz clic en "Extract Price from AI Comparable"
3. Verifica:
   - Los precios se extraen y se escriben en la columna "Price"
   - Las celdas se colorean en azul claro (#c9daf8)

### Test 5: AI Source New Price
1. Asegúrate de tener filas con "Price" vacío
2. Haz clic en "AI Source New Price"
3. Verifica:
   - Los precios se generan y se escriben
   - Las celdas se colorean en amarillo claro (#fff2cc)

## 🐛 Solución de Problemas

### Error: "OPENAI_API_KEY not found"
- Verifica que el archivo `backend/.env` existe
- Verifica que la clave está correctamente escrita (sin comillas extra)
- La clave debe empezar con `sk-` o `sk-proj-`

### Error: "PERPLEXITY_API_KEY not found"
- Esto es opcional, pero recomendado
- La clave debe empezar con `pplx-`

### Error: "GOOGLE_SERVICE_ACCOUNT_JSON not found"
- Necesitas crear una cuenta de servicio en Google Cloud Console
- Descarga el JSON y cópialo como string en el `.env`
- Asegúrate de que la cuenta de servicio tenga acceso a la hoja

### Error: "Could not find 'Structured Data' tab"
- Asegúrate de que tu hoja tiene una pestaña que comienza con "Structured Data"
- O proporciona el nombre de la pestaña manualmente

### Error: "Missing headers"
- Verifica que tu hoja tiene los headers requeridos en la fila 2
- Los headers deben coincidir con los nombres esperados (pueden tener variaciones)

### El backend no responde
- Verifica que el puerto 9000 no está en uso
- Revisa los logs del backend para ver errores
- Verifica que todas las dependencias están instaladas

### El frontend no se conecta al backend
- Verifica que el backend está corriendo
- Verifica la variable `REACT_APP_API_BASE` en el frontend (por defecto: `http://localhost:9000`)
- Revisa la consola del navegador para errores CORS

## 📊 Monitoreo

### Logs del Backend
El backend muestra logs detallados en la consola:
- ✅ Operaciones exitosas
- ❌ Errores
- 🔵 Requests entrantes
- 📊 Resúmenes de procesamiento

### Historial en Frontend
El panel de historial muestra:
- Operaciones completadas
- Tiempos de ejecución
- Errores encontrados
- Estadísticas de procesamiento

## 🔄 Flujo Completo de Prueba

1. **Cargar hoja**: Conecta una hoja de Google Sheets
2. **Build Description**: Genera descripciones para productos
3. **AI Source Comparables**: Encuentra comparables en el mercado
4. **Extract Price**: Extrae precios de los comparables
5. **AI Source New Price**: Genera precios nuevos para filas sin precio

Cada paso debe completarse exitosamente antes de pasar al siguiente.


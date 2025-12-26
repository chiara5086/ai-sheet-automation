import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:9000';


// Fetch sheet preview (headers + first rows) from backend
export const fetchSheetPreview = async (sheetUrl, sheetName) => {
  return axios.get(`${API_BASE}/sheet-preview`, { params: { sheet_url: sheetUrl, sheet_name: sheetName } });
};

export const runProcessStep = async (sheetId, step, sheetName = null, signal = null) => {
  console.log(`DEBUG: Making POST request to ${API_BASE}/process`);
  console.log(`DEBUG: Payload:`, { sheetId, step, sheet_name: sheetName });
  console.log(`DEBUG: Full URL: ${API_BASE}/process`);
  
  try {
    const response = await axios.post(`${API_BASE}/process`, { 
      sheetId, 
      step, 
      sheet_name: sheetName 
    }, {
      timeout: 1800000, // 30 minutes timeout for long processing (100k rows will take time)
      headers: {
        'Content-Type': 'application/json',
      },
      signal: signal, // Add AbortController signal to cancel request
    });
    console.log('DEBUG: Response received! Status:', response.status);
    console.log('DEBUG: Response data:', response.data);
    return response;
  } catch (error) {
    console.error('DEBUG: Axios error:', error);
    console.error('DEBUG: Error message:', error.message);
    console.error('DEBUG: Error code:', error.code);
    console.error('DEBUG: Error response:', error.response);
    if (error.code === 'ECONNABORTED') {
      console.error('DEBUG: Request timed out after 30 minutes');
    }
    if (axios.isCancel(error)) {
      console.log('DEBUG: Request was cancelled');
    }
    throw error;
  }
};

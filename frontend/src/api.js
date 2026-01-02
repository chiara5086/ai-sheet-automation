import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:9000';


// Fetch sheet preview (headers + first rows) from backend
export const fetchSheetPreview = async (sheetUrl, sheetName) => {
  return axios.get(`${API_BASE}/sheet-preview`, { params: { sheet_url: sheetUrl, sheet_name: sheetName } });
};

export const runProcessStep = async (sheetId, step, sheetName = null, signal = null, sessionId = null, customPrompt = null) => {
  console.log(`DEBUG: Making POST request to ${API_BASE}/process`);
  console.log(`DEBUG: Payload:`, { sheetId, step, sheet_name: sheetName, session_id: sessionId, custom_prompt: customPrompt ? 'provided' : 'none' });
  console.log(`DEBUG: Full URL: ${API_BASE}/process`);
  
  try {
    const response = await axios.post(`${API_BASE}/process`, { 
      sheetId, 
      step, 
      sheet_name: sheetName,
      session_id: sessionId,
      custom_prompt: customPrompt
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

// History API functions
export const saveHistory = async (sheetName, step, message, timestamp, time) => {
  try {
    const response = await axios.post(`${API_BASE}/history`, {
      sheet_name: sheetName,
      step: step,
      message: message,
      timestamp: timestamp,
      time: time,
    });
    return response.data;
  } catch (error) {
    console.error('Error saving history:', error);
    throw error;
  }
};

export const getHistory = async (limit = 100, sheetName = null) => {
  try {
    const params = { limit };
    if (sheetName) {
      params.sheet_name = sheetName;
    }
    const response = await axios.get(`${API_BASE}/history`, { params });
    return response.data;
  } catch (error) {
    console.error('Error retrieving history:', error);
    throw error;
  }
};

export const getHistoryGrouped = async () => {
  try {
    const response = await axios.get(`${API_BASE}/history/grouped`);
    return response.data;
  } catch (error) {
    console.error('Error retrieving grouped history:', error);
    throw error;
  }
};

export const clearHistory = async () => {
  try {
    const response = await axios.delete(`${API_BASE}/history`);
    return response.data;
  } catch (error) {
    console.error('Error clearing history:', error);
    throw error;
  }
};

export const getActiveSessions = async () => {
  try {
    const response = await axios.get(`${API_BASE}/active-sessions`);
    return response.data;
  } catch (error) {
    console.error('Error retrieving active sessions:', error);
    throw error;
  }
};

export const getActiveProcesses = async () => {
  try {
    const response = await axios.get(`${API_BASE}/active-processes`);
    return response.data;
  } catch (error) {
    console.error('Error retrieving active processes:', error);
    throw error;
  }
};

export const saveActiveProcess = async (processData) => {
  try {
    const response = await axios.post(`${API_BASE}/active-processes`, processData);
    return response.data;
  } catch (error) {
    console.error('Error saving active process:', error);
    throw error;
  }
};

export const deleteActiveProcess = async (processId) => {
  try {
    const response = await axios.delete(`${API_BASE}/active-processes/${processId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting active process:', error);
    throw error;
  }
};

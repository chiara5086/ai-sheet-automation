import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Typography,
  Button,
  Box,
  AppBar,
  Toolbar,
  Card,
  CardContent,
  IconButton,
  Snackbar,
  Alert,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import TablePreview from '../components/TablePreview';
import SheetSelector from '../components/SheetSelector';
import RealTimeProgress from '../components/RealTimeProgress';
import NotificationBell from '../components/NotificationBell';
import StepSelector from '../components/StepSelector';
import InstructionsCard from '../components/InstructionsCard';
import { DEFAULT_PROMPTS } from '../components/PromptEditor';
import { fetchSheetPreview, runProcessStep } from '../api';
import HistoryIcon from '@mui/icons-material/History';

const STEPS = [
  { id: 1, name: 'Build Description', color: '#1a2746' },
  { id: 2, name: 'AI Source Comparables', color: '#ff8200' },
  { id: 3, name: 'Extract price from AI Comparable', color: '#2196f3' },
  { id: 4, name: 'AI Source New Price', color: '#ff9800' },
  { id: 5, name: 'AI Similar Comparable', color: '#e2c69b' },
];

export default function Home() {
  const navigate = useNavigate();
  const [sheetUrl, setSheetUrl] = useState('');
  const [sheetHeaders, setSheetHeaders] = useState([]);
  const [sheetRows, setSheetRows] = useState([]);
  const [sheetName, setSheetName] = useState(null);
  const [priceStepMap, setPriceStepMap] = useState({});
  const [notifications, setNotifications] = useState([]);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(null);
  const [progressStats, setProgressStats] = useState({
    total: 0,
    processed: 0,
    success: 0,
    errors: 0,
    skipped: 0,
  });
  const [elapsedTime, setElapsedTime] = useState(0);
  const [customPrompts, setCustomPrompts] = useState({});
  const timerRef = useRef(null);
  const startTimeRef = useRef(null);
  const abortControllerRef = useRef(null);
  const wsRef = useRef(null);
  const sessionIdRef = useRef(null);

  // Step colors
  const stepColors = {
    'Extract price from AI Comparable': '#c9daf8',
    'AI Source New Price': '#fff2cc',
    'AI Similar Comparable': '#e2c69b',
  };

  // Initialize WebSocket connection
  useEffect(() => {
    if (!sessionIdRef.current) {
      sessionIdRef.current = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:9000';
    const wsUrl = API_BASE.replace('http', 'ws') + `/ws/${sessionIdRef.current}`;
    
    try {
      const ws = new WebSocket(wsUrl);
      ws.onopen = () => {
        console.log('WebSocket connected');
      };
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'progress') {
            setProgressStats({
              total: data.total || 0,
              processed: data.processed || 0,
              success: data.success || 0,
              errors: data.errors || 0,
              skipped: data.skipped || 0,
            });
          } else if (data.type === 'complete') {
            setIsProcessing(false);
            setCurrentStep(null);
            addNotification('success', `Step '${data.step}' completed`, `Processed ${data.processed} rows successfully`);
            showSnackbar(`Step '${data.step}' completed successfully!`, 'success');
          } else if (data.type === 'error') {
            setIsProcessing(false);
            setCurrentStep(null);
            addNotification('error', `Step '${data.step}' failed`, data.message || 'An error occurred');
            showSnackbar(`Error: ${data.message}`, 'error');
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
      wsRef.current = ws;
    } catch (e) {
      console.error('Failed to create WebSocket:', e);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Timer for elapsed time
  useEffect(() => {
    if (isProcessing) {
      if (!timerRef.current) {
        startTimeRef.current = Date.now();
        timerRef.current = setInterval(() => {
          if (startTimeRef.current) {
            const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
            setElapsedTime(elapsed);
          }
        }, 100);
      }
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      if (!isProcessing) {
        setElapsedTime(0);
        startTimeRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isProcessing]);

  const addNotification = (type, title, message) => {
    const notification = {
      id: Date.now(),
      type,
      title,
      message,
      time: new Date().toLocaleTimeString(),
      read: false,
    };
    setNotifications((prev) => [notification, ...prev]);
  };

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleClearNotifications = () => {
    setNotifications([]);
  };

  const handleSavePrompt = (stepName, prompt) => {
    setCustomPrompts((prev) => ({ ...prev, [stepName]: prompt }));
    showSnackbar('Prompt saved successfully!', 'success');
  };

  const handleSheetSelected = async (url) => {
    setSheetUrl(url);
    try {
      const res = await fetchSheetPreview(url);
      setSheetHeaders(res.data.headers);
      setSheetRows(res.data.rows);
      if (res.data.sheet_name) {
        setSheetName(res.data.sheet_name);
      }
      addNotification('info', 'Sheet loaded', `${res.data.sheet_name || 'Sheet'} loaded with ${res.data.rows.length} rows`);
      
      // Save to history
      const historyItem = {
        sheetName: res.data.sheet_name || 'Unknown Sheet',
        message: `Sheet loaded: ${res.data.sheet_name || 'default tab'} with ${res.data.headers.length} columns and ${res.data.rows.length} rows`,
        timestamp: new Date().toISOString(),
        time: new Date().toLocaleTimeString(),
      };
      const savedHistory = JSON.parse(localStorage.getItem('sheetHistory') || '[]');
      savedHistory.unshift(historyItem);
      localStorage.setItem('sheetHistory', JSON.stringify(savedHistory.slice(0, 100))); // Keep last 100
    } catch (err) {
      addNotification('error', 'Error loading sheet', err.message);
      showSnackbar(`Error loading sheet: ${err.message}`, 'error');
    }
  };

  const handleRunStep = async (stepName, customPrompt = null) => {
    if (isProcessing) {
      showSnackbar('Another step is already running. Please wait.', 'warning');
      return;
    }

    if (!sheetUrl) {
      showSnackbar('Please load a sheet first', 'warning');
      return;
    }

    setIsProcessing(true);
    setCurrentStep(stepName);
    setProgressStats({ total: 0, processed: 0, success: 0, errors: 0, skipped: 0 });
    setElapsedTime(0);
    startTimeRef.current = Date.now();

    abortControllerRef.current = new AbortController();
    addNotification('info', `Step started: ${stepName}`, 'Processing has begun');
    showSnackbar(`Starting ${stepName}...`, 'info');

    try {
      const match = sheetUrl.match(/\/d\/([a-zA-Z0-9-_]+)/);
      const sheetId = match ? match[1] : null;
      if (!sheetId) throw new Error('Invalid sheet URL');

      // Use custom prompt if provided, otherwise use saved custom prompt or default
      const promptToUse = customPrompt || customPrompts[stepName] || DEFAULT_PROMPTS[stepName] || null;

      // Include session_id for WebSocket updates
      const res = await runProcessStep(
        sheetId,
        stepName,
        sheetName,
        abortControllerRef.current?.signal,
        sessionIdRef.current,
        promptToUse
      );

      setIsProcessing(false);
      setCurrentStep(null);

      const errors = res.data?.errors || [];
      const filledRows = res.data?.filled_rows || [];
      const stats = res.data?.stats || {};

      // Update progress stats
      setProgressStats({
        total: stats.total || sheetRows.length,
        processed: stats.filled || filledRows.length || 0,
        success: stats.filled || 0,
        errors: stats.errors_count || errors.length || 0,
        skipped: (stats.total || 0) - (stats.filled || 0) - (stats.errors_count || 0),
      });

      const finalTime = startTimeRef.current
        ? Math.floor((Date.now() - startTimeRef.current) / 1000)
        : elapsedTime;

      let successMsg = `Step '${stepName}' completed in ${formatTime(finalTime)}.`;
      if (stats.filled > 0) {
        successMsg += ` Filled ${stats.filled} row(s).`;
      }
      if (stats.errors_count > 0) {
        successMsg += ` ${stats.errors_count} error(s).`;
      }

      addNotification('success', `Step completed: ${stepName}`, successMsg);
      showSnackbar(successMsg, 'success');

      // Save to history
      const historyItem = {
        sheetName: sheetName || 'Unknown Sheet',
        step: stepName,
        message: successMsg,
        timestamp: new Date().toISOString(),
        time: new Date().toLocaleTimeString(),
      };
      const savedHistory = JSON.parse(localStorage.getItem('sheetHistory') || '[]');
      savedHistory.unshift(historyItem);
      localStorage.setItem('sheetHistory', JSON.stringify(savedHistory.slice(0, 100)));

      // Update price step map
      if (filledRows && filledRows.length > 0) {
        setPriceStepMap((prev) => {
          const updated = { ...prev };
          filledRows.forEach((rowIdx) => {
            updated[rowIdx] = stepName;
          });
          return updated;
        });
      }

      // Refresh sheet data
      if (sheetUrl) {
        const res = await fetchSheetPreview(sheetUrl);
        setSheetRows(res.data.rows);
      }
    } catch (err) {
      setIsProcessing(false);
      setCurrentStep(null);
      const errorMsg = err.response?.data?.detail || err.message || 'Unknown error';
      
      if (err.name === 'CanceledError' || err.message === 'canceled') {
        addNotification('info', `Step cancelled: ${stepName}`, 'Process was cancelled by user');
        showSnackbar(`Step '${stepName}' was cancelled`, 'info');
      } else {
        addNotification('error', `Step failed: ${stepName}`, errorMsg);
        showSnackbar(`Error: ${errorMsg}`, 'error');
      }
    }
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsProcessing(false);
      setCurrentStep(null);
      setElapsedTime(0);
      startTimeRef.current = null;
      abortControllerRef.current = null;
      addNotification('info', 'Process cancelled', 'The current process was cancelled');
      showSnackbar('Process cancelled', 'info');
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <>
      <AppBar position="static" sx={{ backgroundColor: '#1a2746', boxShadow: 2, borderRadius: 0 }}>
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Typography variant="h5" component="div" sx={{ fontWeight: 700, color: '#ffffff' }}>
            Data Structuring Sheet App
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton
              onClick={() => navigate('/history')}
              sx={{ color: '#fff', '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' } }}
            >
              <HistoryIcon />
            </IconButton>
            <NotificationBell
              notifications={notifications}
              onClearAll={handleClearNotifications}
            />
          </Box>
        </Toolbar>
      </AppBar>

      <Box sx={{ background: '#f5f5f5', minHeight: 'calc(100vh - 64px)', py: 4 }}>
        <Container maxWidth="xl">
          {/* Instructions Card */}
          {!sheetHeaders.length && (
            <InstructionsCard />
          )}

          {/* Sheet Selection Card */}
          <Card sx={{ mb: 4, borderRadius: 2, boxShadow: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: '#1a2746', mb: 3 }}>
                Connect Google Sheet
              </Typography>
              <SheetSelector onSheetSelected={handleSheetSelected} />
            </CardContent>
          </Card>

          {/* Process Steps Section */}
          {sheetHeaders.length > 0 && (
            <>
              <Card sx={{ mb: 4, borderRadius: 2, boxShadow: 3 }}>
                <CardContent sx={{ p: 3 }}>
                  <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: '#1a2746', mb: 3 }}>
                    Automation Steps
                  </Typography>

                  {/* Real-time Progress */}
                  {isProcessing && (
                    <RealTimeProgress
                      isActive={isProcessing}
                      currentStep={currentStep}
                      stats={progressStats}
                      elapsedTime={elapsedTime}
                    />
                  )}

                  {/* Step List */}
                  <StepSelector
                    steps={STEPS}
                    onRunStep={handleRunStep}
                    customPrompts={customPrompts}
                    onSavePrompt={handleSavePrompt}
                  />

                  {/* Cancel Button */}
                  {isProcessing && (
                    <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
                      <Button
                        variant="contained"
                        onClick={handleCancel}
                        sx={{
                          backgroundColor: '#d32f2f',
                          color: '#fff',
                          '&:hover': { backgroundColor: '#b71c1c' },
                          fontWeight: 600,
                          px: 4,
                          py: 1.5,
                        }}
                      >
                        Cancel Process
                      </Button>
                    </Box>
                  )}
                </CardContent>
              </Card>

              {/* Sheet Preview Card */}
              <Card sx={{ mb: 4, borderRadius: 2, boxShadow: 3 }}>
                <CardContent sx={{ p: 3 }}>
                  <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: '#1a2746', mb: 3 }}>
                    Sheet Preview
                  </Typography>
                  <TablePreview
                    headers={sheetHeaders}
                    rows={sheetRows}
                    priceStepMap={priceStepMap}
                    stepColors={stepColors}
                    previewCount={3}
                  />
                </CardContent>
              </Card>
            </>
          )}
        </Container>
      </Box>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
}

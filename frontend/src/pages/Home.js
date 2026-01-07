import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Typography,
  Button,
  Box,
  Card,
  CardContent,
  Snackbar,
  Alert,
  Chip,
  CircularProgress,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import TablePreview from '../components/TablePreview';
import SheetSelector from '../components/SheetSelector';
import NavigationBar from '../components/NavigationBar';
import StepSelector from '../components/StepSelector';
import InstructionsCard from '../components/InstructionsCard';
import { DEFAULT_PROMPTS } from '../components/PromptEditor';
import { fetchSheetPreview, runProcessStep, saveHistory, cancelProcess } from '../api';
import { useNotificationContext } from '../context/NotificationContext';

const STEPS = [
  { id: 1, name: 'Generate AI Data', color: '#9c27b0' },
  { id: 2, name: 'Build Description', color: '#1a2746' },
  { id: 3, name: 'AI Source Comparables', color: '#ff8200' },
  { id: 4, name: 'Extract price from AI Comparable', color: '#2196f3' },
  { id: 5, name: 'AI Source New Price', color: '#ff9800' },
  { id: 6, name: 'AI Similar Comparable', color: '#e2c69b' },
];

export default function Home() {
  const { notifications, addNotification, markAllAsRead, clearNotifications, markAsRead } = useNotificationContext();
  const [sheetUrl, setSheetUrl] = useState('');
  const [sheetHeaders, setSheetHeaders] = useState([]);
  const [sheetRows, setSheetRows] = useState([]);
  const [sheetName, setSheetName] = useState(null);
  const [priceStepMap, setPriceStepMap] = useState({});
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  // Multiple processes state - each process has its own progress bar
  const [processes, setProcesses] = useState({}); // { processId: { stepName, stats, elapsedTime, isCompleted, isActive, sessionId } }
  const processTimersRef = useRef({}); // { processId: timerId }
  const processAbortControllersRef = useRef({}); // { processId: AbortController }
  const wsConnectionsRef = useRef({}); // { processId: WebSocket }

  const [customPrompts, setCustomPrompts] = useState({});

  // Step colors
  const stepColors = {
    'Extract price from AI Comparable': '#c9daf8',
    'AI Source New Price': '#fff2cc',
    'AI Similar Comparable': '#e2c69b',
  };

  // Timer function for elapsed time
  const startTimer = (processId, startTime) => {
    if (processTimersRef.current[processId]) {
      clearInterval(processTimersRef.current[processId]);
    }

    const timer = setInterval(() => {
      setProcesses(prev => {
        const process = prev[processId];
        if (!process || !process.isActive) {
          clearInterval(timer);
          return prev;
        }
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        return {
          ...prev,
          [processId]: {
            ...process,
            elapsedTime: elapsed,
          },
        };
      });
    }, 100);

    processTimersRef.current[processId] = timer;
  };

  // Connect WebSocket for a specific process
  const connectWebSocket = (processId, sessionId) => {
    const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:9000';
    const wsUrl = API_BASE.replace('http', 'ws') + `/ws/${sessionId}`;

    try {
      const ws = new WebSocket(wsUrl);
      
      // Register message handler FIRST to ensure we catch all messages
      ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log(`📨 Home: WebSocket message received for process ${processId}:`, data);
          console.log(`📨 Home: Message type: ${data.type}, processId: ${processId}`);
          
          if (data.type === 'progress') {
            console.log(`📊 Home: WebSocket progress update for process ${processId}:`, data);
            setProcesses(prev => {
              const process = prev[processId];
              if (!process) {
                console.warn(`⚠️ Home: Process ${processId} not found in state for progress update`);
                return prev;
              }
              
              // Calculate progress
              const total = data.total || process.stats.total;
              const success = data.success ?? 0;
              const skipped = data.skipped ?? 0;
              const processed = data.processed ?? (success || 0);
              
              // Calculate progress: (success + skipped) / total * 100
              const progress = total > 0 
                ? Math.min(100, ((success + skipped) / total) * 100)
                : 0;
              
              console.log(`📊 Home: Updating progress for ${processId}:`, {
                dataReceived: {
                  total: data.total,
                  success: data.success,
                  skipped: data.skipped,
                  processed: data.processed,
                },
                calculated: {
                  total,
                  success,
                  skipped,
                  processed,
                  progress: `${progress.toFixed(1)}%`,
                  progressValue: progress
                },
                currentState: {
                  total: process.stats.total,
                  success: process.stats.success,
                  skipped: process.stats.skipped,
                  processed: process.stats.processed,
                  progress: process.progress
                }
              });
              
              const updatedProcess = {
                ...process,
                stats: {
                  total: total,
                  processed: processed,
                  success: success,
                  errors: data.errors || 0,
                  skipped: skipped,
                  initialEmptyRows: process.stats.initialEmptyRows, // Keep fixed
                },
                progress: progress,
              };
              
              // If progress reaches 100%, set a timeout to mark as completed if complete message doesn't arrive
              // This is a fallback in case the WebSocket closes before receiving the 'complete' message
              if (progress >= 100 && !process.isCompleted) {
                console.log(`⏳ Progress reached 100% for ${processId}, waiting for complete message...`);
                // Clear any existing timeout for this process
                if (process.completionTimeout) {
                  clearTimeout(process.completionTimeout);
                }
                // Set a timeout to auto-complete if complete message doesn't arrive in 5 seconds
                // Increased from 3 to 5 seconds to give more time for the complete message
                const timeoutId = setTimeout(() => {
                  console.log(`⏰ Auto-completing process ${processId} after 100% progress (complete message not received within 5s)`);
                  setProcesses(prev => {
                    const p = prev[processId];
                    if (p && !p.isCompleted && p.progress >= 100) {
                      const completionTime = Date.now();
                      const processStartTime = p.startTime || completionTime;
                      const finalElapsedTime = Math.floor((completionTime - processStartTime) / 1000);
                      
                      // Stop timer
                      if (processTimersRef.current[processId]) {
                        clearInterval(processTimersRef.current[processId]);
                        delete processTimersRef.current[processId];
                      }
                      
                      console.log(`✅ Home: Auto-completed process ${processId} (fallback):`, {
                        isCompleted: true,
                        isActive: false,
                        elapsedTime: finalElapsedTime
                      });
                      
                      return {
                        ...prev,
                        [processId]: {
                          ...p,
                          isActive: false,
                          isCompleted: true,
                          elapsedTime: finalElapsedTime,
                        },
                      };
                    }
                    return prev;
                  });
                }, 5000);
                updatedProcess.completionTimeout = timeoutId;
              }
              
              return {
                ...prev,
                [processId]: updatedProcess,
              };
            });
          } else if (data.type === 'complete') {
            console.log('✅ WebSocket received complete message:', { processId, data });
            console.log('✅ Processing complete message for process:', processId);
            
            // Format time as MM:SS
            const formatTime = (seconds) => {
              const mins = Math.floor(seconds / 60);
              const secs = seconds % 60;
              return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            };

            // Capture the completion time immediately
            const completionTime = Date.now();
            
            setProcesses(prev => {
              const process = prev[processId];
              if (!process) {
                console.warn(`⚠️ Process ${processId} not found in state`);
                return prev;
              }
              
              // Cancel auto-completion timeout if it exists
              if (process.completionTimeout) {
                clearTimeout(process.completionTimeout);
                console.log(`⏰ Cancelled auto-completion timeout for ${processId}`);
              }
              
              // Cancel fallback timeout if it exists
              if (process.fallbackTimeoutId) {
                clearTimeout(process.fallbackTimeoutId);
                console.log(`⏰ Cancelled fallback timeout for ${processId}`);
              }
              
              // Calculate elapsed time using the process's startTime
              const processStartTime = process.startTime || completionTime;
              const finalElapsedTime = Math.floor((completionTime - processStartTime) / 1000);
              const finalSheetName = process.sheetName || sheetName || 'Unknown Sheet';
              
              console.log('📊 Calculating elapsed time for history:', {
                processId,
                startTime: processStartTime,
                completionTime,
                elapsedSeconds: finalElapsedTime,
                formatted: formatTime(finalElapsedTime)
              });
              
              // Stop timer
              if (processTimersRef.current[processId]) {
                clearInterval(processTimersRef.current[processId]);
                delete processTimersRef.current[processId];
              }

              const progress = process.stats.total > 0 
                ? ((data.success + data.skipped) / process.stats.total) * 100 
                : 100;

              const updated = {
                ...prev,
                [processId]: {
                  ...process,
                  isActive: false,
                  isCompleted: true,
                  elapsedTime: finalElapsedTime, // Update elapsedTime with final value
                  stats: {
                    total: data.total || process.stats.total,
                    processed: data.processed || data.success || 0,
                    success: data.success || 0,
                    errors: data.errors || 0,
                    skipped: data.skipped || 0,
                    initialEmptyRows: process.stats.initialEmptyRows,
                  },
                  progress: progress,
                },
              };

              // Note: History is saved by Monitor page when it receives the 'complete' message
              // Home only updates its own state to show "Completed" status
              
              addNotification('success', `Step '${data.step}' completed`, `Processed ${data.success || 0} rows successfully`);
              showSnackbar(`Step '${data.step}' completed successfully!`, 'success');
              
              console.log(`✅ Home: Process ${processId} marked as completed:`, {
                isCompleted: updated[processId].isCompleted,
                isActive: updated[processId].isActive,
                progress: updated[processId].progress
              });
              
              // Force save to localStorage immediately to ensure state persists
              setTimeout(() => {
                localStorage.setItem('homeProcesses', JSON.stringify(updated));
                console.log(`💾 Home: Force-saved completed process ${processId} to localStorage`);
                
                // Dispatch processCompleted event for Monitor to sync
                window.dispatchEvent(new CustomEvent('processCompleted', {
                  detail: {
                    processId,
                    stepName: data.step || process.stepName,
                    sheetName: finalSheetName,
                    stats: {
                      total: data.total || process.stats.total,
                      processed: data.processed || data.success || 0,
                      success: data.success || 0,
                      errors: data.errors || 0,
                      skipped: data.skipped || 0,
                      initialEmptyRows: process.stats.initialEmptyRows,
                    },
                    elapsedTime: finalElapsedTime,
                  }
                }));
                console.log(`📢 Home: Dispatched processCompleted event for ${processId}`);
              }, 0);
              
              return updated;
            });
          } else if (data.type === 'error') {
            setProcesses(prev => {
              const process = prev[processId];
              if (!process) return prev;
              
              // Stop timer
              if (processTimersRef.current[processId]) {
                clearInterval(processTimersRef.current[processId]);
                delete processTimersRef.current[processId];
              }

              addNotification('error', `Step '${data.step}' failed`, data.message || 'An error occurred');
              showSnackbar(`Error: ${data.message}`, 'error');
              
              return {
                ...prev,
                [processId]: {
                  ...process,
                  isActive: false,
                  isCompleted: false,
                },
              };
            });
          }
        } catch (e) {
          console.error(`❌ Home: Error parsing WebSocket message for process ${processId}:`, e);
        }
      };

      ws.onopen = () => {
        console.log(`✅ Home WebSocket connected for process ${processId}, sessionId: ${sessionId}`);
        console.log(`🔗 Home WebSocket URL: ${wsUrl}`);
        console.log(`📡 Home WebSocket readyState: ${ws.readyState} (OPEN=${WebSocket.OPEN})`);
        // Store WebSocket immediately when opened
        wsConnectionsRef.current[processId] = ws;
        console.log(`💾 Home: WebSocket stored in ref for ${processId}`);
      };

      ws.onerror = (error) => {
        console.error(`❌ Home: WebSocket error for process ${processId}:`, error);
      };

      ws.onclose = (event) => {
        console.log(`🔌 Home WebSocket disconnected for process ${processId}`, {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        });
        // Clean up the reference
        if (wsConnectionsRef.current[processId] === ws) {
          delete wsConnectionsRef.current[processId];
          console.log(`🗑️ Home: Removed WebSocket from ref for ${processId}`);
        }
      };

      // Store WebSocket reference immediately (will be updated when opened)
      wsConnectionsRef.current[processId] = ws;
      console.log(`💾 Home: WebSocket reference stored for ${processId} (before open)`);
    } catch (e) {
      console.error(`Failed to create WebSocket for process ${processId}:`, e);
    }
  };

  // Notify Monitor page about new/updated process
  const notifyMonitorPage = (processId, processData) => {
    const monitorData = {
      processId,
      stepName: processData.stepName,
      sessionId: processData.sessionId,
      initialStats: processData.stats,
      sheetName: processData.sheetName, // Include sheetName
    };
    console.log(`📢 Home: Notifying Monitor about process ${processId}:`, {
      stepName: monitorData.stepName,
      sessionId: monitorData.sessionId,
      initialEmptyRows: monitorData.initialStats?.initialEmptyRows,
      total: monitorData.initialStats?.total,
      sheetName: monitorData.sheetName
    });
    localStorage.setItem('newProcess', JSON.stringify(monitorData));
    // Trigger custom event for same-window communication
    window.dispatchEvent(new CustomEvent('newProcess', { detail: monitorData }));
    // Also trigger storage event for other windows
    window.dispatchEvent(new Event('storage'));
  };

  // Load sheet data and processes from localStorage on mount
  useEffect(() => {
    // Load sheet data
    const savedSheetUrl = localStorage.getItem('homeSheetUrl');
    const savedSheetHeaders = localStorage.getItem('homeSheetHeaders');
    const savedSheetRows = localStorage.getItem('homeSheetRows');
    const savedSheetName = localStorage.getItem('homeSheetName');
    
    if (savedSheetUrl) {
      setSheetUrl(savedSheetUrl);
      if (savedSheetHeaders) {
        try {
          const parsedHeaders = JSON.parse(savedSheetHeaders);
          if (parsedHeaders && parsedHeaders.length > 0) {
            setSheetHeaders(parsedHeaders);
          }
        } catch (e) {
          console.error('Error loading sheet headers:', e);
        }
      }
      if (savedSheetRows) {
        try {
          const parsedRows = JSON.parse(savedSheetRows);
          if (parsedRows && parsedRows.length > 0) {
            setSheetRows(parsedRows);
          }
        } catch (e) {
          console.error('Error loading sheet rows:', e);
        }
      }
      if (savedSheetName) {
        setSheetName(savedSheetName);
      }
    }
    
    // Load processes (Home uses 'homeProcesses', Monitor uses 'monitorProcesses')
    const savedProcesses = localStorage.getItem('homeProcesses');
    console.log('🏠 Home: Loading processes from localStorage:', savedProcesses);
    if (savedProcesses) {
      try {
        const parsed = JSON.parse(savedProcesses);
        console.log('🏠 Home: Parsed processes:', parsed);
        console.log('🏠 Home: Number of processes:', Object.keys(parsed).length);
        setProcesses(parsed);
        // Restart timers for active processes
        Object.keys(parsed).forEach(processId => {
          if (parsed[processId].isActive && parsed[processId].startTime) {
            startTimer(processId, parsed[processId].startTime);
          }
          // Reconnect WebSocket if needed
          if (parsed[processId].isActive && parsed[processId].sessionId && !wsConnectionsRef.current[processId]) {
            connectWebSocket(processId, parsed[processId].sessionId);
          }
        });
      } catch (e) {
        console.error('Error loading processes from localStorage:', e);
      }
    } else {
      console.log('🏠 Home: No processes found in localStorage');
    }
  }, []);

  // Save processes to localStorage whenever they change (Home uses 'homeProcesses')
  useEffect(() => {
    if (Object.keys(processes).length > 0) {
      localStorage.setItem('homeProcesses', JSON.stringify(processes));
    } else {
      // Clear localStorage if no processes
      localStorage.removeItem('homeProcesses');
    }
  }, [processes]);

  // Listen for process completion from Monitor page
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'monitorProcesses') {
        try {
          const monitorProcesses = JSON.parse(e.newValue);
          console.log('🔄 Home: Monitor processes updated, syncing completed processes...');
          
          setProcesses(prev => {
            const updated = { ...prev };
            let hasChanges = false;
            
            // Sync completed processes from Monitor to Home
            Object.entries(monitorProcesses).forEach(([processId, monitorProcess]) => {
              if (monitorProcess.isCompleted && prev[processId] && !prev[processId].isCompleted) {
                console.log(`✅ Home: Syncing completed process ${processId} from Monitor`);
                updated[processId] = {
                  ...prev[processId],
                  isCompleted: true,
                  isActive: false,
                  progress: monitorProcess.progress || 100,
                  elapsedTime: monitorProcess.elapsedTime || prev[processId].elapsedTime,
                  stats: {
                    ...prev[processId].stats,
                    ...monitorProcess.stats,
                  },
                };
                hasChanges = true;
                
                // Stop timer if running
                if (processTimersRef.current[processId]) {
                  clearInterval(processTimersRef.current[processId]);
                  delete processTimersRef.current[processId];
                }
              }
            });
            
            if (hasChanges) {
              console.log('💾 Home: Updated processes from Monitor sync');
              // Force save to localStorage
              setTimeout(() => {
                localStorage.setItem('homeProcesses', JSON.stringify(updated));
              }, 0);
            }
            
            return hasChanges ? updated : prev;
          });
        } catch (err) {
          console.error('Error syncing from Monitor:', err);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    
    // Also check periodically for completed processes in Monitor
    const checkInterval = setInterval(() => {
      const monitorProcesses = localStorage.getItem('monitorProcesses');
      if (monitorProcesses) {
        try {
          const parsed = JSON.parse(monitorProcesses);
          setProcesses(prev => {
            const updated = { ...prev };
            let hasChanges = false;
            
            Object.entries(parsed).forEach(([processId, monitorProcess]) => {
              if (monitorProcess.isCompleted && prev[processId] && !prev[processId].isCompleted) {
                console.log(`✅ Home: Periodic sync - marking process ${processId} as completed`);
                updated[processId] = {
                  ...prev[processId],
                  isCompleted: true,
                  isActive: false,
                  progress: monitorProcess.progress || 100,
                  elapsedTime: monitorProcess.elapsedTime || prev[processId].elapsedTime,
                  stats: {
                    ...prev[processId].stats,
                    ...monitorProcess.stats,
                  },
                };
                hasChanges = true;
                
                if (processTimersRef.current[processId]) {
                  clearInterval(processTimersRef.current[processId]);
                  delete processTimersRef.current[processId];
                }
              }
            });
            
            return hasChanges ? updated : prev;
          });
        } catch (err) {
          console.error('Error in periodic sync:', err);
        }
      }
    }, 2000); // Check every 2 seconds

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(checkInterval);
    };
  }, []);


  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Close all WebSocket connections
      Object.values(wsConnectionsRef.current).forEach(ws => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      });

      // Clear all timers
      Object.values(processTimersRef.current).forEach(timer => {
        clearInterval(timer);
      });
    };
  }, []);

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
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
      
      // Save sheet data to localStorage
      localStorage.setItem('homeSheetUrl', url);
      localStorage.setItem('homeSheetHeaders', JSON.stringify(res.data.headers));
      localStorage.setItem('homeSheetRows', JSON.stringify(res.data.rows));
      if (res.data.sheet_name) {
        localStorage.setItem('homeSheetName', res.data.sheet_name);
      }
      
      addNotification('info', 'Sheet loaded', `${res.data.sheet_name || 'Sheet'} loaded with ${res.data.rows.length} rows`);
      
      // Save to history using API
      console.log('💾 Home: Saving sheet load to history...');
      saveHistory(
        res.data.sheet_name || 'Unknown Sheet',
        null, // No step for sheet loading
        `Sheet loaded: ${res.data.sheet_name || 'default tab'} with ${res.data.headers.length} columns and ${res.data.rows.length} rows`,
        new Date().toISOString(),
        new Date().toLocaleTimeString()
      ).then((result) => {
        console.log('✅ Home: Sheet load history saved successfully:', result);
        // Notify History page to refresh
        window.dispatchEvent(new CustomEvent('historyUpdated'));
        console.log('📢 Home: Dispatched historyUpdated event for sheet load');
      }).catch((err) => {
        console.error('Failed to save history to database:', err);
        // Fallback to localStorage if API fails
        const historyItem = {
          sheetName: res.data.sheet_name || 'Unknown Sheet',
          message: `Sheet loaded: ${res.data.sheet_name || 'default tab'} with ${res.data.headers.length} columns and ${res.data.rows.length} rows`,
          timestamp: new Date().toISOString(),
          time: new Date().toLocaleTimeString(),
        };
        const savedHistory = JSON.parse(localStorage.getItem('sheetHistory') || '[]');
        savedHistory.unshift(historyItem);
        localStorage.setItem('sheetHistory', JSON.stringify(savedHistory.slice(0, 100)));
        // Notify History page to refresh
        window.dispatchEvent(new CustomEvent('historyUpdated'));
      });
    } catch (err) {
      addNotification('error', 'Error loading sheet', err.message);
      showSnackbar(`Error loading sheet: ${err.message}`, 'error');
    }
  };

  const handleClearSheet = () => {
    setSheetUrl('');
    setSheetHeaders([]);
    setSheetRows([]);
    setSheetName('');
    
    // Clear from localStorage
    localStorage.removeItem('homeSheetUrl');
    localStorage.removeItem('homeSheetHeaders');
    localStorage.removeItem('homeSheetRows');
    localStorage.removeItem('homeSheetName');
    
    showSnackbar('Sheet cleared', 'info');
  };

  const handleLoadDifferentSheet = () => {
    handleClearSheet();
    // Focus on the sheet input field (will be handled by SheetSelector)
    setTimeout(() => {
      const input = document.querySelector('input[placeholder*="Google Sheet URL"]');
      if (input) {
        input.focus();
      }
    }, 100);
  };

  const handleRunStep = async (stepName, customPrompt = null) => {
    if (!sheetUrl) {
      showSnackbar('Please load a sheet first', 'warning');
      return;
    }

    // Generate unique process ID
    const processId = `process_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Calculate initial empty rows
    let initialEmptyRows = 0;
    if (stepName === "Build Description" && sheetRows.length > 0) {
      const descHeaderIndex = sheetHeaders.findIndex(h => 
        h && h.toLowerCase().includes('script technical description')
      );
      if (descHeaderIndex >= 0) {
        initialEmptyRows = sheetRows.filter(row => {
          const descValue = row[descHeaderIndex];
          return !descValue || !String(descValue).trim();
        }).length;
        console.log(`📊 Home: Calculated initialEmptyRows: ${initialEmptyRows} for step "${stepName}"`);
      } else {
        console.warn(`⚠️ Home: Could not find 'Script Technical Description' column for calculating initialEmptyRows`);
      }
    } else if (stepName === "Generate AI Data" && sheetRows.length > 0) {
      // For Generate AI Data, don't calculate initialEmptyRows from frontend
      // It will be calculated correctly in Monitor.js using backend data (total - skipped)
      // This avoids incorrect counts when sheetRows doesn't have all rows or filtering is wrong
      initialEmptyRows = 0;
      console.log(`📊 Home: Leaving initialEmptyRows as 0 for "${stepName}" - will be calculated from backend data`);
    } else {
      console.log(`📊 Home: Skipping initialEmptyRows calculation (stepName: "${stepName}", sheetRows.length: ${sheetRows.length})`);
    }

    // Create new process
    const initialStats = {
      total: sheetRows.length || 0,
      processed: 0,
      success: 0,
      errors: 0,
      skipped: 0,
      initialEmptyRows: initialEmptyRows,
    };

    const newProcess = {
      stepName,
      sessionId,
      sheetName: sheetName || 'Unknown Sheet', // Store sheetName in process
      stats: initialStats,
      elapsedTime: 0,
      isCompleted: false,
      isActive: true,
      progress: 0,
      startTime: Date.now(),
    };

    // Add process to state FIRST, then connect WebSocket
    setProcesses(prev => ({
      ...prev,
      [processId]: newProcess,
    }));

    // Start timer
    startTimer(processId, newProcess.startTime);

    // Connect WebSocket AFTER state is updated - use setTimeout to ensure state update completes
    setTimeout(() => {
      console.log(`🔌 Home: Connecting WebSocket for process ${processId} with sessionId ${sessionId}`);
      connectWebSocket(processId, sessionId);
    }, 0);

    // Notify Monitor page (but Monitor will manage its own WebSocket independently)
    notifyMonitorPage(processId, newProcess);

    // Create abort controller
    const abortController = new AbortController();
    processAbortControllersRef.current[processId] = abortController;

    addNotification('info', `Step started: ${stepName}`, 'Processing has begun');
    showSnackbar(`Starting ${stepName}...`, 'info');
    
    try {
      const match = sheetUrl.match(/\/d\/([a-zA-Z0-9-_]+)/);
      const sheetId = match ? match[1] : null;
      if (!sheetId) throw new Error('Invalid sheet URL');
      
      const promptToUse = customPrompt || customPrompts[stepName] || DEFAULT_PROMPTS[stepName] || null;

      const res = await runProcessStep(
        sheetId,
        stepName,
        sheetName,
        abortController.signal,
        sessionId,
        promptToUse
      );

      const errors = res.data?.errors || [];
      const filledRows = res.data?.filled_rows || [];
      const stats = res.data?.stats || {};
      
      // Immediately update progress with stats from HTTP response
      // This ensures the UI shows progress even if WebSocket messages don't arrive
      // If the process is complete (all rows processed), mark as completed immediately
      setProcesses(prev => {
        const process = prev[processId];
        if (process && stats.total) {
          const updatedStats = {
            total: stats.total || process.stats.total || 0,
            processed: stats.processed || stats.success || process.stats.processed || 0,
            success: stats.success || stats.processed || process.stats.success || 0,
            errors: stats.errors_count || stats.errors || process.stats.errors || 0,
            skipped: stats.skipped || process.stats.skipped || 0,
            initialEmptyRows: process.stats.initialEmptyRows || 0,
          };
          
          const progress = updatedStats.total > 0 
            ? ((updatedStats.success + updatedStats.skipped) / updatedStats.total) * 100 
            : 100;
          
          // Check if process is complete: if success + skipped + errors >= total, it's done
          // For Generate AI Data and other steps, the process is complete when all rows are processed
          // Also check if processed count equals total (for steps that use "processed" field)
          const totalProcessed = updatedStats.success + updatedStats.skipped + updatedStats.errors;
          const isComplete = updatedStats.total > 0 && 
            (totalProcessed >= updatedStats.total || 
             (updatedStats.processed && updatedStats.processed >= updatedStats.total));
          
          console.log(`📊 Home: Updating progress from HTTP response:`, {
            processId,
            rawStats: stats,
            updatedStats: updatedStats,
            progress,
            isComplete,
            calculation: `${updatedStats.success} + ${updatedStats.skipped} + ${updatedStats.errors} >= ${updatedStats.total} = ${(updatedStats.success + updatedStats.skipped + updatedStats.errors) >= updatedStats.total}`,
            processIsCompleted: process.isCompleted
          });
          
          // If process is complete based on HTTP response, mark it as completed immediately
          // This ensures the UI updates even if WebSocket message doesn't arrive
          if (isComplete && !process.isCompleted) {
            console.log(`✅ Home: Process ${processId} is complete based on HTTP response, marking as completed immediately`);
            const completionTime = Date.now();
            const processStartTime = process.startTime || completionTime;
            const finalElapsedTime = Math.floor((completionTime - processStartTime) / 1000);
            
            // Stop timer
            if (processTimersRef.current[processId]) {
              clearInterval(processTimersRef.current[processId]);
              delete processTimersRef.current[processId];
            }
            
            return {
              ...prev,
              [processId]: {
                ...process,
                isActive: false,
                isCompleted: true,
                elapsedTime: finalElapsedTime,
                stats: updatedStats,
                progress: 100, // Force to 100% when complete
              },
            };
          }
          
          // If complete, mark as completed immediately
          if (isComplete && !process.isCompleted) {
            console.log(`✅ Home: Process ${processId} is complete based on HTTP response stats, marking as completed immediately`);
            const completionTime = Date.now();
            const processStartTime = process.startTime || completionTime;
            const finalElapsedTime = Math.floor((completionTime - processStartTime) / 1000);
            
            // Stop timer
            if (processTimersRef.current[processId]) {
              clearInterval(processTimersRef.current[processId]);
              delete processTimersRef.current[processId];
            }
            
            // Cancel fallback timeout if it exists
            if (process.fallbackTimeoutId) {
              clearTimeout(process.fallbackTimeoutId);
            }
            
            const updated = {
              ...prev,
              [processId]: {
                ...process,
                isActive: false,
                isCompleted: true,
                elapsedTime: finalElapsedTime,
                stats: updatedStats,
                progress: 100,
              },
            };
            
            // Force save to localStorage immediately
            localStorage.setItem('homeProcesses', JSON.stringify(updated));
            console.log(`💾 Home: Force-saved completed process ${processId} to localStorage (HTTP response)`);
            
            // Notify Monitor that process is completed
            window.dispatchEvent(new CustomEvent('processCompleted', {
              detail: {
                processId,
                stats: updatedStats,
                elapsedTime: finalElapsedTime,
                stepName: process.stepName,
                sheetName: process.sheetName,
              }
            }));
            console.log(`📢 Home: Notified Monitor that process ${processId} is completed`);
            
            return updated;
          }
          
          return {
            ...prev,
            [processId]: {
              ...process,
              stats: updatedStats,
              progress: Math.min(progress, 100),
            },
          };
        }
        return prev;
      });
      
      // Fallback: If HTTP request completes successfully but we don't receive 'complete' message
      // within 2 seconds, mark as completed anyway using stats from HTTP response
      // This handles cases where WebSocket closes before receiving the complete message
      const fallbackTimeoutId = setTimeout(() => {
        setProcesses(prev => {
          const process = prev[processId];
          if (process && !process.isCompleted && process.isActive) {
            console.log(`⏰ Home: Fallback - marking process ${processId} as completed after HTTP success (no complete message received within 2s)`);
            const completionTime = Date.now();
            const processStartTime = process.startTime || completionTime;
            const finalElapsedTime = Math.floor((completionTime - processStartTime) / 1000);
            
            // Stop timer
            if (processTimersRef.current[processId]) {
              clearInterval(processTimersRef.current[processId]);
              delete processTimersRef.current[processId];
            }
            
            // Use stats from HTTP response - they are the source of truth
            const finalStats = {
              total: stats.total || process.stats.total || 0,
              processed: stats.processed || stats.success || process.stats.processed || 0,
              success: stats.success || stats.processed || process.stats.success || 0,
              errors: stats.errors_count || stats.errors || process.stats.errors || 0,
              skipped: stats.skipped || process.stats.skipped || 0,
              initialEmptyRows: process.stats.initialEmptyRows || 0,
            };
            
            const updated = {
              ...prev,
              [processId]: {
                ...process,
                isActive: false,
                isCompleted: true,
                elapsedTime: finalElapsedTime,
                stats: finalStats,
                progress: 100,
              },
            };
            
            // Force save to localStorage immediately
            localStorage.setItem('homeProcesses', JSON.stringify(updated));
            console.log(`💾 Home: Force-saved completed process ${processId} to localStorage (fallback) with stats:`, finalStats);
            
            // Notify Monitor that process is completed
            window.dispatchEvent(new CustomEvent('processCompleted', {
              detail: {
                processId,
                stats: finalStats,
                elapsedTime: finalElapsedTime,
                stepName: process.stepName,
                sheetName: process.sheetName,
              }
            }));
            console.log(`📢 Home: Notified Monitor that process ${processId} is completed (fallback)`);
            
            return updated;
          }
          return prev;
        });
      }, 2000); // Wait 2 seconds after HTTP response
      
      // Store timeout ID so we can clear it if complete message arrives
      setProcesses(prev => {
        const process = prev[processId];
        if (process) {
          return {
            ...prev,
            [processId]: {
              ...process,
              fallbackTimeoutId: fallbackTimeoutId,
            },
          };
        }
        return prev;
      });
      
      // Note: History is now saved when WebSocket sends 'complete' message
      // to ensure we capture the elapsed time correctly
      
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
      setProcesses(prev => {
        const process = prev[processId];
        if (!process) return prev;
        
        // Stop timer
        if (processTimersRef.current[processId]) {
          clearInterval(processTimersRef.current[processId]);
          delete processTimersRef.current[processId];
        }

        const errorMsg = err.response?.data?.detail || err.message || 'Unknown error';
        
        if (err.name === 'CanceledError' || err.message === 'canceled') {
          addNotification('info', `Step cancelled: ${stepName}`, 'Process was cancelled by user');
          showSnackbar(`Step '${stepName}' was cancelled`, 'info');
        } else {
          addNotification('error', `Step failed: ${stepName}`, errorMsg);
          showSnackbar(`Error: ${errorMsg}`, 'error');
        }

        return {
          ...prev,
          [processId]: {
            ...process,
            isActive: false,
            isCompleted: false,
          },
        };
      });
    }
  };

  const handleCancelProcess = async (processId) => {
    const abortController = processAbortControllersRef.current[processId];
    if (abortController) {
      abortController.abort();
      delete processAbortControllersRef.current[processId];
    }

    setProcesses(prev => {
      const process = prev[processId];
      if (!process) return prev;

      // Cancel process on backend
      if (process.sessionId) {
        cancelProcess(process.sessionId).catch(err => {
          console.error('Error cancelling process on backend:', err);
        });
      }

      // Stop timer
      if (processTimersRef.current[processId]) {
        clearInterval(processTimersRef.current[processId]);
        delete processTimersRef.current[processId];
      }

      // Close WebSocket
      if (wsConnectionsRef.current[processId]) {
        wsConnectionsRef.current[processId].close();
        delete wsConnectionsRef.current[processId];
      }

      addNotification('info', 'Process cancelled', `Process '${process.stepName}' was cancelled`);
      showSnackbar(`Process '${process.stepName}' was cancelled`, 'info');

      // Remove process completely instead of marking as inactive
      const updated = { ...prev };
      delete updated[processId];
      
      // Update localStorage immediately (Home uses 'homeProcesses')
      if (Object.keys(updated).length > 0) {
        localStorage.setItem('homeProcesses', JSON.stringify(updated));
      } else {
        localStorage.removeItem('homeProcesses');
      }
      
      return updated;
    });
  };

  const handleRemoveProcess = (processId) => {
    setProcesses(prev => {
      const updated = { ...prev };
      delete updated[processId];
      // Update localStorage immediately (Home uses 'homeProcesses', Monitor uses 'monitorProcesses')
      // Note: Removing from Home does NOT remove from Monitor
      if (Object.keys(updated).length > 0) {
        localStorage.setItem('homeProcesses', JSON.stringify(updated));
      } else {
        localStorage.removeItem('homeProcesses');
      }
      
      return updated;
    });

    // Clean up
    if (processTimersRef.current[processId]) {
      clearInterval(processTimersRef.current[processId]);
      delete processTimersRef.current[processId];
    }
    if (wsConnectionsRef.current[processId]) {
      wsConnectionsRef.current[processId].close();
      delete wsConnectionsRef.current[processId];
    }
    if (processAbortControllersRef.current[processId]) {
      delete processAbortControllersRef.current[processId];
    }
  };

  const processList = Object.entries(processes);
  const activeProcesses = processList.filter(([_, process]) => process.isActive);
  const hasActiveProcesses = activeProcesses.length > 0;

  return (
    <>
      <NavigationBar
        notifications={notifications}
        onClearNotifications={clearNotifications}
        onMarkAllRead={markAllAsRead}
        onMarkAsRead={markAsRead}
      />

      <Box sx={{ background: '#f5f5f5', minHeight: '100vh', pt: '80px', pb: 4 }}>
        <Container maxWidth="xl">
          {/* Instructions Card - Always visible for reference */}
          <InstructionsCard />

          {/* Sheet Selection Card */}
          <Card sx={{ mb: 4, borderRadius: 2, boxShadow: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: '#1a2746', mb: 2 }}>
                Connect Google Sheet
              </Typography>
              <Typography variant="body2" sx={{ color: '#666', mb: 3, fontStyle: 'italic' }}>
                {sheetHeaders.length > 0 
                  ? '✓ Sheet loaded successfully. You can now see the available automation steps below.'
                  : 'Once you load a sheet, you will be able to see the available automation steps below.'}
              </Typography>
            <SheetSelector onSheetSelected={handleSheetSelected} />
            </CardContent>
          </Card>

          {/* Current Sheet Info */}
          {sheetName && sheetHeaders.length > 0 && (
            <Card sx={{ mb: 4, borderRadius: 2, boxShadow: 3, backgroundColor: '#f5f5f5' }}>
              <CardContent sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                    <Typography variant="body2" sx={{ color: '#666', fontWeight: 500 }}>
                      Current Sheet:
                    </Typography>
                    <Chip 
                      label={sheetName} 
                      sx={{ 
                        backgroundColor: '#1a2746', 
                        color: 'white',
                        fontWeight: 600,
                        fontSize: '0.875rem'
                      }} 
                    />
                    <Typography variant="body2" sx={{ color: '#666', ml: 1 }}>
                      ({sheetHeaders.length} columns, {sheetRows.length} rows)
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={handleLoadDifferentSheet}
                      sx={{
                        borderColor: '#1a2746',
                        color: '#1a2746',
                        textTransform: 'none',
                        '&:hover': {
                          borderColor: '#2d3f66',
                          backgroundColor: 'rgba(26, 39, 70, 0.04)',
                        },
                      }}
                    >
                      Load Different Sheet
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={handleClearSheet}
                      sx={{
                        borderColor: '#d32f2f',
                        color: '#d32f2f',
                        textTransform: 'none',
                        '&:hover': {
                          borderColor: '#c62828',
                          backgroundColor: 'rgba(211, 47, 47, 0.04)',
                        },
                      }}
                    >
                      Clear Sheet
                    </Button>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Process Steps Section */}
          {sheetHeaders.length > 0 && (
            <>
              <Card sx={{ mb: 4, borderRadius: 2, boxShadow: 3 }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: '#1a2746', mb: 3 }}>
                  Automation Steps
                </Typography>

                  {/* Process Status Indicators - Simple Processing/Completed status */}
                  {processList.length > 0 && (
                    <Box sx={{ mb: 3 }}>
                      {processList.map(([processId, process]) => (
                        <Box key={processId} sx={{ mb: 2, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            {process.isCompleted ? (
                              <>
                                <CheckCircleIcon sx={{ color: '#10b981', fontSize: 24 }} />
                                <Typography variant="body1" sx={{ fontWeight: 600, color: '#1a2746' }}>
                                  {process.stepName} - Completed
                                </Typography>
                              </>
                            ) : (
                              <>
                                <CircularProgress size={20} sx={{ color: '#1e40af' }} />
                                <Typography variant="body1" sx={{ fontWeight: 600, color: '#1a2746' }}>
                                  {process.stepName} - Processing...
                                </Typography>
                              </>
                            )}
                          </Box>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            {!process.isCompleted && (
                              <Button 
                                size="small"
                                variant="outlined"
                                color="error"
                                onClick={() => handleCancelProcess(processId)}
                              >
                                Cancel
                              </Button>
                            )}
                            {process.isCompleted && (
                              <Button 
                                size="small"
                                variant="text"
                                onClick={() => handleRemoveProcess(processId)}
                                sx={{ color: '#999' }}
                              >
                                Remove
                              </Button>
                            )}
                          </Box>
                        </Box>
                      ))}
                    </Box>
                  )}

                  {/* Step List */}
                  <StepSelector
                    steps={STEPS}
                    onRunStep={handleRunStep}
                    customPrompts={customPrompts}
                    onSavePrompt={handleSavePrompt}
                    isProcessing={hasActiveProcesses}
                  />
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

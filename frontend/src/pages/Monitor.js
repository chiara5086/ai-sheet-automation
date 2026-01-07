import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
} from '@mui/material';
import MonitorIcon from '@mui/icons-material/Monitor';
import DetailedProgressMonitor from '../components/DetailedProgressMonitor';
import NavigationBar from '../components/NavigationBar';
import { saveHistory } from '../api';
import { useNotificationContext } from '../context/NotificationContext';

/**
 * Monitor page - Shows detailed progress for all active and completed processes
 * Each process has its own progress bar that persists
 * Uses localStorage and events (not shared database)
 */
export default function Monitor() {
  const { notifications, markAllAsRead, clearNotifications, markAsRead } = useNotificationContext();
  // State for multiple processes
  const [processes, setProcesses] = useState({}); // { processId: { stepName, stats, elapsedTime, isCompleted, isActive, startTime, sessionId, progress, sheetName } }
  const processTimersRef = useRef({}); // { processId: timerId }
  const wsConnectionsRef = useRef({}); // { processId: WebSocket }
  const historySavedRef = useRef({}); // { processId: true } - Track which processes have already saved history

  // Load processes from localStorage on mount (Monitor uses 'monitorProcesses')
  useEffect(() => {
    const savedProcesses = localStorage.getItem('monitorProcesses');
    if (savedProcesses) {
      try {
        const parsed = JSON.parse(savedProcesses);
        console.log('📥 Monitor: Loaded processes from localStorage:', Object.keys(parsed).length);
        
        // Clean up invalid processes (those that are neither active nor completed)
        const cleaned = {};
        Object.entries(parsed).forEach(([processId, process]) => {
          // Only keep processes that are either active or completed
          if (process.isActive || process.isCompleted) {
            cleaned[processId] = process;
          } else {
            console.log(`🧹 Monitor: Removing invalid process ${processId} (neither active nor completed)`);
          }
        });
        
        if (Object.keys(cleaned).length !== Object.keys(parsed).length) {
          console.log(`🧹 Monitor: Cleaned ${Object.keys(parsed).length - Object.keys(cleaned).length} invalid processes`);
          // Update localStorage with cleaned processes
          if (Object.keys(cleaned).length > 0) {
            localStorage.setItem('monitorProcesses', JSON.stringify(cleaned));
          } else {
            localStorage.removeItem('monitorProcesses');
          }
        }
        
        setProcesses(cleaned);
        
        // Restart timers for active processes
        Object.entries(cleaned).forEach(([processId, process]) => {
          if (process.isActive && !process.isCompleted && process.startTime) {
            startTimer(processId, process.startTime);
          }
          // Reconnect WebSocket if needed
          if (process.isActive && process.sessionId && !wsConnectionsRef.current[processId]) {
            connectWebSocket(processId, process.sessionId);
          }
        });
      } catch (e) {
        console.error('Error loading processes from localStorage:', e);
      }
    }
  }, []);

  // Save processes to localStorage whenever they change (Monitor uses 'monitorProcesses')
  useEffect(() => {
    if (Object.keys(processes).length > 0) {
      const toSave = JSON.stringify(processes);
      localStorage.setItem('monitorProcesses', toSave);
      console.log('💾 Monitor: Saved processes to localStorage:', Object.keys(processes).length, 'processes');
    } else {
      localStorage.removeItem('monitorProcesses');
      console.log('💾 Monitor: Removed processes from localStorage');
    }
  }, [processes]);

  // Timer function for elapsed time
  const startTimer = (processId, startTime) => {
    if (processTimersRef.current[processId]) {
      clearInterval(processTimersRef.current[processId]);
    }

    const timer = setInterval(() => {
      setProcesses(prev => {
        const process = prev[processId];
        if (!process || !process.isActive || process.isCompleted) {
          clearInterval(timer);
          delete processTimersRef.current[processId];
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
    }, 1000);

    processTimersRef.current[processId] = timer;
  };

  // Listen for new processes from Home page via custom event and localStorage
  useEffect(() => {
    console.log('👂 Monitor: Setting up event listeners (processCompleted, newProcess, storage)');
    
    // Listen for process completion from Home
    const handleProcessCompleted = (e) => {
      console.log(`📨 Monitor: processCompleted event received:`, e.detail);
      const { processId, stats, elapsedTime, stepName, sheetName } = e.detail || {};
      if (!processId) {
        console.warn('⚠️ Monitor: processCompleted event missing processId');
        return;
      }
      console.log(`🔄 Monitor: Received processCompleted event for ${processId} from Home`);
      
      setProcesses(prev => {
        const process = prev[processId];
        if (!process) {
          console.warn(`⚠️ Monitor: Process ${processId} not found for completion sync`);
          return prev;
        }
        
        if (process.isCompleted) {
          console.log(`⚠️ Monitor: Process ${processId} already marked as completed`);
          return prev;
        }
        
        console.log(`✅ Monitor: Syncing completion from Home for process ${processId}`);
        
        // Stop timer
        if (processTimersRef.current[processId]) {
          clearInterval(processTimersRef.current[processId]);
          delete processTimersRef.current[processId];
        }
        
        // Calculate initialEmptyRows if needed
        let finalInitialEmptyRows = process.stats.initialEmptyRows;
        if (finalInitialEmptyRows === 0) {
          if (stepName === "Build Description" && stats.skipped > 0) {
            finalInitialEmptyRows = stats.total - stats.skipped;
            console.log(`📊 Monitor: Calculated initialEmptyRows for Build Description: ${finalInitialEmptyRows} (total: ${stats.total}, skipped: ${stats.skipped})`);
          } else if (stepName === "AI Source Comparables") {
            // For AI Source Comparables, initialEmptyRows = success (the rows that were filled)
            finalInitialEmptyRows = stats.success || 0;
            console.log(`📊 Monitor: Calculated initialEmptyRows for AI Source Comparables: ${finalInitialEmptyRows} (success: ${stats.success})`);
          } else if (stepName === "Generate AI Data" && stats.skipped > 0) {
            // For Generate AI Data, initialEmptyRows = total - skipped (rows that were already filled)
            finalInitialEmptyRows = stats.total - stats.skipped;
            console.log(`📊 Monitor: Calculated initialEmptyRows for Generate AI Data: ${finalInitialEmptyRows} (total: ${stats.total}, skipped: ${stats.skipped})`);
          }
        }
        
        const updatedProcess = {
          ...process,
          isActive: false,
          isCompleted: true,
          elapsedTime: elapsedTime,
          stats: {
            total: stats.total,
            processed: stats.processed || stats.success || 0,
            success: stats.success || 0,
            errors: stats.errors || 0,
            skipped: stats.skipped || 0,
            initialEmptyRows: finalInitialEmptyRows,
          },
          progress: 100,
        };
        
        // Save to history if not already saved
        if (!historySavedRef.current[processId]) {
          historySavedRef.current[processId] = true;
          setTimeout(() => {
            const formatTime = (seconds) => {
              const mins = Math.floor(seconds / 60);
              const secs = seconds % 60;
              return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            };
            
            saveHistory(
              sheetName || process.sheetName || 'Unknown Sheet',
              stepName || process.stepName,
              `Step '${stepName || process.stepName}' completed in ${formatTime(elapsedTime)}. Filled ${stats.success || 0} row(s).`,
              new Date().toISOString(),
              new Date().toLocaleTimeString()
            ).then((result) => {
              console.log('✅ Monitor: History saved successfully (from Home completion)');
              window.dispatchEvent(new CustomEvent('historyUpdated'));
            }).catch((err) => {
              console.error('❌ Monitor: Failed to save history:', err);
            });
          }, 100);
        }
        
        return {
          ...prev,
          [processId]: updatedProcess,
        };
      });
    };
    
    window.addEventListener('processCompleted', handleProcessCompleted);
    
    const handleStorageChange = (e) => {
      if (e.key === 'newProcess') {
        try {
          const newProcess = JSON.parse(e.newValue);
          addProcess(newProcess);
          localStorage.removeItem('newProcess');
        } catch (err) {
          console.error('Error parsing new process:', err);
        }
      } else if (e.key === 'homeProcesses') {
        // Only sync NEW processes from Home, don't overwrite existing process state
        // Monitor manages its own state via WebSocket, so we don't want to overwrite progress updates
        try {
          const updatedProcesses = JSON.parse(e.newValue);
          setProcesses(prev => {
            const merged = { ...prev };
            // Only add NEW processes, don't update existing ones (they're managed by WebSocket)
            Object.keys(updatedProcesses).forEach(processId => {
              if (!merged[processId]) {
                // New process from Home, add it
                merged[processId] = updatedProcesses[processId];
                // Connect WebSocket and start timer after state update
                setTimeout(() => {
                  if (updatedProcesses[processId].isActive && updatedProcesses[processId].startTime) {
                    startTimer(processId, updatedProcesses[processId].startTime);
                  }
                  if (updatedProcesses[processId].isActive && updatedProcesses[processId].sessionId) {
                    console.log(`🔌 Monitor: Connecting WebSocket for process ${processId} from homeProcesses sync`);
                    connectWebSocket(processId, updatedProcesses[processId].sessionId);
                  }
                }, 0);
              }
              // Note: We intentionally don't update existing processes here
              // Monitor's WebSocket handles all progress updates independently
            });
            return merged;
          });
        } catch (err) {
          console.error('Error syncing new processes from Home:', err);
        }
      }
    };

    const handleCustomEvent = (e) => {
      if (e.detail && e.detail.processId) {
        addProcess(e.detail);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('newProcess', handleCustomEvent);
    window.addEventListener('processCompleted', handleProcessCompleted);
    console.log('✅ Monitor: Event listeners registered');
    
    // Also check localStorage periodically (for same-window communication)
    const checkForNewProcess = setInterval(() => {
      const newProcessData = localStorage.getItem('newProcess');
      if (newProcessData) {
        try {
          const newProcess = JSON.parse(newProcessData);
          addProcess(newProcess);
          localStorage.removeItem('newProcess');
        } catch (err) {
          console.error('Error parsing new process:', err);
        }
      }
      // Also sync homeProcesses for same-window communication
      // This handles both NEW processes and COMPLETION status updates
      const homeProcessesData = localStorage.getItem('homeProcesses');
      if (homeProcessesData) {
        try {
          const updatedProcesses = JSON.parse(homeProcessesData);
          setProcesses(prev => {
            const merged = { ...prev };
            Object.keys(updatedProcesses).forEach(processId => {
              const homeProcess = updatedProcesses[processId];
              const monitorProcess = merged[processId];
              
              if (!monitorProcess) {
                // Add new process from Home
                merged[processId] = homeProcess;
                if (homeProcess.isActive && homeProcess.startTime) {
                  startTimer(processId, homeProcess.startTime);
                }
                if (homeProcess.isActive && homeProcess.sessionId) {
                  connectWebSocket(processId, homeProcess.sessionId);
                }
              } else if (homeProcess.isCompleted && !monitorProcess.isCompleted) {
                // Home says it's completed but Monitor doesn't - sync completion
                console.log(`🔄 Monitor: Syncing completion for ${processId} from homeProcesses (interval check)`);
                
                // Stop timer
                if (processTimersRef.current[processId]) {
                  clearInterval(processTimersRef.current[processId]);
                  delete processTimersRef.current[processId];
                }
                
                // Calculate initialEmptyRows if needed
                let finalInitialEmptyRows = monitorProcess.stats?.initialEmptyRows || 0;
                if (finalInitialEmptyRows === 0) {
                  const stepName = homeProcess.stepName || monitorProcess.stepName;
                  const stats = homeProcess.stats || {};
                  if (stepName === "Build Description" && stats.skipped > 0) {
                    finalInitialEmptyRows = stats.total - stats.skipped;
                    console.log(`📊 Monitor: Calculated initialEmptyRows for Build Description: ${finalInitialEmptyRows}`);
                  } else if (stepName === "AI Source Comparables") {
                    finalInitialEmptyRows = stats.success || 0;
                    console.log(`📊 Monitor: Calculated initialEmptyRows for AI Source Comparables: ${finalInitialEmptyRows}`);
                  } else if (stepName === "Generate AI Data" && stats.skipped > 0) {
                    finalInitialEmptyRows = stats.total - stats.skipped;
                    console.log(`📊 Monitor: Calculated initialEmptyRows for Generate AI Data: ${finalInitialEmptyRows}`);
                  }
                }
                
                merged[processId] = {
                  ...monitorProcess,
                  ...homeProcess,
                  isActive: false,
                  isCompleted: true,
                  stats: {
                    ...homeProcess.stats,
                    initialEmptyRows: finalInitialEmptyRows,
                  },
                  progress: 100,
                };
                
                // Save to history if not already saved
                if (!historySavedRef.current[processId]) {
                  historySavedRef.current[processId] = true;
                  setTimeout(() => {
                    const formatTime = (seconds) => {
                      const mins = Math.floor(seconds / 60);
                      const secs = seconds % 60;
                      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
                    };
                    
                    const sheetNameToSave = homeProcess.sheetName || monitorProcess.sheetName || 'Unknown Sheet';
                    const stepToSave = homeProcess.stepName || monitorProcess.stepName;
                    const successCount = homeProcess.stats?.success || 0;
                    const elapsedTimeToSave = homeProcess.elapsedTime || 0;
                    
                    saveHistory(
                      sheetNameToSave,
                      stepToSave,
                      `Step '${stepToSave}' completed in ${formatTime(elapsedTimeToSave)}. Filled ${successCount} row(s).`,
                      new Date().toISOString(),
                      new Date().toLocaleTimeString()
                    ).then(() => {
                      console.log('✅ Monitor: History saved successfully (from homeProcesses sync)');
                      window.dispatchEvent(new CustomEvent('historyUpdated'));
                    }).catch((err) => {
                      console.error('❌ Monitor: Failed to save history:', err);
                    });
                  }, 100);
                }
              }
            });
            return merged;
          });
        } catch (err) {
          console.error('Error syncing processes from Home:', err);
        }
      }
    }, 500);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('newProcess', handleCustomEvent);
      window.removeEventListener('processCompleted', handleProcessCompleted);
      clearInterval(checkForNewProcess);
    };
  }, []);

  // Add a new process
  const addProcess = (processData) => {
    const { processId, stepName, sessionId, initialStats, sheetName } = processData;
    
    setProcesses(prev => {
      // Only add if process doesn't exist, or if it exists but is completed (allow replacement of completed processes)
      const existingProcess = prev[processId];
      if (existingProcess && existingProcess.isActive && !existingProcess.isCompleted) {
        console.log(`📥 Monitor: Process ${processId} already exists and is active, skipping add to preserve progress`);
        return prev;
      }
      
      // If process exists but is completed, replace it
      if (existingProcess) {
        console.log(`📥 Monitor: Process ${processId} exists but is completed, replacing with new data`);
        // Clean up old WebSocket and timer
        if (wsConnectionsRef.current[processId]) {
          wsConnectionsRef.current[processId].close();
          delete wsConnectionsRef.current[processId];
        }
        if (processTimersRef.current[processId]) {
          clearInterval(processTimersRef.current[processId]);
          delete processTimersRef.current[processId];
        }
      }
      
      // For Generate AI Data and Build Description, wait for backend to calculate skipped before showing empty rows
      // This ensures we show the correct value once, without it changing
      let calculatedInitialEmptyRows = 0;
      
      // Only calculate if we have skipped from backend (indicates backend has calculated it)
      // If skipped is undefined or not yet received, wait for first progress message
      // Don't calculate initialEmptyRows if skipped is 0 and we haven't received confirmation from backend
      // This prevents showing "224 empty rows" initially when it should be "60 empty rows"
      if (initialStats?.total !== undefined && initialStats?.skipped !== undefined) {
        if (stepName === "Build Description" || stepName === "Generate AI Data") {
          // Only calculate if skipped is not 0 OR if we have a non-zero total (meaning backend has calculated it)
          // If skipped is 0 and total is the same as initialEmptyRows would be, wait for backend confirmation
          const calculated = initialStats.total - initialStats.skipped;
          // If skipped is 0 and calculated equals total, this might be a default value, not from backend
          // So we'll wait for the first progress message to confirm
          if (initialStats.skipped === 0 && calculated === initialStats.total) {
            // This is likely a default value, wait for backend
            console.log(`📊 Monitor: Skipped is 0 and would result in emptyRows=total, waiting for backend confirmation (total: ${initialStats.total})`);
            calculatedInitialEmptyRows = 0; // Don't show chip until backend confirms
          } else {
            // Use backend data: initialEmptyRows = total - skipped (rows that were empty at start)
            calculatedInitialEmptyRows = calculated;
            console.log(`📊 Monitor: Using backend data for initialEmptyRows: ${calculatedInitialEmptyRows} (total: ${initialStats.total}, skipped: ${initialStats.skipped})`);
          }
        } else if (stepName === "AI Source Comparables") {
          // For AI Source Comparables, use success count
          if (initialStats.success !== undefined && initialStats.success > 0) {
            calculatedInitialEmptyRows = initialStats.success;
            console.log(`📊 Monitor: Calculated initialEmptyRows for AI Source Comparables from success: ${calculatedInitialEmptyRows}`);
          }
        }
      } else {
        // Wait for first progress message from backend to get correct skipped value
        console.log(`📊 Monitor: Waiting for backend to calculate skipped before showing empty rows (total: ${initialStats?.total || 'unknown'})`);
      }
      
      const newProcess = {
        stepName,
        sessionId,
        sheetName: sheetName || 'Unknown Sheet',
        stats: {
          ...(initialStats || { total: 0, processed: 0, success: 0, errors: 0, skipped: 0, initialEmptyRows: 0 }),
          initialEmptyRows: calculatedInitialEmptyRows, // Use calculated value
        },
        elapsedTime: 0,
        isCompleted: false,
        isActive: true,
        progress: 0,
        startTime: Date.now(),
      };

      console.log(`📥 Monitor: Adding new process ${processId}:`, {
        stepName,
        sheetName: newProcess.sheetName,
        initialEmptyRows: newProcess.stats.initialEmptyRows,
        total: newProcess.stats.total,
        skipped: newProcess.stats.skipped,
        sessionId
      });

      const result = {
        ...prev,
        [processId]: newProcess,
      };
      
      // Connect WebSocket IMMEDIATELY - this is critical to receive all messages
      if (sessionId) {
        console.log(`🔌 Monitor: Connecting WebSocket IMMEDIATELY for process ${processId} with sessionId ${sessionId}`);
        // Connect immediately, don't wait
        connectWebSocket(processId, sessionId);
      } else {
        console.warn(`⚠️ Monitor: No sessionId provided for process ${processId}`);
      }
      
      // Start timer immediately
      startTimer(processId, newProcess.startTime);
      
      return result;
    });
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
          console.log(`📨 Monitor WebSocket message for process ${processId}:`, data);
          console.log(`📨 Monitor: Message type: ${data.type}, processId: ${processId}`);
          
          if (data.type === 'progress') {
            console.log(`📊 Monitor WebSocket progress update for process ${processId}:`, data);
            setProcesses(prev => {
              const process = prev[processId];
              if (!process) {
                console.warn(`⚠️ Monitor: Process ${processId} not found in state for progress update`);
                return prev;
              }
              
              // Calculate progress
              const total = data.total || process.stats.total;
              const success = data.success ?? 0;
              const skipped = data.skipped ?? 0;
              const processed = data.processed ?? (success || 0);
              
              // Update initialEmptyRows when we receive first progress message with skipped from backend
              // This ensures we show the correct value once, without it changing
              let updatedInitialEmptyRows = process.stats.initialEmptyRows;
              if (process.stepName === "Build Description" || process.stepName === "Generate AI Data") {
                // Always update if we have valid skipped value from backend (even if it's 0)
                // The key is: if we haven't received skipped from backend yet, or if it changed
                if (total > 0 && skipped >= 0 && data.skipped !== undefined) {
                  // Check if this is the first time we're getting skipped from backend
                  // We know it's the first time if:
                  // 1. initialEmptyRows is 0 (not set yet), OR
                  // 2. process.stats.skipped is undefined (we haven't received it yet), OR
                  // 3. The skipped value changed (meaning backend just calculated it)
                  const previousSkipped = process.stats.skipped;
                  if (updatedInitialEmptyRows === 0 || previousSkipped === undefined || previousSkipped !== skipped) {
                    updatedInitialEmptyRows = total - skipped;
                    console.log(`📊 Monitor: Set initialEmptyRows from progress message: ${updatedInitialEmptyRows} (total: ${total}, skipped: ${skipped}, previousSkipped: ${previousSkipped})`);
                  } else {
                    // Already set correctly, keep the original value (don't change it)
                    updatedInitialEmptyRows = process.stats.initialEmptyRows;
                  }
                }
              } else if (process.stepName === "AI Source Comparables") {
                // For AI Source Comparables, use success count
                if (updatedInitialEmptyRows === 0 && success > 0) {
                  updatedInitialEmptyRows = success;
                  console.log(`📊 Monitor: Updated initialEmptyRows from progress: ${updatedInitialEmptyRows} (success: ${success})`);
                }
              }
              
              // Calculate progress: based on empty rows being processed, not total rows
              // Progress = (success / emptyRows) * 100 when emptyRows > 0
              let progress = 0;
              if (updatedInitialEmptyRows > 0) {
                progress = Math.min(100, (success / updatedInitialEmptyRows) * 100);
              } else if (total > 0) {
                // Fallback: if emptyRows not calculated yet, use total (but this should be temporary)
                progress = Math.min(100, ((success + skipped) / total) * 100);
              }
              
              console.log(`📊 Monitor: Updating progress for ${processId}:`, {
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
                  initialEmptyRows: updatedInitialEmptyRows, // Update if needed
                },
                progress: progress,
              };
              
              // If progress reaches 100%, set a timeout to mark as completed if complete message doesn't arrive
              if (progress >= 100 && !process.isCompleted) {
                console.log(`⏳ Monitor: Progress reached 100% for ${processId}, waiting for complete message...`);
                // Clear any existing timeout for this process
                if (process.completionTimeout) {
                  clearTimeout(process.completionTimeout);
                }
                // Set a timeout to auto-complete if complete message doesn't arrive in 3 seconds
                const timeoutId = setTimeout(() => {
                  console.log(`⏰ Monitor: Auto-completing process ${processId} after 100% progress (complete message not received)`);
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
                }, 3000);
                updatedProcess.completionTimeout = timeoutId;
              }
              
              const updated = {
                ...prev,
                [processId]: updatedProcess,
              };
              
              console.log(`📊 Monitor: State after update for ${processId}:`, {
                stats: updated[processId].stats,
                progress: updated[processId].progress
              });
              
              return updated;
            });
          } else if (data.type === 'cancelled') {
            console.log(`🚫 Monitor WebSocket received cancelled message for process ${processId}:`, data);
            setProcesses(prev => {
              const process = prev[processId];
              if (!process) {
                console.warn(`⚠️ Monitor: Process ${processId} not found in state for cancelled message`);
                return prev;
              }
              
              // Cancel auto-completion timeout if it exists
              if (process.completionTimeout) {
                clearTimeout(process.completionTimeout);
                console.log(`⏰ Monitor: Cancelled auto-completion timeout for ${processId}`);
              }
              
              // Stop timer
              if (processTimersRef.current[processId]) {
                clearInterval(processTimersRef.current[processId]);
                delete processTimersRef.current[processId];
              }

              // Update initialEmptyRows with backend data if available
              const total = data.total || process.stats.total;
              const skipped = data.skipped !== undefined ? data.skipped : process.stats.skipped;
              let finalInitialEmptyRows = process.stats.initialEmptyRows;
              if (process.stepName === "Build Description" || process.stepName === "Generate AI Data") {
                if (total > 0 && skipped >= 0 && skipped !== undefined) {
                  finalInitialEmptyRows = total - skipped;
                  console.log(`📊 Monitor: Updated initialEmptyRows in cancelled handler: ${finalInitialEmptyRows} (total: ${total}, skipped: ${skipped})`);
                }
              }

              const updatedProcess = {
                ...process,
                isActive: false,
                isCompleted: false,
                isCancelled: true,
                stats: {
                  ...process.stats,
                  total: total,
                  processed: data.processed || process.stats.processed,
                  success: data.success !== undefined ? data.success : process.stats.success,
                  errors: data.errors !== undefined ? data.errors : process.stats.errors,
                  skipped: skipped !== undefined ? skipped : process.stats.skipped,
                  initialEmptyRows: finalInitialEmptyRows,
                },
              };

              console.log(`🚫 Monitor: Process ${processId} marked as cancelled:`, {
                isCancelled: updatedProcess.isCancelled,
                isActive: updatedProcess.isActive,
                isCompleted: updatedProcess.isCompleted,
                initialEmptyRows: updatedProcess.stats.initialEmptyRows
              });

              return {
                ...prev,
                [processId]: updatedProcess,
              };
            });
          } else if (data.type === 'complete') {
            console.log(`✅ Monitor WebSocket received complete message for process ${processId}:`, data);
            setProcesses(prev => {
              const process = prev[processId];
              if (!process) {
                console.warn(`⚠️ Monitor: Process ${processId} not found in state for complete message`);
                return prev;
              }
              
              // Cancel auto-completion timeout if it exists
              if (process.completionTimeout) {
                clearTimeout(process.completionTimeout);
                console.log(`⏰ Monitor: Cancelled auto-completion timeout for ${processId}`);
              }
              
              // Stop timer
              if (processTimersRef.current[processId]) {
                clearInterval(processTimersRef.current[processId]);
                delete processTimersRef.current[processId];
              }

              // Calculate final progress - should be 100% when completed
              const total = data.total || process.stats.total;
              const success = data.success || 0;
              const skipped = data.skipped || 0;
              const finalElapsedTime = Math.floor((Date.now() - process.startTime) / 1000);

              console.log(`✅ Monitor: Marking process ${processId} as completed:`, {
                total,
                success,
                skipped,
                elapsedTime: finalElapsedTime
              });

              // Update initialEmptyRows with backend data (always update for Generate AI Data to get accurate count)
              let finalInitialEmptyRows = process.stats.initialEmptyRows;
              if (process.stepName === "Build Description" || process.stepName === "Generate AI Data") {
                if (total > 0 && skipped >= 0) {
                  // Use backend data: initialEmptyRows = total - skipped (rows that were empty at start)
                  finalInitialEmptyRows = total - skipped;
                  console.log(`📊 Monitor: Updated initialEmptyRows in complete handler: ${finalInitialEmptyRows} (total: ${total}, skipped: ${skipped})`);
                }
              } else if (process.stepName === "AI Source Comparables") {
                if (finalInitialEmptyRows === 0 && success > 0) {
                  finalInitialEmptyRows = success;
                  console.log(`📊 Monitor: Updated initialEmptyRows in complete handler: ${finalInitialEmptyRows} (success: ${success})`);
                }
              }

              const updatedProcess = {
                ...process,
                isActive: false,
                isCompleted: true,
                elapsedTime: finalElapsedTime,
                stats: {
                  total: total,
                  processed: data.processed || data.success || 0,
                  success: success,
                  errors: data.errors || 0,
                  skipped: skipped,
                  initialEmptyRows: finalInitialEmptyRows, // Use updated value
                },
                progress: 100, // Always 100% when completed
              };

              console.log(`✅ Monitor: Process ${processId} marked as completed with stats:`, {
                isCompleted: updatedProcess.isCompleted,
                isActive: updatedProcess.isActive,
                progress: updatedProcess.progress,
                initialEmptyRows: updatedProcess.stats.initialEmptyRows
              });

              // Save to history immediately with the calculated elapsed time
              // Only save once per process (avoid duplicates if handler runs multiple times)
              if (!historySavedRef.current[processId]) {
                historySavedRef.current[processId] = true;
                console.log(`💾 Monitor: Marking process ${processId} as history-saved to prevent duplicates`);
                
                // Use setTimeout to ensure state update completes first
                setTimeout(() => {
                  const formatTime = (seconds) => {
                    const mins = Math.floor(seconds / 60);
                    const secs = seconds % 60;
                    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
                  };

                  const sheetNameToSave = process.sheetName || 'Unknown Sheet';
                  const stepToSave = data.step || process.stepName;
                  const successCount = success;
                  const elapsedTimeToSave = finalElapsedTime;
                  
                  console.log('🔄 Monitor: Saving history with elapsed time:', {
                    sheetNameToSave,
                    stepToSave,
                    successCount,
                    elapsedTimeToSave,
                    formatted: formatTime(elapsedTimeToSave)
                  });
                  
                  // Save history asynchronously
                  saveHistory(
                    sheetNameToSave,
                    stepToSave,
                    `Step '${stepToSave}' completed in ${formatTime(elapsedTimeToSave)}. Filled ${successCount} row(s).`,
                    new Date().toISOString(),
                    new Date().toLocaleTimeString()
                  ).then((result) => {
                    console.log('✅ Monitor: History saved successfully to database:', result);
                    // Notify History page to refresh
                    window.dispatchEvent(new CustomEvent('historyUpdated'));
                    console.log('📢 Monitor: Dispatched historyUpdated event');
                  }).catch((err) => {
                    console.error('❌ Monitor: Failed to save history to database:', err);
                    console.error('Error details:', err.response?.data || err.message);
                    // Fallback to localStorage if API fails
                    const historyItem = {
                      sheetName: sheetNameToSave,
                      step: stepToSave,
                      message: `Step '${stepToSave}' completed in ${formatTime(elapsedTimeToSave)}. Filled ${successCount} row(s).`,
                      timestamp: new Date().toISOString(),
                      time: new Date().toLocaleTimeString(),
                    };
                    const savedHistory = JSON.parse(localStorage.getItem('sheetHistory') || '[]');
                    savedHistory.unshift(historyItem);
                    localStorage.setItem('sheetHistory', JSON.stringify(savedHistory.slice(0, 100)));
                    console.log('💾 Monitor: History saved to localStorage as fallback');
                    // Notify History page to refresh
                    window.dispatchEvent(new CustomEvent('historyUpdated'));
                    console.log('📢 Monitor: Dispatched historyUpdated event (localStorage)');
                  });
                }, 100);
              } else {
                console.log(`⚠️ Monitor: History already saved for process ${processId}, skipping duplicate save`);
              }

              return {
                ...prev,
                [processId]: updatedProcess,
              };
            });
          } else if (data.type === 'error') {
            console.error(`❌ Monitor WebSocket received error message for process ${processId}`);
            setProcesses(prev => {
              const process = prev[processId];
              if (!process) return prev;
              
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
                  isCompleted: false,
                },
              };
            });
          }
        } catch (e) {
          console.error(`❌ Monitor: Error parsing WebSocket message for process ${processId}:`, e);
        }
      };

      ws.onopen = () => {
        console.log(`✅ Monitor WebSocket connected for process ${processId}, sessionId: ${sessionId}`);
        console.log(`🔗 Monitor WebSocket URL: ${wsUrl}`);
        console.log(`📡 Monitor WebSocket readyState: ${ws.readyState} (OPEN=${WebSocket.OPEN})`);
        // Store WebSocket immediately when opened
        wsConnectionsRef.current[processId] = ws;
        console.log(`💾 Monitor: WebSocket stored in ref for ${processId}`);
      };

      ws.onerror = (error) => {
        console.error(`❌ Monitor: WebSocket error for process ${processId}:`, error);
      };

      ws.onclose = (event) => {
        console.log(`🔌 Monitor WebSocket disconnected for process ${processId}`, {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        });
        // Clean up the reference
        if (wsConnectionsRef.current[processId] === ws) {
          delete wsConnectionsRef.current[processId];
          console.log(`🗑️ Monitor: Removed WebSocket from ref for ${processId}`);
        }
      };

      // Store WebSocket reference immediately (will be updated when opened)
      wsConnectionsRef.current[processId] = ws;
      console.log(`💾 Monitor: WebSocket reference stored for ${processId} (before open)`);
    } catch (e) {
      console.error(`Failed to create Monitor WebSocket for process ${processId}:`, e);
    }
  };

  // Mark a process as completed manually (if it's stuck)
  const handleMarkAsCompleted = (processId) => {
    setProcesses(prev => {
      const process = prev[processId];
      if (!process) return prev;
      
      const updated = {
        ...prev,
        [processId]: {
          ...process,
          isActive: false,
          isCompleted: true,
          progress: 100,
          elapsedTime: process.startTime ? Math.floor((Date.now() - process.startTime) / 1000) : process.elapsedTime,
        },
      };
      
      // Update localStorage (Monitor uses 'monitorProcesses')
      localStorage.setItem('monitorProcesses', JSON.stringify(updated));
      
      return updated;
    });
    
    // Stop timer
    if (processTimersRef.current[processId]) {
      clearInterval(processTimersRef.current[processId]);
      delete processTimersRef.current[processId];
    }
  };

  // Remove a completed process
  const handleRemoveProcess = (processId) => {
    setProcesses(prev => {
      const updated = { ...prev };
      delete updated[processId];
      // Update localStorage immediately (Monitor uses 'monitorProcesses')
      if (Object.keys(updated).length > 0) {
        localStorage.setItem('monitorProcesses', JSON.stringify(updated));
      } else {
        localStorage.removeItem('monitorProcesses');
      }
      return updated;
    });

    // Clean up WebSocket
    if (wsConnectionsRef.current[processId]) {
      wsConnectionsRef.current[processId].close();
      delete wsConnectionsRef.current[processId];
    }

    // Clean up timer
    if (processTimersRef.current[processId]) {
      clearInterval(processTimersRef.current[processId]);
      delete processTimersRef.current[processId];
    }
  };

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

  const processList = Object.entries(processes);

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
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
            <MonitorIcon sx={{ color: '#1a2746', fontSize: 36 }} />
            <Typography variant="h4" sx={{ fontWeight: 700, color: '#1a2746', fontSize: '2rem', lineHeight: 1.2 }}>
              Process Monitor
            </Typography>
          </Box>

          {processList.length === 0 ? (
            <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <MonitorIcon sx={{ fontSize: 64, color: '#ccc', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  No active processes
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Start a process from the Home page to see detailed progress here
                </Typography>
              </CardContent>
            </Card>
          ) : (
            <>
              <Typography variant="h6" sx={{ mb: 3, fontWeight: 600, color: '#1a2746' }}>
                Active and Completed Processes ({processList.length})
              </Typography>
              {processList.map(([processId, process]) => (
                <DetailedProgressMonitor
                  key={processId}
                  processId={processId}
                  stepName={process.stepName || 'Unknown Step'}
                  sheetName={process.sheetName}
                  stats={process.stats || {}}
                  elapsedTime={process.elapsedTime || 0}
                  isCompleted={Boolean(process.isCompleted)}
                  isActive={Boolean(process.isActive)}
                  isCancelled={Boolean(process.isCancelled)}
                  onRemove={handleRemoveProcess}
                  onMarkAsCompleted={handleMarkAsCompleted}
                  progress={process.progress || 0}
                />
              ))}
            </>
          )}
        </Container>
      </Box>
    </>
  );
}

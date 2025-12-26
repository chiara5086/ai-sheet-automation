import React, { useState, useEffect, useRef } from 'react';
import { Container, Typography, Paper, Button, Stack, Box, AppBar, Toolbar, Card, CardContent, Grid } from '@mui/material';
import TablePreview from '../components/TablePreview';
import SheetSelector from '../components/SheetSelector';
import ProcessStepper from '../components/ProcessStepper';
import ProgressBar from '../components/ProgressBar';
import HistoryPanel from '../components/HistoryPanel';
import { fetchSheetPreview } from '../api';

export default function Home() {
  const [sheetUrl, setSheetUrl] = useState('');
  const [sheetHeaders, setSheetHeaders] = useState([]);
  const [sheetRows, setSheetRows] = useState([]);
  const [sheetName, setSheetName] = useState(null); // Store detected sheet name
  const [activeStep, setActiveStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [history, setHistory] = useState([]);
  const [elapsedTime, setElapsedTime] = useState(0); // Time in seconds
  const timerRef = useRef(null);
  const startTimeRef = useRef(null);
  const abortControllerRef = useRef(null);

  const handleSheetSelected = async (url) => {
    setSheetUrl(url);
    setHistory((h) => [
      `Loaded sheet: ${url}`,
      ...h
    ]);
    try {
      const res = await fetchSheetPreview(url);
      setSheetHeaders(res.data.headers);
      setSheetRows(res.data.rows);
      if (res.data.sheet_name) {
        setSheetName(res.data.sheet_name);
      }
      setHistory((h) => [
        `Sheet loaded: ${res.data.sheet_name || 'default tab'} with ${res.data.headers.length} columns and ${res.data.rows.length} rows`,
        ...h
      ]);
    } catch (err) {
      setHistory((h) => [
        `Error loading sheet: ${err.message}`,
        ...h
      ]);
    }
  };

  // Handler for running a process step
  // Track which rows were filled by which step for coloring (row index -> step name)
  const [priceStepMap, setPriceStepMap] = useState({});

  // Step color mapping for Price cell coloring
  const stepColors = {
    'Extract price from AI Comparable': '#c9daf8', // light blue
    'AI Source New Price': '#fff2cc', // light yellow
    'AI Similar Comparable': '#e2c69b', // light orange
  };

  // Timer effect: update elapsed time while processing
  useEffect(() => {
    if (progress > 0 && progress < 100) {
      if (!timerRef.current) {
        startTimeRef.current = Date.now();
        timerRef.current = setInterval(() => {
          if (startTimeRef.current) {
            const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
            setElapsedTime(elapsed);
          }
        }, 100); // Update every 100ms for smooth display
      }
    } else {
      // Stop timer when progress is 0 or 100
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      if (progress === 0) {
        setElapsedTime(0);
        startTimeRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [progress]);

  // Format time as MM:SS
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle cancellation
  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setProgress(0);
      setElapsedTime(0);
      startTimeRef.current = null;
      abortControllerRef.current = null;
      setHistory((h) => [
        'Process cancelled by user.',
        ...h
      ]);
    }
  };

  const handleRunStep = async (stepName) => {
    setHistory((h) => [
      `Running step: ${stepName}`,
      ...h
    ]);
    setProgress(10);
    setElapsedTime(0);
    startTimeRef.current = Date.now();
    
    // Create new AbortController for this request
    abortControllerRef.current = new AbortController();
    
    try {
      const match = sheetUrl.match(/\/d\/([a-zA-Z0-9-_]+)/);
      const sheetId = match ? match[1] : null;
      if (!sheetId) throw new Error('Invalid sheet URL');
      
      console.log('DEBUG: Calling API with:', { sheetId, stepName, sheetName });
      console.log('DEBUG: API Base URL:', process.env.REACT_APP_API_BASE || 'http://localhost:9000');
      
      const res = await import('../api').then(api => api.runProcessStep(sheetId, stepName, sheetName, abortControllerRef.current?.signal));
      console.log('DEBUG: API Response received:', res);
      setProgress(100);
      
      // Calculate final elapsed time
      if (startTimeRef.current) {
        const finalTime = Math.floor((Date.now() - startTimeRef.current) / 1000);
        setElapsedTime(finalTime);
      }
      
      // Parse response
      const errors = res.data?.errors || [];
      const filledRows = res.data?.filled_rows || [];
      const emptyRows = res.data?.empty_price_rows || [];
      const stats = res.data?.stats || {};
      
      // Filter out expected "missing data" errors (these are just informational)
      const realErrors = errors.filter(err => 
        !err.includes('Missing asset, technical specs, or comparable listings') &&
        !err.includes('Row ')  // Filter out individual row errors, only show critical errors
      );
      
      // Build clean success message with detailed stats
      const finalTime = startTimeRef.current ? Math.floor((Date.now() - startTimeRef.current) / 1000) : elapsedTime;
      let successMsg = `Step '${stepName}' completed in ${formatTime(finalTime)}.`;
      
      // Add detailed stats if available (only for price-related steps)
      const isPriceStep = stepName.includes('Price') || stepName.includes('Comparable');
      const isDescriptionStep = stepName === 'Build Description';
      
      if (stats.empty_before !== undefined && isPriceStep) {
        successMsg += ` Found ${stats.empty_before} empty row(s).`;
        if (stats.filled > 0) {
          successMsg += ` Filled ${stats.filled} price(s).`;
        } else {
          // More detailed message when no prices filled
          if (stats.empty_before === 0) {
            successMsg += ` No empty rows found to process.`;
          } else if (stats.errors_count > 0) {
            successMsg += ` No prices filled (${stats.errors_count} error(s) encountered).`;
          } else {
            successMsg += ` No prices found/filled (API may not have found prices for these assets).`;
          }
        }
        if (stats.empty_after > 0) {
          successMsg += ` ${stats.empty_after} row(s) still empty.`;
        }
      } else if (isDescriptionStep) {
        // For Build Description, show description-related stats
        const errorCount = errors.length;
        if (errorCount === 0) {
          successMsg += ` Descriptions generated successfully.`;
        } else {
          successMsg += ` ${errorCount} error(s) encountered.`;
        }
      } else if (!isPriceStep && !isDescriptionStep) {
        // For other steps (like AI Source Comparables)
        if (filledRows && filledRows.length > 0) {
          successMsg += ` ${filledRows.length} row(s) updated.`;
        } else if (errors.length > 0) {
          successMsg += ` ${errors.length} error(s) encountered.`;
        }
      } else {
        // Fallback to simple stats for price steps
        if (filledRows && filledRows.length > 0) {
          successMsg += ` ${filledRows.length} price(s) filled.`;
        } else if (!isDescriptionStep) {
          successMsg += ` No prices filled.`;
        }
        if (emptyRows && emptyRows.length > 0 && isPriceStep) {
          successMsg += ` ${emptyRows.length} row(s) still empty.`;
        }
      }
      
      if (realErrors.length > 0) {
        // Only show critical errors (not individual row errors)
        successMsg += ` ${realErrors.length} critical error(s).`;
        // Add critical errors to history (but only critical ones, not per-row)
        realErrors.forEach(err => {
          if (!err.includes('Row ')) {  // Only add non-row-specific errors
            setHistory((h) => [`⚠️ ${err}`, ...h]);
          }
        });
      }
      
      setHistory((h) => [successMsg, ...h]);
      
      // Update price step map
      if (filledRows && filledRows.length > 0) {
        setPriceStepMap((prev) => {
          const updated = { ...prev };
          filledRows.forEach(rowIdx => {
            updated[rowIdx] = stepName;
          });
          return updated;
        });
      }
      
      // Refresh sheet data to show updates
      if (sheetUrl) {
        const res = await fetchSheetPreview(sheetUrl);
        setSheetRows(res.data.rows);
      }
    } catch (err) {
      // Check if error was due to cancellation
      if (err.name === 'CanceledError' || err.message === 'canceled' || (err.code === 'ERR_CANCELED')) {
        setHistory((h) => [
          `Step '${stepName}' was cancelled by user.`,
          ...h
        ]);
      } else {
        const errorMsg = err.response?.data?.detail || err.message || 'Unknown error';
        console.error('DEBUG: Error details:', err);
        console.error('DEBUG: Error response:', err.response);
        setHistory((h) => [
          `Error running step '${stepName}': ${errorMsg}`,
          ...h
        ]);
      }
      setProgress(0);
      setElapsedTime(0);
      startTimeRef.current = null;
      abortControllerRef.current = null;
    }
  };

  return (
    <>
      {/* Header Navigation Bar - Aucto Style */}
      <AppBar position="static" sx={{ backgroundColor: '#1a2746', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', borderRadius: 0 }}>
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Typography variant="h5" component="div" sx={{ fontWeight: 700, color: '#ffffff' }}>
              AI Sheet Automation
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ color: '#ffffff', opacity: 0.9 }}>
              Google Sheets Automation Tool
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box sx={{ background: '#ffffff', minHeight: 'calc(100vh - 64px)', py: 4 }}>
        <Container maxWidth="xl">
          {/* Sheet Selection Card */}
          <Card sx={{ mb: 4, borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
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
              <Card sx={{ mb: 4, borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
                <CardContent sx={{ p: 3 }}>
                  <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: '#1a2746', mb: 3 }}>
                    Automation Steps
                  </Typography>
            <ProcessStepper activeStep={activeStep} />
                  
                  {/* Step Action Buttons */}
                  <Grid container spacing={2} sx={{ mt: 3 }}>
                    <Grid item xs={12} sm={6} md={4}>
                      <Button 
                        variant="contained" 
                        color="primary" 
                        fullWidth
                        sx={{ py: 1.5, fontWeight: 600 }}
                        onClick={() => handleRunStep('Build Description')}
                      >
                        Build Description
                      </Button>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Button 
                        variant="contained" 
                        color="secondary" 
                        fullWidth
                        sx={{ py: 1.5, fontWeight: 600 }}
                        onClick={() => handleRunStep('AI Source Comparables')}
                      >
                        AI Source Comparables
                      </Button>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Button 
                        variant="contained" 
                        sx={{ 
                          py: 1.5, 
                          fontWeight: 600,
                          backgroundColor: '#1a2746',
                          '&:hover': { backgroundColor: '#2d3f66' }
                        }}
                        fullWidth
                        onClick={() => handleRunStep('Extract price from AI Comparable')}
                      >
                        Extract Price from AI Comparable
                      </Button>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Button 
                        variant="contained" 
                        sx={{ 
                          py: 1.5, 
                          fontWeight: 600,
                          backgroundColor: '#ff8200',
                          '&:hover': { backgroundColor: '#ffa033' }
                        }}
                        fullWidth
                        onClick={() => handleRunStep('AI Source New Price')}
                      >
                        AI Source New Price
                      </Button>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Button 
                        variant="contained" 
                        sx={{ 
                          py: 1.5, 
                          fontWeight: 600,
                          backgroundColor: '#e2c69b',
                          color: '#1a2746',
                          '&:hover': { backgroundColor: '#d6b48a' }
                        }}
                        fullWidth
                        onClick={() => handleRunStep('AI Similar Comparable')}
                      >
                        AI Similar Comparable
                      </Button>
                    </Grid>
                  </Grid>

                  {/* Progress Bar */}
                  {progress > 0 && (
                    <Box sx={{ mt: 3 }}>
                      <ProgressBar value={progress} label={`Processing: ${progress}%`} />
                      <Typography variant="body2" sx={{ mt: 1, textAlign: 'center', color: '#666' }}>
                        Elapsed time: {formatTime(elapsedTime)}
                      </Typography>
                      {progress < 100 && (
                        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
                          <Button
                            variant="contained"
                            onClick={handleCancel}
                            sx={{
                              backgroundColor: '#d32f2f',
                              color: '#fff',
                              '&:hover': {
                                backgroundColor: '#b71c1c',
                              },
                              fontWeight: 600,
                              px: 3,
                            }}
                          >
                            Cancel Process
                          </Button>
                        </Box>
                      )}
                    </Box>
                  )}
                </CardContent>
              </Card>

              {/* Sheet Preview Card */}
              <Card sx={{ mb: 4, borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
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

          {/* History Panel Card */}
          <Card sx={{ borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
            <CardContent sx={{ p: 3 }}>
            <HistoryPanel history={history} />
            </CardContent>
          </Card>
        </Container>
      </Box>
    </>
  );
}

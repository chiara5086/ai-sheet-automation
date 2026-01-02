import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  List,
  ListItem,
  ListItemText,
  Chip,
  Card,
  CardContent,
  Divider,
} from '@mui/material';
import NavigationBar from '../components/NavigationBar';
import HistoryIcon from '@mui/icons-material/History';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';
import RefreshIcon from '@mui/icons-material/Refresh';
import { IconButton, CircularProgress } from '@mui/material';
import { getHistoryGrouped } from '../api';

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null); // Clear any previous errors
      console.log('📥 History page: Loading history from API...');
      const response = await getHistoryGrouped();
      console.log('📥 History page: API response received:', response);
      
      if (response.status === 'ok' && response.history) {
        // Convert grouped history to flat list for compatibility
        const flatHistory = [];
        for (const [sheetName, items] of Object.entries(response.history)) {
          items.forEach(item => {
            flatHistory.push({
              ...item,
              sheetName: item.sheet_name || sheetName, // Use sheet_name from DB or fallback
            });
          });
        }
        // Sort by timestamp descending
        flatHistory.sort((a, b) => {
          const timeA = a.timestamp || a.created_at || '';
          const timeB = b.timestamp || b.created_at || '';
          return timeB.localeCompare(timeA);
        });
        console.log('📥 History page: Setting history with', flatHistory.length, 'items');
        setHistory(flatHistory);
      } else {
        console.warn('📥 History page: API response not ok or history missing, falling back to localStorage');
        // Fallback to localStorage if API fails
        const savedHistory = localStorage.getItem('sheetHistory');
        if (savedHistory) {
          try {
            const parsed = JSON.parse(savedHistory);
            console.log('📥 History page: Loaded', parsed.length, 'items from localStorage');
            setHistory(parsed);
          } catch (e) {
            console.error('Error loading history from localStorage:', e);
            setHistory([]);
          }
        } else {
          setHistory([]);
        }
      }
    } catch (err) {
      console.error('❌ History page: Error loading history from API:', err);
      setError(err.message);
      // Fallback to localStorage if API fails
      const savedHistory = localStorage.getItem('sheetHistory');
      if (savedHistory) {
        try {
          const parsed = JSON.parse(savedHistory);
          console.log('📥 History page: Loaded', parsed.length, 'items from localStorage (fallback)');
          setHistory(parsed);
        } catch (e) {
          console.error('Error loading history from localStorage:', e);
          setHistory([]);
        }
      } else {
        setHistory([]);
      }
    } finally {
      setLoading(false);
      console.log('📥 History page: Loading complete');
    }
  };

  useEffect(() => {
    // Load history from API on mount
    loadHistory();

    // Listen for custom event when history is updated
    // Use a debounce to avoid multiple rapid reloads
    let reloadTimeout = null;
    const handleHistoryUpdate = () => {
      console.log('📥 History page received historyUpdated event, refreshing...');
      // Debounce: only reload if no other update comes within 500ms
      if (reloadTimeout) {
        clearTimeout(reloadTimeout);
      }
      reloadTimeout = setTimeout(() => {
        loadHistory();
      }, 500);
    };
    window.addEventListener('historyUpdated', handleHistoryUpdate);
    console.log('👂 History page listening for historyUpdated events');

    // Also listen for storage events (from localStorage fallback)
    const handleStorageChange = (e) => {
      if (e.key === 'sheetHistory') {
        // Debounce storage events too
        if (reloadTimeout) {
          clearTimeout(reloadTimeout);
        }
        reloadTimeout = setTimeout(() => {
          loadHistory();
        }, 500);
      }
    };
    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('historyUpdated', handleHistoryUpdate);
      window.removeEventListener('storage', handleStorageChange);
      if (reloadTimeout) {
        clearTimeout(reloadTimeout);
      }
    };
  }, []);

  const getHistoryIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircleIcon sx={{ color: '#4caf50', fontSize: 20 }} />;
      case 'error':
        return <ErrorIcon sx={{ color: '#f44336', fontSize: 20 }} />;
      default:
        return <InfoIcon sx={{ color: '#2196f3', fontSize: 20 }} />;
    }
  };

  const getHistoryType = (item) => {
    if (item.toLowerCase().includes('error') || item.toLowerCase().includes('failed')) {
      return 'error';
    }
    if (item.toLowerCase().includes('completed') || item.toLowerCase().includes('success')) {
      return 'success';
    }
    return 'info';
  };

  // Group history by sheet
  const groupedHistory = history.reduce((acc, item) => {
    const sheetName = item.sheetName || item.sheet_name || 'Unknown Sheet';
    if (!acc[sheetName]) {
      acc[sheetName] = [];
    }
    acc[sheetName].push(item);
    return acc;
  }, {});

  return (
    <>
      <NavigationBar />
      <Box sx={{ background: '#f5f5f5', minHeight: '100vh', pt: '80px', pb: 4 }}>
        <Container maxWidth="xl">
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <HistoryIcon sx={{ color: '#1a2746', fontSize: 36 }} />
              <Typography variant="h4" sx={{ fontWeight: 700, color: '#1a2746', fontSize: '2rem', lineHeight: 1.2 }}>
                Sheet Processing History
              </Typography>
            </Box>
            <IconButton
              onClick={loadHistory}
              disabled={loading}
              sx={{ color: '#1a2746' }}
              title="Refresh history"
            >
              {loading ? <CircularProgress size={24} /> : <RefreshIcon />}
            </IconButton>
          </Box>

        {loading ? (
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <Typography variant="h6" color="text.secondary">
                Loading history...
              </Typography>
            </CardContent>
          </Card>
        ) : error ? (
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <ErrorIcon sx={{ fontSize: 64, color: '#f44336', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                Error loading history
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {error}
              </Typography>
            </CardContent>
          </Card>
        ) : Object.keys(groupedHistory).length === 0 ? (
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <HistoryIcon sx={{ fontSize: 64, color: '#ccc', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No history yet
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Process some sheets to see history here
              </Typography>
            </CardContent>
          </Card>
        ) : (
          Object.entries(groupedHistory).map(([sheetName, items]) => (
            <Card key={sheetName} sx={{ mb: 3, borderRadius: 2, boxShadow: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600, color: '#1a2746' }}>
                    {sheetName}
                  </Typography>
                  <Chip label={`${items.length} entries`} size="small" />
                </Box>
                <Divider sx={{ mb: 2 }} />
                <List sx={{ p: 0 }}>
                  {items.map((item, idx) => {
                    const type = getHistoryType(item.message || item);
                    return (
                      <ListItem
                        key={idx}
                        sx={{
                          borderLeft: `3px solid ${
                            type === 'success'
                              ? '#4caf50'
                              : type === 'error'
                              ? '#f44336'
                              : '#2196f3'
                          }`,
                          pl: 2,
                          py: 1.5,
                          mb: 1,
                          backgroundColor: '#fafafa',
                          borderRadius: 1,
                          '&:hover': {
                            backgroundColor: '#f5f5f5',
                          },
                        }}
                      >
                        <Box sx={{ mr: 1.5 }}>{getHistoryIcon(type)}</Box>
                        <ListItemText
                          primary={item.message || item}
                          secondary={item.timestamp || item.time || 'No timestamp'}
                          primaryTypographyProps={{
                            sx: {
                              fontSize: '0.95rem',
                              fontWeight: 500,
                              color: '#1a2746',
                            },
                          }}
                          secondaryTypographyProps={{
                            sx: { fontSize: '0.8rem', color: '#666', mt: 0.5 },
                          }}
                        />
                        {item.step && (
                          <Chip
                            label={item.step}
                            size="small"
                            sx={{
                              backgroundColor: '#e3f2fd',
                              color: '#1976d2',
                              fontWeight: 500,
                            }}
                          />
                        )}
                      </ListItem>
                    );
                  })}
                </List>
              </CardContent>
            </Card>
          ))
        )}
        </Container>
      </Box>
    </>
  );
}


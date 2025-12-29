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
  IconButton,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import HistoryIcon from '@mui/icons-material/History';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';

export default function History() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);

  useEffect(() => {
    // Load history from localStorage
    const savedHistory = localStorage.getItem('sheetHistory');
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error('Error loading history:', e);
      }
    }
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
    const sheetName = item.sheetName || 'Unknown Sheet';
    if (!acc[sheetName]) {
      acc[sheetName] = [];
    }
    acc[sheetName].push(item);
    return acc;
  }, {});

  return (
    <Box sx={{ background: '#f5f5f5', minHeight: '100vh', py: 4 }}>
      <Container maxWidth="xl">
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
          <IconButton onClick={() => navigate('/')} sx={{ color: '#1a2746' }}>
            <ArrowBackIcon />
          </IconButton>
          <HistoryIcon sx={{ color: '#1a2746', fontSize: 32 }} />
          <Typography variant="h4" sx={{ fontWeight: 700, color: '#1a2746' }}>
            Sheet Processing History
          </Typography>
        </Box>

        {Object.keys(groupedHistory).length === 0 ? (
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
  );
}


import React from 'react';
import { Box, Typography, List, ListItem, ListItemText, Paper } from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';

export default function HistoryPanel({ history }) {
  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <HistoryIcon sx={{ color: '#1a2746' }} />
        <Typography variant="h6" sx={{ fontWeight: 600, color: '#1a2746' }}>
          Run History
        </Typography>
      </Box>
      <Paper 
        variant="outlined" 
        sx={{ 
          maxHeight: 400, 
          overflow: 'auto',
          backgroundColor: '#f9fafb',
          borderColor: '#e0e0e0'
        }}
      >
        <List sx={{ p: 0 }}>
          {history.length === 0 ? (
            <ListItem>
              <ListItemText 
                primary="No history yet. Load a sheet and run a step to see activity here."
                sx={{ color: '#999', fontStyle: 'italic' }}
              />
            </ListItem>
          ) : (
            history.map((item, idx) => (
              <ListItem 
                key={idx}
                sx={{
                  borderBottom: idx < history.length - 1 ? '1px solid #e0e0e0' : 'none',
                  '&:hover': {
                    backgroundColor: '#f5f5f5',
                  },
                }}
              >
                <ListItemText 
                  primary={item}
                  primaryTypographyProps={{
                    sx: {
                      fontSize: '0.9rem',
                      color: '#1a2746',
                      fontFamily: 'monospace',
                    }
                  }}
                />
              </ListItem>
            ))
          )}
        </List>
      </Paper>
    </Box>
  );
}

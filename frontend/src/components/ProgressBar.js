import React from 'react';
import { LinearProgress, Box, Typography } from '@mui/material';

export default function ProgressBar({ value, label }) {
  if (value === 0) return null;
  
  return (
    <Box sx={{ width: '100%', mb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="body2" sx={{ color: '#1a2746', fontWeight: 500 }}>
          {label}
        </Typography>
        <Typography variant="body2" sx={{ color: '#666', fontWeight: 500 }}>
          {value}%
        </Typography>
      </Box>
      <LinearProgress 
        variant="determinate" 
        value={value} 
        sx={{ 
          height: 8, 
          borderRadius: 4,
          backgroundColor: '#e0e0e0',
          '& .MuiLinearProgress-bar': {
            backgroundColor: '#ff8200',
            borderRadius: 4,
          }
        }} 
      />
    </Box>
  );
}

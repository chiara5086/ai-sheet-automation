import React from 'react';
import { Box, Typography, LinearProgress, Chip } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

/**
 * Simple progress bar component for Home page
 * Shows only overall progress percentage and status
 */
export default function SimpleProgressBar({ stepName, progress, isCompleted, elapsedTime }) {
  if (!stepName && !isCompleted) {
    return null;
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Box
      sx={{
        mb: 2,
        p: 2,
        backgroundColor: '#fff',
        borderRadius: 2,
        border: '1px solid #e0e0e0',
        boxShadow: 1,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="body1" sx={{ fontWeight: 600, color: '#1a2746' }}>
          {isCompleted ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CheckCircleIcon sx={{ color: '#10b981', fontSize: 20 }} /> {/* green-600 */}
              {stepName} - Completed
            </Box>
          ) : (
            `${stepName} - Processing...`
          )}
        </Typography>
        <Chip
          label={`${Math.round(progress)}%`}
          size="small"
          sx={{
            backgroundColor: isCompleted ? '#10b981' : '#1e40af',
            color: '#fff',
            fontWeight: 600,
          }}
        />
      </Box>
      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{
          height: 8,
          borderRadius: 4,
          backgroundColor: '#e5e7eb', // gray-200
          '& .MuiLinearProgress-bar': {
            backgroundColor: isCompleted ? '#10b981' : '#1e40af',
            borderRadius: 4,
          },
        }}
      />
      {elapsedTime > 0 && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
          {isCompleted ? 'Total time: ' : 'Elapsed: '}{formatTime(elapsedTime)}
        </Typography>
      )}
    </Box>
  );
}


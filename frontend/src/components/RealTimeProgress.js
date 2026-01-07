import React from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Card,
  CardContent,
  Grid,
  Chip,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';

export default function RealTimeProgress({
  isActive,
  isCompleted,
  currentStep,
  stats,
  elapsedTime,
}) {
  // Show component if active or completed (to persist after completion)
  if (!isActive && !isCompleted) {
    return null;
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const total = stats.total || 0;
  const processed = stats.processed || 0;
  const success = stats.success || 0;
  const errors = stats.errors || 0;
  const skipped = stats.skipped || 0;
  // Use initial empty rows count (fixed at start) instead of recalculating
  const emptyRows = stats.initialEmptyRows || 0;
  // Progress should be based on empty rows being processed, not total rows
  // Only show empty rows chip when we have the correct value from backend (skipped has been calculated)
  // skipped can be 0 or any number, but it must be defined (not undefined) to indicate backend calculated it
  // Don't show if skipped is undefined (meaning we haven't received the correct value from backend yet)
  // This prevents showing "224 empty rows" initially when it should be "60 empty rows" after backend calculates skipped
  const hasCorrectEmptyRows = skipped !== undefined && emptyRows > 0;
  let progress = 0;
  if (emptyRows > 0) {
    // Calculate progress based on empty rows: (success / emptyRows) * 100
    progress = (success / emptyRows) * 100;
  } else if (total > 0) {
    // Fallback: if emptyRows not calculated yet, use total (but this should be temporary)
    progress = ((success + skipped) / total) * 100;
  }

  return (
    <Card
      sx={{
        mb: 3,
        borderRadius: 2,
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        border: '1px solid #e0e0e0',
      }}
    >
      <CardContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
            {isCompleted ? (
              <>
                <CheckCircleIcon sx={{ color: '#4caf50', fontSize: 24 }} />
                Completed: {currentStep}
              </>
            ) : (
              <>
                Processing: {currentStep}
              </>
            )}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{
                flexGrow: 1,
                height: 10,
                borderRadius: 5,
                backgroundColor: '#e0e0e0',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: isCompleted ? '#4caf50' : '#ff8200',
                  borderRadius: 5,
                },
              }}
            />
            <Typography variant="body2" sx={{ fontWeight: 600, minWidth: 60 }}>
              {Math.round(progress)}%
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary">
            {isCompleted ? 'Total time: ' : 'Elapsed time: '}{formatTime(elapsedTime)}
          </Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Box
              sx={{
                p: 1.5,
                backgroundColor: '#f5f5f5',
                borderRadius: 1,
                textAlign: 'center',
              }}
            >
              <Typography variant="caption" color="text.secondary">
                Total Rows
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {total}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box
              sx={{
                p: 1.5,
                backgroundColor: '#e8f5e9',
                borderRadius: 1,
                textAlign: 'center',
              }}
            >
              <Typography variant="caption" color="text.secondary">
                Processed
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 600, color: '#4caf50' }}>
                {processed}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box
              sx={{
                p: 1.5,
                backgroundColor: '#e3f2fd',
                borderRadius: 1,
                textAlign: 'center',
              }}
            >
              <Typography variant="caption" color="text.secondary">
                Success
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 600, color: '#2196f3' }}>
                {success}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box
              sx={{
                p: 1.5,
                backgroundColor: '#ffebee',
                borderRadius: 1,
                textAlign: 'center',
              }}
            >
              <Typography variant="caption" color="text.secondary">
                Errors
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 600, color: '#f44336' }}>
                {errors}
              </Typography>
            </Box>
          </Grid>
        </Grid>

        <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {hasCorrectEmptyRows && emptyRows > 0 && (
            <Chip
              icon={<HourglassEmptyIcon />}
              label={`${emptyRows} empty rows`}
              size="small"
              sx={{ backgroundColor: '#e3f2fd', color: '#1976d2', fontWeight: 500 }}
            />
          )}
          {skipped > 0 && !isCompleted && (
            <Chip
              label={`${skipped} already filled`}
              size="small"
              sx={{ backgroundColor: '#f5f5f5', color: '#666', fontWeight: 400 }}
            />
          )}
        </Box>
      </CardContent>
    </Card>
  );
}


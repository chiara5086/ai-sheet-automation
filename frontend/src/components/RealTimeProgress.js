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
  currentStep,
  stats,
  elapsedTime,
}) {
  if (!isActive) {
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
  const progress = total > 0 ? (processed / total) * 100 : 0;

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
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
            Processing: {currentStep}
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
                  backgroundColor: '#ff8200',
                  borderRadius: 5,
                },
              }}
            />
            <Typography variant="body2" sx={{ fontWeight: 600, minWidth: 60 }}>
              {Math.round(progress)}%
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary">
            Elapsed time: {formatTime(elapsedTime)}
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

        {skipped > 0 && (
          <Box sx={{ mt: 2 }}>
            <Chip
              icon={<HourglassEmptyIcon />}
              label={`${skipped} skipped`}
              size="small"
              sx={{ backgroundColor: '#fff3e0', color: '#e65100' }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
}


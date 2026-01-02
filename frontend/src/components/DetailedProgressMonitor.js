import React from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Card,
  CardContent,
  Grid,
  Chip,
  IconButton,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import CloseIcon from '@mui/icons-material/Close';

/**
 * Detailed progress monitor component for Monitor page
 * Shows comprehensive progress information with all stats
 */
export default function DetailedProgressMonitor({
  processId,
  stepName,
  sheetName,
  stats,
  elapsedTime,
  isCompleted,
  isActive,
  onRemove,
  onMarkAsCompleted,
  progress: progressProp,
}) {
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
  const emptyRows = stats.initialEmptyRows || 0;
  // Use progress from prop if provided, otherwise calculate
  const progress = progressProp !== undefined ? progressProp : (total > 0 ? ((success + skipped) / total) * 100 : 0);
  
  // Debug log for empty rows (only log once, not on every render)
  React.useEffect(() => {
    if (emptyRows > 0) {
      console.log(`📊 DetailedProgressMonitor: Process ${processId} has ${emptyRows} empty rows`);
    }
  }, [processId, emptyRows]); // Only log when processId or emptyRows changes

  return (
    <Card
      sx={{
        mb: 3,
        borderRadius: 2,
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        border: '1px solid #e0e0e0',
        position: 'relative',
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              {isCompleted ? (
                <>
                  <CheckCircleIcon sx={{ color: '#10b981', fontSize: 24 }} />
                  Completed: {stepName}
                </>
              ) : (
                <>
                  Processing: {stepName}
                </>
              )}
            </Typography>
            {sheetName && (
              <Typography variant="body2" sx={{ fontWeight: 500, color: '#1a2746', mb: 0.5 }}>
                Sheet: {sheetName}
              </Typography>
            )}
            <Typography variant="body2" color="text.secondary">
              {isCompleted ? 'Total time: ' : 'Elapsed time: '}{formatTime(elapsedTime)}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {!isCompleted && isActive && onMarkAsCompleted && (
              <IconButton
                size="small"
                onClick={() => onMarkAsCompleted(processId)}
                sx={{ color: '#1e40af', '&:hover': { color: '#1e3a8a' } }}
                title="Mark as completed"
              >
                <CheckCircleIcon />
              </IconButton>
            )}
            {onRemove && isCompleted && (
              <IconButton
                size="small"
                onClick={() => onRemove(processId)}
                sx={{ color: '#999', '&:hover': { color: '#ef4444' } }}
                title="Remove process"
              >
                <CloseIcon />
              </IconButton>
            )}
          </Box>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <LinearProgress
            variant="determinate"
            value={progress}
            sx={{
              flexGrow: 1,
              height: 10,
              borderRadius: 5,
              backgroundColor: '#e5e7eb',
              '& .MuiLinearProgress-bar': {
                backgroundColor: isCompleted ? '#10b981' : '#1e40af',
                borderRadius: 5,
              },
            }}
          />
          <Typography variant="body2" sx={{ fontWeight: 600, minWidth: 60 }}>
            {Math.round(progress)}%
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
              <Typography variant="h6" sx={{ fontWeight: 600, color: '#10b981' }}>
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
          {emptyRows > 0 && (
            <Chip
              icon={<HourglassEmptyIcon />}
              label={`${emptyRows} empty rows`}
              size="small"
              sx={{ backgroundColor: '#e3f2fd', color: '#1976d2', fontWeight: 500 }}
            />
          )}
          {skipped > 0 && (
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


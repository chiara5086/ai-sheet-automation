import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Chip,
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import WarningIcon from '@mui/icons-material/Warning';

const REQUIRED_COLUMNS = [
  { name: 'YOM > OEM > MODEL', description: 'Asset name or title (column name must start with this)' },
  { name: 'Raw Trusted Data', description: 'Raw data containing technical specifications' },
  { name: 'AI Data', description: 'Additional AI-generated structured data and specifications' },
  { name: 'Script Technical Description', description: 'Technical description generated with AI' },
  { name: 'AI Comparable Price', description: 'AI-sourced comparable listings and prices found online' },
  { name: 'Price', description: 'Final extracted price value' },
];

export default function InstructionsCard({ onDismiss }) {
  const handleCopyEmail = () => {
    navigator.clipboard.writeText('colab-sheets-access@subtle-palisade-482013-e1.iam.gserviceaccount.com');
    alert('Service account email copied to clipboard!');
  };

  return (
    <Box sx={{ mb: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <InfoIcon sx={{ color: '#1a2746', fontSize: 28 }} />
        <Typography variant="h5" sx={{ fontWeight: 700, color: '#1a2746', fontSize: '1.75rem', lineHeight: 1.2 }}>
          Usage Instructions
        </Typography>
      </Box>
      <Typography variant="body2" sx={{ color: '#666', mb: 2, fontStyle: 'italic' }}>
        Follow these steps to set up and use the application:
      </Typography>

      <Grid container spacing={1.5}>
        {/* Step 1: Share the Google Sheet */}
        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              borderRadius: 2,
              boxShadow: 2,
              backgroundColor: 'rgba(173, 216, 230, 0.3)', // Light blue translucent
              border: '1px solid rgba(173, 216, 230, 0.5)',
            }}
          >
            <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Chip label="1" size="small" sx={{ backgroundColor: '#1a2746', color: '#fff', fontWeight: 600, height: 20, fontSize: '0.7rem' }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1a2746', fontSize: '0.85rem' }}>
                  Share the Google Sheet
                </Typography>
              </Box>
              <Typography variant="caption" sx={{ color: '#666', mb: 1, display: 'block', fontSize: '0.75rem' }}>
                Share your Google Sheet with the following service account email:
              </Typography>
              <Box
                component="code"
                onClick={handleCopyEmail}
                sx={{
                  display: 'block',
                  p: 1,
                  backgroundColor: 'rgba(255, 255, 255, 0.7)',
                  borderRadius: 1,
                  fontFamily: 'monospace',
                  fontSize: '0.7rem',
                  color: '#1a2746',
                  border: '1px solid rgba(173, 216, 230, 0.8)',
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                  },
                }}
              >
                colab-sheets-access@subtle-palisade-482013-e1.iam.gserviceaccount.com
              </Box>
              <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: '#999', fontSize: '0.65rem' }}>
                (Click to copy)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Step 2: Verify Column Names */}
        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              borderRadius: 2,
              boxShadow: 2,
              backgroundColor: 'rgba(173, 216, 230, 0.3)', // Light blue translucent
              border: '1px solid rgba(173, 216, 230, 0.5)',
            }}
          >
            <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Chip label="2" size="small" sx={{ backgroundColor: '#1a2746', color: '#fff', fontWeight: 600, height: 20, fontSize: '0.7rem' }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1a2746', fontSize: '0.85rem' }}>
                  Verify Column Names
                </Typography>
              </Box>
              <Typography variant="caption" sx={{ color: '#666', mb: 1, display: 'block', fontSize: '0.75rem' }}>
                Column names must match exactly or start with the specified name:
              </Typography>
              <Box
                sx={{
                  p: 1,
                  backgroundColor: 'rgba(255, 255, 255, 0.5)',
                  borderRadius: 1,
                  border: '1px solid rgba(173, 216, 230, 0.8)',
                  maxHeight: 120,
                  overflowY: 'auto',
                }}
              >
                {REQUIRED_COLUMNS.map((col, idx) => (
                  <Box key={idx} sx={{ py: 0.25 }}>
                    <Typography
                      variant="caption"
                      component="div"
                      sx={{
                        fontFamily: 'monospace',
                        fontWeight: 600,
                        color: '#1a2746',
                        fontSize: '0.7rem',
                        mb: col.description ? 0.1 : 0,
                      }}
                    >
                      • {col.name}
                    </Typography>
                    {col.description && (
                      <Typography
                        variant="caption"
                        component="div"
                        sx={{
                          display: 'block',
                          ml: 1.5,
                          color: '#666',
                          fontStyle: 'italic',
                          fontSize: '0.65rem',
                        }}
                      >
                        {col.description}
                      </Typography>
                    )}
                  </Box>
                ))}
              </Box>
              <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: '#999', fontStyle: 'italic', fontSize: '0.65rem' }}>
                Headers in row 2, data from row 3.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Step 3: Copy the Correct Link */}
        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              borderRadius: 2,
              boxShadow: 2,
              backgroundColor: 'rgba(173, 216, 230, 0.3)', // Light blue translucent
              border: '1px solid rgba(173, 216, 230, 0.5)',
            }}
          >
            <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Chip label="3" size="small" sx={{ backgroundColor: '#1a2746', color: '#fff', fontWeight: 600, height: 20, fontSize: '0.7rem' }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1a2746', fontSize: '0.85rem' }}>
                  Copy the Correct Link
                </Typography>
              </Box>
              <Typography variant="caption" sx={{ color: '#666', mb: 1, display: 'block', fontSize: '0.75rem' }}>
                Copy the link from your browser's address bar, but stop before "/edit". Examples:
              </Typography>
              <Box sx={{ mb: 0.75 }}>
                <Typography variant="caption" sx={{ display: 'block', mb: 0.5, color: '#4caf50', fontWeight: 500, fontSize: '0.7rem' }}>
                  ✅ Correct format:
                </Typography>
                <Box
                  component="code"
                  sx={{
                    display: 'block',
                    p: 1,
                    backgroundColor: 'rgba(255, 255, 255, 0.7)',
                    borderRadius: 1,
                    fontFamily: 'monospace',
                    fontSize: '0.65rem',
                    color: '#1a2746',
                    border: '1px solid rgba(173, 216, 230, 0.8)',
                    wordBreak: 'break-all',
                  }}
                >
                  https://docs.google.com/spreadsheets/d/ABC123XYZ456/
                </Box>
              </Box>
              <Box>
                <Typography variant="caption" sx={{ display: 'block', mb: 0.5, color: '#f44336', fontWeight: 500, fontSize: '0.7rem' }}>
                  ❌ Incorrect format:
                </Typography>
                <Box
                  component="code"
                  sx={{
                    display: 'block',
                    p: 1,
                    backgroundColor: 'rgba(255, 240, 240, 0.7)',
                    borderRadius: 1,
                    fontFamily: 'monospace',
                    fontSize: '0.65rem',
                    color: '#d32f2f',
                    border: '1px solid rgba(244, 67, 54, 0.5)',
                    wordBreak: 'break-all',
                  }}
                >
                  https://docs.google.com/spreadsheets/d/ABC123XYZ456/edit?gid=580610989#gid=580610989
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Step 4: Structured Data Tab Required */}
        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              borderRadius: 2,
              boxShadow: 2,
              backgroundColor: 'rgba(173, 216, 230, 0.3)', // Light blue translucent
              border: '1px solid rgba(173, 216, 230, 0.5)',
            }}
          >
            <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Chip label="4" size="small" sx={{ backgroundColor: '#1a2746', color: '#fff', fontWeight: 600, height: 20, fontSize: '0.7rem' }} />
                <WarningIcon sx={{ color: '#ff9800', fontSize: 16 }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1a2746', fontSize: '0.85rem' }}>
                  Structured Data Tab Required
                </Typography>
              </Box>
              <Typography variant="caption" sx={{ color: '#666', mb: 1, display: 'block', fontSize: '0.75rem' }}>
                Your Google Sheet must have a worksheet that starts with "Structured Data" (e.g., "Structured Data - CNC Lathes").
              </Typography>
              <Box
                sx={{
                  p: 1,
                  backgroundColor: 'rgba(255, 243, 205, 0.7)',
                  borderRadius: 1,
                  border: '1px solid rgba(255, 193, 7, 0.5)',
                }}
              >
                <Typography variant="caption" sx={{ color: '#856404', fontWeight: 500, fontSize: '0.7rem' }}>
                  ⚠️ If your sheet does not have a worksheet starting with "Structured Data", the application will not be able to load your data.
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Collapse,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Chip,
  Divider,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import InfoIcon from '@mui/icons-material/Info';
import WarningIcon from '@mui/icons-material/Warning';

const REQUIRED_COLUMNS = [
  { name: 'YOM OEM Model', description: 'Asset name or title (column name must start with this)' },
  { name: 'Technical Specifications', description: 'Raw data containing technical specifications' },
  { name: 'AI Data', description: '' },
  { name: 'AI Description', description: 'Technical description generated with AI' },
  { name: 'AI Comparable Price', description: '' },
  { name: 'Price', description: '' },
];

export default function InstructionsCard({ onDismiss }) {
  const [expanded, setExpanded] = useState(true);

  return (
    <Card
      sx={{
        mb: 4,
        borderRadius: 2,
        boxShadow: 3,
        border: '2px solid #ff8200',
        backgroundColor: '#fffbf0',
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon sx={{ color: '#ff8200', fontSize: 28 }} />
            <Typography variant="h5" sx={{ fontWeight: 600, color: '#1a2746' }}>
              Usage Instructions
            </Typography>
          </Box>
          <Box>
            <IconButton
              onClick={() => setExpanded(!expanded)}
              sx={{ color: '#1a2746' }}
            >
              {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
        </Box>

        <Collapse in={expanded}>
          <Box sx={{ pl: 1 }}>
            <Typography variant="body1" sx={{ mb: 3, color: '#333', lineHeight: 1.8 }}>
              Before you begin, make sure to follow these steps:
            </Typography>

            <List sx={{ mb: 2 }}>
              <ListItem sx={{ alignItems: 'flex-start', pb: 2 }}>
                <Box sx={{ minWidth: 32, mt: 0.5 }}>
                  <Chip label="1" size="small" sx={{ backgroundColor: '#1a2746', color: '#fff', fontWeight: 600 }} />
                </Box>
                <ListItemText
                  primary={
                    <Typography variant="body1" sx={{ fontWeight: 600, mb: 0.5, color: '#1a2746' }}>
                      Share the Google Sheet
                    </Typography>
                  }
                  secondary={
                    <Typography variant="body2" sx={{ color: '#666', mt: 0.5 }}>
                      Share your Google Sheet with the following service account email:
                      <Box
                        component="code"
                        sx={{
                          display: 'block',
                          mt: 1,
                          p: 1.5,
                          backgroundColor: '#f5f5f5',
                          borderRadius: 1,
                          fontFamily: 'monospace',
                          fontSize: '0.9rem',
                          color: '#1a2746',
                          border: '1px solid #ddd',
                          cursor: 'pointer',
                          '&:hover': {
                            backgroundColor: '#e8e8e8',
                          },
                        }}
                        onClick={(e) => {
                          const text = e.target.textContent;
                          navigator.clipboard.writeText(text);
                        }}
                      >
                        colab-sheets-access@subtle-palisade-482013-e1.iam.gserviceaccount.com
                      </Box>
                      <Typography variant="caption" sx={{ display: 'block', mt: 1, color: '#999' }}>
                        (Click on the code above to copy it)
                      </Typography>
                    </Typography>
                  }
                />
              </ListItem>

              <Divider sx={{ my: 2 }} />

              <ListItem sx={{ alignItems: 'flex-start', pb: 2 }}>
                <Box sx={{ minWidth: 32, mt: 0.5 }}>
                  <Chip label="2" size="small" sx={{ backgroundColor: '#1a2746', color: '#fff', fontWeight: 600 }} />
                </Box>
                <ListItemText
                  primary={
                    <Typography variant="body1" sx={{ fontWeight: 600, mb: 0.5, color: '#1a2746' }}>
                      Verify Column Names
                    </Typography>
                  }
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
                        Make sure your sheet has the following columns. Column names must match exactly or start with the specified name:
                      </Typography>
                      <Box
                        sx={{
                          p: 2,
                          backgroundColor: '#f9f9f9',
                          borderRadius: 1,
                          border: '1px solid #e0e0e0',
                        }}
                      >
                        {REQUIRED_COLUMNS.map((col, idx) => (
                          <Box key={idx} sx={{ py: 0.5 }}>
                            <Typography
                              variant="body2"
                              component="div"
                              sx={{
                                fontFamily: 'monospace',
                                fontWeight: 600,
                                color: '#1a2746',
                                mb: col.description ? 0.25 : 0,
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
                                  ml: 2,
                                  color: '#666',
                                  fontStyle: 'italic',
                                }}
                              >
                                {col.description}
                              </Typography>
                            )}
                          </Box>
                        ))}
                      </Box>
                    </Box>
                  }
                />
              </ListItem>

              <Divider sx={{ my: 2 }} />

              <ListItem sx={{ alignItems: 'flex-start', pb: 2 }}>
                <Box sx={{ minWidth: 32, mt: 0.5 }}>
                  <Chip label="3" size="small" sx={{ backgroundColor: '#1a2746', color: '#fff', fontWeight: 600 }} />
                </Box>
                <ListItemText
                  primary={
                    <Typography variant="body1" sx={{ fontWeight: 600, mb: 0.5, color: '#1a2746' }}>
                      Copy the Correct Link
                    </Typography>
                  }
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
                        Copy the Google Sheet link up to (but not including) the word "edit". Example:
                      </Typography>
                      <Box
                        component="code"
                        sx={{
                          display: 'block',
                          p: 1.5,
                          backgroundColor: '#f5f5f5',
                          borderRadius: 1,
                          fontFamily: 'monospace',
                          fontSize: '0.85rem',
                          color: '#1a2746',
                          border: '1px solid #ddd',
                          wordBreak: 'break-all',
                        }}
                      >
                        https://docs.google.com/spreadsheets/d/1svP4U0MDq11qlVAeRP25gOsTal7uNXBSJhe3ASz7pmE/
                      </Box>
                      <Typography variant="caption" sx={{ display: 'block', mt: 1, color: '#999', fontStyle: 'italic' }}>
                        ✅ Correct: ends with "/" after the ID
                      </Typography>
                      <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: '#f44336', fontStyle: 'italic' }}>
                        ❌ Incorrect: do not include "/edit" or "/edit#gid=0" at the end
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>

              <Divider sx={{ my: 2 }} />

              <ListItem sx={{ alignItems: 'flex-start' }}>
                <Box sx={{ minWidth: 32, mt: 0.5 }}>
                  <Chip label="4" size="small" sx={{ backgroundColor: '#1a2746', color: '#fff', fontWeight: 600 }} />
                </Box>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <WarningIcon sx={{ color: '#ff9800', fontSize: 20 }} />
                      <Typography variant="body1" sx={{ fontWeight: 600, mb: 0.5, color: '#1a2746' }}>
                        Structured Data Tab Required
                      </Typography>
                    </Box>
                  }
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
                        Your Google Sheet must have a tab (worksheet) named "Structured Data" or that starts with "Structured Data".
                      </Typography>
                      <Box
                        sx={{
                          p: 1.5,
                          backgroundColor: '#fff3cd',
                          borderRadius: 1,
                          border: '1px solid #ffc107',
                          mt: 1,
                        }}
                      >
                        <Typography variant="body2" sx={{ color: '#856404', fontWeight: 500 }}>
                          ⚠️ Important: If your sheet does not have a tab with this exact name or that starts with "Structured Data", 
                          the application will not be able to load your data. Make sure to create or rename a tab accordingly.
                        </Typography>
                      </Box>
                    </Box>
                  }
                />
              </ListItem>
            </List>

            <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #e0e0e0' }}>
              <Typography variant="body2" sx={{ color: '#666', fontStyle: 'italic' }}>
                💡 Note: Headers should be in row 2, and data should start from row 3.
              </Typography>
            </Box>
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
}

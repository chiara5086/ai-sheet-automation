import React, { useState } from 'react';
import {
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Box,
  Typography,
  Paper,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CloseIcon from '@mui/icons-material/Close';
import { DEFAULT_PROMPTS } from './PromptEditor';

export default function StepSelector({ steps, onRunStep, customPrompts, onSavePrompt }) {
  const [selectedStep, setSelectedStep] = useState(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState(false);
  const [currentPrompt, setCurrentPrompt] = useState('');

  const handleStepClick = (step) => {
    setSelectedStep(step);
    const prompt = customPrompts[step.name] || DEFAULT_PROMPTS[step.name] || '';
    setCurrentPrompt(prompt);
    setEditingPrompt(false);
    setShowPrompt(true);
  };

  const handleEdit = () => {
    setEditingPrompt(true);
  };

  const handleSave = () => {
    if (onSavePrompt && selectedStep) {
      onSavePrompt(selectedStep.name, currentPrompt);
    }
    setEditingPrompt(false);
  };

  const handleRun = () => {
    if (selectedStep && onRunStep) {
      // Save the current prompt if it was edited
      if (editingPrompt && onSavePrompt) {
        onSavePrompt(selectedStep.name, currentPrompt);
      }
      setShowPrompt(false);
      onRunStep(selectedStep.name, currentPrompt);
    }
  };

  const handleClose = () => {
    setShowPrompt(false);
    setSelectedStep(null);
    setEditingPrompt(false);
  };

  return (
    <>
      <Paper sx={{ borderRadius: 2, boxShadow: 2 }}>
        <List sx={{ p: 0 }}>
          {steps.map((step, index) => (
            <ListItem
              key={step.id}
              disablePadding
              sx={{
                borderBottom: index < steps.length - 1 ? '1px solid #e0e0e0' : 'none',
              }}
            >
              <ListItemButton
                onClick={() => handleStepClick(step)}
                sx={{
                  py: 1.5,
                  px: 2,
                  '&:hover': {
                    backgroundColor: '#f5f5f5',
                  },
                }}
              >
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    backgroundColor: step.color,
                    color: '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 600,
                    mr: 2,
                    flexShrink: 0,
                  }}
                >
                  {step.id}
                </Box>
                <ListItemText
                  primary={step.name}
                  primaryTypographyProps={{
                    sx: {
                      fontWeight: 500,
                      color: '#1a2746',
                    },
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Paper>

      {/* Prompt Dialog */}
      <Dialog
        open={showPrompt}
        onClose={handleClose}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
          },
        }}
      >
        <DialogTitle
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: '#1a2746',
            color: '#fff',
            py: 2,
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            {selectedStep?.name}
          </Typography>
          <IconButton onClick={handleClose} sx={{ color: '#fff' }} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent sx={{ p: 3, pt: 3 }}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {editingPrompt
                ? 'Edit the prompt below. Variables: {asset}, {tech_specs}, {comparable}, {ai_data}'
                : 'Current prompt for this step:'}
            </Typography>
          </Box>
          <TextField
            multiline
            rows={12}
            fullWidth
            value={currentPrompt}
            onChange={(e) => setCurrentPrompt(e.target.value)}
            variant="outlined"
            disabled={!editingPrompt}
            sx={{
              '& .MuiOutlinedInput-root': {
                fontFamily: 'monospace',
                fontSize: '0.875rem',
              },
            }}
          />
        </DialogContent>

        <DialogActions sx={{ p: 2, pt: 1, gap: 1 }}>
          {!editingPrompt ? (
            <>
              <Button onClick={handleEdit} startIcon={<EditIcon />} color="primary">
                Edit Prompt
              </Button>
              <Box sx={{ flexGrow: 1 }} />
              <Button onClick={handleClose} color="inherit">
                Cancel
              </Button>
              <Button
                onClick={handleRun}
                variant="contained"
                startIcon={<PlayArrowIcon />}
                sx={{
                  backgroundColor: selectedStep?.color || '#1a2746',
                  '&:hover': {
                    backgroundColor: selectedStep?.color || '#2d3f66',
                    opacity: 0.9,
                  },
                }}
              >
                Run Step
              </Button>
            </>
          ) : (
            <>
              <Button onClick={() => setEditingPrompt(false)} color="inherit">
                Cancel Edit
              </Button>
              <Box sx={{ flexGrow: 1 }} />
              <Button onClick={handleSave} variant="contained" color="primary">
                Save Prompt
              </Button>
              <Button
                onClick={handleRun}
                variant="contained"
                startIcon={<PlayArrowIcon />}
                sx={{
                  backgroundColor: selectedStep?.color || '#1a2746',
                  '&:hover': {
                    backgroundColor: selectedStep?.color || '#2d3f66',
                    opacity: 0.9,
                  },
                }}
              >
                Save & Run
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>
    </>
  );
}


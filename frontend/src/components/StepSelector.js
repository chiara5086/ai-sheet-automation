import React, { useState } from 'react';
import {
  Box,
  Typography,
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

export default function StepSelector({ steps, onRunStep, customPrompts, onSavePrompt, isProcessing = false }) {
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
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {steps.map((step) => (
          <Button
            key={step.id}
            onClick={() => handleStepClick(step)}
            variant="contained"
            disabled={isProcessing}
            fullWidth
            sx={{
              py: 2,
              px: 3,
              backgroundColor: step.color,
              color: '#fff',
              fontWeight: 600,
              fontSize: '1rem',
              textTransform: 'none',
              borderRadius: 2,
              boxShadow: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-start',
              gap: 2,
              '&:hover': {
                backgroundColor: step.color,
                opacity: 0.9,
                boxShadow: 4,
                transform: 'translateY(-2px)',
              },
              '&:disabled': {
                backgroundColor: '#e0e0e0',
                color: '#9e9e9e',
              },
              transition: 'all 0.2s ease-in-out',
            }}
          >
            <Box
              sx={{
                width: 36,
                height: 36,
                borderRadius: '50%',
                backgroundColor: 'rgba(255, 255, 255, 0.3)',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '1.1rem',
                flexShrink: 0,
              }}
            >
              {step.id}
            </Box>
            <Typography
              sx={{
                fontWeight: 600,
                fontSize: '1rem',
                color: '#fff',
              }}
            >
              {step.name}
            </Typography>
          </Button>
        ))}
      </Box>

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


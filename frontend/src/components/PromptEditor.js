import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  IconButton,
  Tooltip,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import CloseIcon from '@mui/icons-material/Close';

const DEFAULT_PROMPTS = {
  'Build Description': `You are a technical documentation engineer writing for an industrial machinery catalog. For each item below, generate a single, objective technical description (200–250 words).
Rules:
- Start with: 'The [Asset Name] is a...' where [Asset Name] MUST be taken verbatim from the Asset Name field. — Do NOT restate or reformat the name.
- Infer it from context if not explicit.
- Immediately state its primary industrial application (e.g., 'engineered for quarry loading', 'designed for earthmoving in construction sites').
- Then describe technical systems in prose: engine, transmission, hydraulics, capacities, dimensions, etc. — only if present in input.
- Integrate specs into sentences (e.g., 'Powered by a... delivering... hp').
- NEVER use subjective, promotional, or evaluative language (e.g., 'robust', 'powerful', 'efficient', 'top-performing').
- Use only facts from 'Raw' or 'Clean' input. Do not invent data.
- Output must be one paragraph. No bullets, dashes, markdown, or lists.
- Output ONLY the description. No other text.

Asset Name: {asset}

Raw input:
{tech_specs}
{ai_data}`,

  'AI Source Comparables': `Search the web for this item. For each comparable listing, return ONLY: Condition, Price, and the Listing URL. No extra text. Format each on one line as: Condition: [condition], Price: [price], URL: [link]. Return up to 10 recent results.

Asset: {asset}
Technical Specifications: {tech_specs}`,

  'Extract price from AI Comparable': `You are an expert in construction equipment valuation. Read the asset details, technical specs, and comparable listings below. Choose the single most relevant price, convert it to USD if needed, and return ONLY the final USD amount formatted like 'XXXXXX.XX'. If no relevant price exists, return blank. Do not add any explanation, note, or extra text.
Asset details: {asset}
Technical specifications: {tech_specs}
Comparable listings found online: {comparable}
{ai_data}`,

  'AI Source New Price': `You are an expert in construction equipment valuation. Based ONLY on the asset details below, return the current market price of a BRAND NEW unit in USD. Return ONLY the price formatted exactly like this: 'XXXXXX.XX'. If no explicit new price is available, return blank. Do not add any words, explanations, notes, or symbols. Do not say 'blank', 'N/A', or anything else. Only output the price or nothing.
Asset details:
{asset}
Technical specifications:
{tech_specs}`,

  'AI Similar Comparable': `You are an expert in construction equipment valuation. Search for similar equipment based on the technical specifications and AI Data provided below. Find comparable assets that match the specifications and characteristics. For each similar asset found, return ONLY: Condition, Price, and the Listing URL. Format each on one line as: Condition: [condition], Price: [price], URL: [link]. Return up to 10 recent results. If no similar assets are found, return blank.

Asset: {asset}
Technical Specifications: {tech_specs}
AI Data: {ai_data}`,
};

export default function PromptEditor({ stepName, onSave }) {
  const [open, setOpen] = useState(false);
  const [prompt, setPrompt] = useState(DEFAULT_PROMPTS[stepName] || '');

  const handleOpen = () => {
    setPrompt(DEFAULT_PROMPTS[stepName] || '');
    setOpen(true);
  };

  const handleSave = () => {
    if (onSave) {
      onSave(stepName, prompt);
    }
    DEFAULT_PROMPTS[stepName] = prompt;
    setOpen(false);
  };

  const handleReset = () => {
    setPrompt(DEFAULT_PROMPTS[stepName] || '');
  };

  return (
    <>
      <Tooltip title="View/Edit Prompt">
        <IconButton
          size="small"
          onClick={handleOpen}
          sx={{
            color: '#1a2746',
            '&:hover': {
              backgroundColor: '#f0f0f0',
            },
          }}
        >
          <EditIcon fontSize="small" />
        </IconButton>
      </Tooltip>

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
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
            Edit Prompt: {stepName}
          </Typography>
          <IconButton
            onClick={() => setOpen(false)}
            sx={{ color: '#fff' }}
            size="small"
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent sx={{ p: 3, pt: 3 }}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Variables disponibles: {'{asset}'}, {'{tech_specs}'}, {'{comparable}'}, {'{ai_data}'}
            </Typography>
          </Box>
          <TextField
            multiline
            rows={15}
            fullWidth
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            variant="outlined"
            sx={{
              '& .MuiOutlinedInput-root': {
                fontFamily: 'monospace',
                fontSize: '0.875rem',
              },
            }}
          />
        </DialogContent>

        <DialogActions sx={{ p: 2, pt: 1, gap: 1 }}>
          <Button onClick={handleReset} color="inherit">
            Reset to Default
          </Button>
          <Box sx={{ flexGrow: 1 }} />
          <Button onClick={() => setOpen(false)} color="inherit">
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            variant="contained"
            startIcon={<SaveIcon />}
            sx={{
              backgroundColor: '#1a2746',
              '&:hover': {
                backgroundColor: '#2d3f66',
              },
            }}
          >
            Save Prompt
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export { DEFAULT_PROMPTS };


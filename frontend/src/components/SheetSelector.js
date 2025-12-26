import React, { useState } from 'react';
import { TextField, Button, Box, InputAdornment } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

export default function SheetSelector({ onSheetSelected }) {
  const [sheetUrl, setSheetUrl] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (sheetUrl) {
      onSheetSelected(sheetUrl);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 2 }}>
      <TextField
        label="Google Sheet URL"
        placeholder="Paste your Google Sheet URL here..."
        variant="outlined"
        value={sheetUrl}
        onChange={e => setSheetUrl(e.target.value)}
        fullWidth
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon sx={{ color: '#1a2746' }} />
            </InputAdornment>
          ),
        }}
        sx={{
          '& .MuiOutlinedInput-root': {
            '&:hover fieldset': {
              borderColor: '#ff8200',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#ff8200',
            },
          },
        }}
      />
      <Button 
        type="submit" 
        variant="contained" 
        sx={{
          backgroundColor: '#ff8200',
          minWidth: 150,
          py: 1.5,
          '&:hover': {
            backgroundColor: '#ffa033',
          },
        }}
      >
        Load Sheet
      </Button>
    </Box>
  );
}

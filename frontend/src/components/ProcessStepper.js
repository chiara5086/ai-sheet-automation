import React from 'react';
import { Stepper, Step, StepLabel, Box } from '@mui/material';

const steps = [
  'Build Description',
  'AI Source Comparables',
  'Extract Price',
  'AI Source New Price',
  'AI Similar Comparable',
];

export default function ProcessStepper({ activeStep }) {
  return (
    <Box sx={{ mb: 4, p: 2, backgroundColor: '#f9fafb', borderRadius: 2 }}>
      <Stepper 
        activeStep={activeStep} 
        alternativeLabel
        nonLinear
        sx={{
          '& .MuiStepLabel-root .Mui-completed': {
            color: '#ff8200',
          },
          '& .MuiStepLabel-label.Mui-completed.MuiStepLabel-alternativeLabel': {
            color: '#1a2746',
            fontWeight: 600,
          },
          '& .MuiStepLabel-root .Mui-active': {
            color: '#ff8200',
          },
          '& .MuiStepLabel-label.Mui-active.MuiStepLabel-alternativeLabel': {
            color: '#1a2746',
            fontWeight: 600,
          },
          '& .MuiStepLabel-root .Mui-disabled': {
            color: '#999',
          },
          // Hide step numbers (icons)
          '& .MuiStepIcon-root': {
            display: 'none',
          },
          '& .MuiStepIcon-text': {
            display: 'none',
          },
        }}
      >
        {steps.map((label, idx) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
    </Box>
  );
}

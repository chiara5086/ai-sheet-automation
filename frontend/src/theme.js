// Custom MUI theme with Aucto colors
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1a2746', // Aucto dark blue
      light: '#2d3f66',
      dark: '#0f1628',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#ff8200', // Aucto orange
      light: '#ffa033',
      dark: '#cc6600',
      contrastText: '#ffffff',
    },
    info: {
      main: '#c9daf8', // Light blue (for price from comparables)
    },
    warning: {
      main: '#fff2cc', // Light yellow (for new price)
    },
    error: {
      main: '#e10098', // Magenta (admin bar)
    },
    background: {
      default: '#ffffff', // White background like Aucto
      paper: '#ffffff',
    },
    text: {
      primary: '#1a2746',
      secondary: '#666666',
    },
  },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    h1: {
      fontWeight: 700,
      color: '#1a2746',
    },
    h2: {
      fontWeight: 700,
      color: '#1a2746',
    },
    h3: {
      fontWeight: 700,
      color: '#1a2746',
    },
    h4: {
      fontWeight: 600,
      color: '#1a2746',
    },
    h5: {
      fontWeight: 600,
      color: '#1a2746',
    },
    h6: {
      fontWeight: 600,
      color: '#1a2746',
    },
    button: {
      fontWeight: 600,
      textTransform: 'none',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          padding: '10px 24px',
          fontWeight: 600,
        },
        containedPrimary: {
          backgroundColor: '#1a2746',
          '&:hover': {
            backgroundColor: '#2d3f66',
          },
        },
        containedSecondary: {
          backgroundColor: '#ff8200',
          '&:hover': {
            backgroundColor: '#ffa033',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 4,
          },
        },
      },
    },
  },
});

export default theme;

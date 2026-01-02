import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Box, Button } from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import MonitorIcon from '@mui/icons-material/Monitor';
import HistoryIcon from '@mui/icons-material/History';
import NotificationBell from './NotificationBell';

/**
 * Fixed navigation bar component with text labels
 * Stays at the top of the page for easy navigation
 */
export default function NavigationBar({ notifications = [], onClearNotifications }) {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { label: 'Home', path: '/', icon: HomeIcon },
    { label: 'Monitor', path: '/monitor', icon: MonitorIcon },
    { label: 'History', path: '/history', icon: HistoryIcon },
  ];

  return (
    <AppBar 
      position="fixed" 
      sx={{ 
        backgroundColor: '#1E293B', 
        boxShadow: 3,
        zIndex: 1300,
        borderRadius: 0, // No rounded corners
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', px: 3 }}>
        {/* Left side: App title */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Typography variant="h5" component="div" sx={{ fontWeight: 700, color: '#ffffff' }}>
            Data Structuring Sheet App
          </Typography>
        </Box>

        {/* Center: Navigation links */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Button
                key={item.path}
                onClick={() => navigate(item.path)}
                startIcon={<Icon />}
                sx={{
                  color: isActive ? '#ff8200' : '#ffffff',
                  fontWeight: isActive ? 600 : 400,
                  textTransform: 'none',
                  fontSize: '0.95rem',
                  px: 2,
                  py: 1,
                  borderRadius: 1, // Rounded corners for buttons (OK)
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  },
                  ...(isActive && {
                    backgroundColor: 'rgba(255, 130, 0, 0.15)',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 130, 0, 0.25)',
                    },
                  }),
                }}
              >
                {item.label}
              </Button>
            );
          })}
        </Box>

        {/* Right side: Notifications */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {onClearNotifications && (
            <NotificationBell
              notifications={notifications}
              onClearAll={onClearNotifications}
            />
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
}


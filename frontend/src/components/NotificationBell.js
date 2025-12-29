import React, { useState } from 'react';
import {
  Badge,
  IconButton,
  Popover,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  Divider,
  Button,
} from '@mui/material';
import NotificationsIcon from '@mui/icons-material/Notifications';
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';

export default function NotificationBell({ notifications, onClearAll }) {
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircleIcon sx={{ color: '#4caf50', fontSize: 20 }} />;
      case 'error':
        return <ErrorIcon sx={{ color: '#f44336', fontSize: 20 }} />;
      default:
        return <InfoIcon sx={{ color: '#2196f3', fontSize: 20 }} />;
    }
  };

  return (
    <>
      <IconButton
        onClick={handleClick}
        sx={{
          color: '#fff',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
          },
        }}
      >
        <Badge badgeContent={unreadCount} color="error">
          {unreadCount > 0 ? (
            <NotificationsIcon />
          ) : (
            <NotificationsNoneIcon />
          )}
        </Badge>
      </IconButton>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        PaperProps={{
          sx: {
            width: 400,
            maxHeight: 500,
            mt: 1,
            borderRadius: 2,
            boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
          },
        }}
      >
        <Box sx={{ p: 2, pb: 1 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Notifications
          </Typography>
        </Box>
        <Divider />
        <List sx={{ maxHeight: 400, overflow: 'auto', p: 0 }}>
          {notifications.length === 0 ? (
            <ListItem>
              <ListItemText
                primary="No notifications"
                secondary="You're all caught up!"
                primaryTypographyProps={{
                  sx: { color: '#999', fontStyle: 'italic' },
                }}
              />
            </ListItem>
          ) : (
            notifications.map((notification, idx) => (
              <ListItem
                key={idx}
                sx={{
                  backgroundColor: notification.read ? 'transparent' : '#f5f5f5',
                  '&:hover': {
                    backgroundColor: '#fafafa',
                  },
                }}
              >
                <Box sx={{ mr: 1.5 }}>{getIcon(notification.type)}</Box>
                <ListItemText
                  primary={notification.title}
                  secondary={notification.message}
                  primaryTypographyProps={{
                    sx: {
                      fontWeight: notification.read ? 400 : 600,
                      fontSize: '0.9rem',
                    },
                  }}
                  secondaryTypographyProps={{
                    sx: { fontSize: '0.8rem', color: '#666' },
                  }}
                />
                <Typography variant="caption" sx={{ color: '#999', ml: 1 }}>
                  {notification.time}
                </Typography>
              </ListItem>
            ))
          )}
        </List>
        {notifications.length > 0 && (
          <>
            <Divider />
            <Box sx={{ p: 1.5, display: 'flex', justifyContent: 'flex-end' }}>
              <Button size="small" onClick={onClearAll}>
                Clear All
              </Button>
            </Box>
          </>
        )}
      </Popover>
    </>
  );
}


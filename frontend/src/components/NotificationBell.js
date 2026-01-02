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

export default function NotificationBell({ 
  notifications, 
  onClearAll, 
  onMarkAllRead,
  onMarkAsRead 
}) {
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
        <Box sx={{ p: 2, pb: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Notifications
          </Typography>
          {notifications.length > 0 && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              {unreadCount > 0 && onMarkAllRead && (
                <Button
                  size="small"
                  onClick={onMarkAllRead}
                  sx={{
                    textTransform: 'none',
                    fontSize: '0.75rem',
                    color: '#1976d2',
                    minWidth: 'auto',
                    px: 1,
                  }}
                >
                  Mark all read
                </Button>
              )}
              {onClearAll && (
                <Button
                  size="small"
                  onClick={onClearAll}
                  sx={{
                    textTransform: 'none',
                    fontSize: '0.75rem',
                    color: '#d32f2f',
                    minWidth: 'auto',
                    px: 1,
                  }}
                >
                  Clear
                </Button>
              )}
            </Box>
          )}
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
                key={notification.id || idx}
                onClick={() => !notification.read && onMarkAsRead && onMarkAsRead(notification.id)}
                sx={{
                  backgroundColor: notification.read ? 'transparent' : '#f5f5f5',
                  cursor: !notification.read && onMarkAsRead ? 'pointer' : 'default',
                  '&:hover': {
                    backgroundColor: notification.read ? '#fafafa' : '#eeeeee',
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
      </Popover>
    </>
  );
}


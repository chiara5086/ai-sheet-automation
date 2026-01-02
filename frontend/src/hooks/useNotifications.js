import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'appNotifications';

export function useNotifications() {
  const [notifications, setNotifications] = useState([]);

  // Load notifications from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setNotifications(parsed);
      } catch (e) {
        console.error('Error loading notifications from localStorage:', e);
      }
    }
  }, []);

  // Save notifications to localStorage whenever they change
  useEffect(() => {
    if (notifications.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(notifications));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [notifications]);

  const addNotification = useCallback((type, title, message) => {
    const notification = {
      id: Date.now() + Math.random(), // Ensure unique ID
      type,
      title,
      message,
      time: new Date().toLocaleTimeString(),
      read: false,
    };
    setNotifications((prev) => [notification, ...prev]);
  }, []);

  const markAsRead = useCallback((id) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) =>
      prev.map((n) => ({ ...n, read: true }))
    );
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  return {
    notifications,
    addNotification,
    markAsRead,
    markAllAsRead,
    clearNotifications,
  };
}


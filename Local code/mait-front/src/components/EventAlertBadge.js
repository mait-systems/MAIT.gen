// src/components/EventAlertBadge.js
import React, { useEffect, useState } from 'react';
import axios from 'axios';

const EventAlertBadge = ({ onClick }) => {
  const [eventCount, setEventCount] = useState(0);

  const fetchEvents = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:8001/api/active-events');
      setEventCount(res.data.count || 0);
    } catch (err) {
      console.error('Failed to fetch active event count:', err);
    }
  };

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  if (eventCount === 0) return null;

  return (
    <div
      onClick={onClick}
      style={{
        background: '#dc3545',
        color: 'white',
        padding: '6px 12px',
        borderRadius: '20px',
        cursor: 'pointer',
        display: 'inline-block',
        marginBottom: '10px',
        fontWeight: 'bold',
      }}
    >
      🔴 {eventCount} Active Event{eventCount > 1 ? 's' : ''}
    </div>
  );
};

export default EventAlertBadge;

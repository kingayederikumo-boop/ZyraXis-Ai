'use client';
import { useState, useEffect } from 'react';
import WebApp from '@twa-dev/sdk';
import axios from 'axios';

export default function Usage() {
  const [usage, setUsage] = useState(null);
  // Similar fetch logic as Home
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">Usage</h1>
      {/* Progress bars for AI, Roleplay, etc. */}
      <div>Usage data fetched from /api/usage</div>
    </div>
  );
}
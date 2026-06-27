'use client';
import { useState, useEffect } from 'react';
import WebApp from '@twa-dev/sdk';
import axios from 'axios';
import { ArrowRight, Image as ImageIcon, MessageSquare, FileText, Zap } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://yourdomain.com';

export default function Home() {
  const [usage, setUsage] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initData = WebApp.initDataUnsafe;
    if (initData.user) {
      fetchUsage(initData.user.id);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUsage = async (tgId: number) => {
    try {
      const res = await axios.get(`${API_BASE}/api/usage`, { 
        params: { telegram_id: tgId },
        headers: { 'x-telegram-init-data': WebApp.initData }
      });
      setUsage(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const quickAction = (action: string) => {
    WebApp.openTelegramLink(`https://t.me/yourbot?start=${action}`);
  };

  return (
    <div className="p-4 max-w-xl mx-auto">
      <div className="card p-8 mb-6 text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-[#A855F7] to-[#E879F9] bg-clip-text text-transparent">ZyraXis AI</h1>
        <p className="text-xl mt-2 text-[#B5B5C3]">Smart AI Assistant</p>
        <button 
          onClick={() => quickAction('chat')}
          className="btn-primary mt-6 w-full py-4 rounded-2xl text-lg font-semibold flex items-center justify-center gap-2"
        >
          Continue Chat <ArrowRight className="w-5 h-5" />
        </button>
      </div>

      <div className="card p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Today's Usage</h2>
        <div className="grid grid-cols-2 gap-4">
          {['AI Replies', 'Roleplay', 'Files', 'Image Edits'].map((label, i) => (
            <div key={i} className="bg-[#12052A] p-4 rounded-xl">
              <div className="text-sm text-[#B5B5C3]">{label}</div>
              <div className="text-2xl font-mono mt-1">
                {usage ? `${usage.ai_remaining || 10}/10` : '--/10'}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-8">
        {[
          { icon: MessageSquare, label: "Ask AI", action: "ask" },
          { icon: ImageIcon, label: "Generate Image", action: "image" },
          { icon: MessageSquare, label: "Roleplay", action: "roleplay" },
          { icon: FileText, label: "Analyze File", action: "file" }
        ].map((act, i) => (
          <button 
            key={i} 
            onClick={() => quickAction(act.action)} 
            className="card p-6 hover:scale-[1.02] transition flex flex-col items-center gap-3 active:scale-95"
          >
            <act.icon className="w-8 h-8 text-[#A855F7]" />
            <span className="font-medium">{act.label}</span>
          </button>
        ))}
      </div>

      <div className="card p-6">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-[#A855F7]" /> Premium Features
        </h3>
        {['Better Search', 'Video Generation', 'Coding Assistant'].map((f, i) => (
          <div 
            key={i} 
            onClick={() => WebApp.openTelegramLink('https://t.me/yourbot?start=premium')} 
            className="flex justify-between items-center py-4 border-b border-[#1A0D3D] last:border-none cursor-pointer hover:bg-[#1A0D3D] px-2 rounded-xl"
          >
            <span>{f}</span>
            <span className="text-[#A855F7] text-sm">Upgrade →</span>
          </div>
        ))}
      </div>
    </div>
  );
}

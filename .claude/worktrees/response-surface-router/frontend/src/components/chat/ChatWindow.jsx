/**
 * ChatWindow — main chat container.
 * Composes: Sidebar + MessageList + ChatInput + PDFExportButton.
 */

import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { ChatProvider, useChat } from '../../context/ChatContext';
import Sidebar from './Sidebar';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import PDFExportButton from './PDFExportButton';
import './ChatWindow.css';

export default function ChatWindow() {
  return (
    <ChatProvider>
      <ChatWindowContent />
    </ChatProvider>
  );
}

function ChatWindowContent() {
  const location = useLocation();
  const { activeSession, sendMessage } = useChat();

  // Auto-submit initialPrompt if navigated from Dashboard recommendation feed
  useEffect(() => {
    const initialPrompt = location.state?.initialPrompt;
    if (initialPrompt) {
      sendMessage(initialPrompt);
      // Clear location state to prevent re-submitting on refresh
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  return (
    <div className="chat-window">
      <Sidebar />
      <div className="chat-area">
        {/* Chat area top toolbar (session info + PDF Export) */}
        <div className="chat-area__toolbar surface-raised">
          <div className="flex items-center gap-2">
            <span className="label-section text-xs">Active Thread</span>
            <span className="font-mono text-xs text-muted">
              {activeSession?.session_id ? `Session #${activeSession.session_id}` : 'New Conversation'}
            </span>
          </div>
          <PDFExportButton sessionId={activeSession?.session_id} />
        </div>

        <MessageList />
        <ChatInput />
      </div>
    </div>
  );
}

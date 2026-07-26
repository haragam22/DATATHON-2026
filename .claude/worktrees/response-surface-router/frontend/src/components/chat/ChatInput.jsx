/**
 * ChatInput — message input bar with textarea, voice STT button, language switcher, and send button.
 * Submits on Enter (Shift+Enter for newline).
 */

import { useState, useRef, useEffect } from 'react';
import { Send, Loader, Mic, MicOff, Languages } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import './ChatInput.css';

export default function ChatInput() {
  const [text, setText] = useState('');
  const [lang, setLang] = useState('en'); // 'en' or 'kn'
  const [isListening, setIsListening] = useState(false);
  const textareaRef = useRef(null);
  const recognitionRef = useRef(null);
  const { sendMessage, isLoading } = useChat();

  // Initialize Speech Recognition API if supported by browser
  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = lang === 'kn' ? 'kn-IN' : 'en-IN';

      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map((result) => result[0].transcript)
          .join('');
        setText(transcript);
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto';
          textareaRef.current.style.height =
            Math.min(textareaRef.current.scrollHeight, 160) + 'px';
        }
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, [lang]);

  const toggleMic = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in this browser. Try Chrome or Edge.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.lang = lang === 'kn' ? 'kn-IN' : 'en-IN';
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const handleSubmit = () => {
    if (!text.trim() || isLoading) return;

    // Prepend language tag if Kannada mode is active
    const finalQuery = lang === 'kn' ? `[Kannada Translation Mode] ${text}` : text;

    sendMessage(finalQuery);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e) => {
    setText(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  };

  return (
    <div className="chat-input">
      {/* Active Language Mode Indicator Banner */}
      {lang === 'kn' && (
        <div className="chat-input__lang-banner text-xs text-gold flex items-center gap-2 mb-2">
          <Languages size={14} />
          <span>Kannada Input Mode Active — Auto-Translating via Zia Services</span>
        </div>
      )}

      <div className="chat-input__container">
        {/* Language Toggle Button */}
        <button
          className={`chat-input__lang-btn ${
            lang === 'kn' ? 'active-gold' : ''
          }`}
          onClick={() => setLang(lang === 'en' ? 'kn' : 'en')}
          title="Toggle Language (English / ಕನ್ನಡ)"
          disabled={isLoading}
          type="button"
        >
          <Languages size={13} />
          <span>{lang === 'en' ? 'EN' : 'KN'}</span>
        </button>

        {/* Text Input */}
        <textarea
          ref={textareaRef}
          className="chat-input__textarea"
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={
            lang === 'kn'
              ? 'ಕನ್ನಡದಲ್ಲಿ ಪ್ರಶ್ನೆ ಕೇಳಿ (Ask in Kannada or English)...'
              : 'Ask a question about KSP crime data…'
          }
          rows={1}
          disabled={isLoading}
          aria-label="Message input"
        />

        {/* Voice Input Button */}
        <button
          className={`chat-input__mic btn-icon ${isListening ? 'listening' : ''}`}
          onClick={toggleMic}
          disabled={isLoading}
          title={isListening ? 'Stop Voice Recording' : 'Voice Input (Speech-to-Text)'}
          aria-label="Voice input"
          type="button"
        >
          {isListening ? (
            <MicOff size={16} className="text-red mic-pulse" />
          ) : (
            <Mic size={16} strokeWidth={1.5} />
          )}
        </button>

        {/* Send Button */}
        <button
          className="chat-input__send btn-icon"
          onClick={handleSubmit}
          disabled={!text.trim() || isLoading}
          aria-label="Send message"
          title="Send (Enter)"
          type="button"
        >
          {isLoading ? (
            <Loader size={16} strokeWidth={1.5} className="chat-input__spinner" />
          ) : (
            <Send size={16} strokeWidth={1.5} />
          )}
        </button>
      </div>

      <div className="chat-input__hint text-xs text-faint flex justify-between items-center">
        <span>Press Enter to send · Shift+Enter for a new line</span>
        <span>Voice STT & Zia Translation Enabled</span>
      </div>
    </div>
  );
}

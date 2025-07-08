import React, { useState, useRef, useEffect } from 'react';
import Message from './Message';
import LoadingSpinner from './LoadingSpinner';
import { sendMessage } from '../services/api';

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm your AI Nutritionist. Describe your health symptoms (like fatigue, hair loss, low energy) and I’ll suggest helpful foods or advice.",
      sender: 'ai',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: inputValue.trim(),
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await sendMessage(userMessage.text, [...messages, userMessage]);
      const aiMessage = {
        id: Date.now() + 1,
        text: response.reply,
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: "Sorry! I'm having trouble reaching the server.",
        sender: 'ai',
        isError: true,
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-container">
        <div className="messages-container">
          {messages.map(msg => <Message key={msg.id} message={msg} />)}
          {isLoading && (
            <div className="message ai-message">
              <div className="message-content loading">
                <LoadingSpinner />
                <span>Analyzing your symptoms...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Buy Now Button */}
        <a
          href="https://yourshopifystore.com/collections/all"
          className="buy-now-button"
          target="_blank"
          rel="noopener noreferrer"
        >
          Buy Now
        </a>

        <div className="input-container">
          <form onSubmit={handleSubmit} className="input-form">
            <div className="input-wrapper">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="e.g. I feel tired all the time"
                className="message-input"
                rows="1"
                maxLength={500}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
              <button
                type="submit"
                className={`send-button ${!inputValue.trim() || isLoading ? 'disabled' : ''}`}
                disabled={!inputValue.trim() || isLoading}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z" fill="currentColor" />
                </svg>
              </button>
            </div>
            <div className="input-footer">
              <small>{inputValue.length}/500 characters • Press Enter to send</small>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

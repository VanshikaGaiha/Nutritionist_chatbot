import React from 'react';

const Message = ({ message }) => {
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  return (
    <div className={`message ${message.sender === 'user' ? 'user-message' : 'ai-message'} ${message.isError ? 'error-message' : ''}`}>
      <div className="message-content">
        <div className="message-text">{message.text.split('\n').map((line, index) => (<React.Fragment key={index}>{line}<br /></React.Fragment>))}</div>

        <div className="message-timestamp">{formatTime(message.timestamp)}</div>
      </div>
    </div>
  );
};

export default Message;

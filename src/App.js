import React from 'react';
import ChatInterface from './components/ChatInterface';
import './styles/App.css';

function App() {
  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <h1>🥗 AI Nutritionist</h1>
          <p>Get personalized nutrition advice powered by AI</p>
        </div>
      </header>
      <main className="app-main">
        <ChatInterface />
      </main>
      <footer className="app-footer">
        <p>© 2025 AI Nutritionist Chatbot</p>
      </footer>
    </div>
  );
}

export default App;

import React from 'react';
import ChatInterface from './components/ChatInterface';
import './styles/App.css';
import logo from './assets/Green BN logo-02.png'; // This line imports your logo

function App() {
  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <img src={logo} alt="Better Nutrition" className="header-logo" />
        </div>
      </header>
      <main className="app-main">
        <ChatInterface />
      </main>
      <footer className="app-footer">
        <p>© 2025 AI Nutritionist Chatbot — Free nutrition advice for everyone</p>
      </footer>
    </div>
  );
}

export default App;

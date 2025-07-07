// client/src/services/api.js

// Store session per browser/tab using in-memory storage
let sessionId = null;

const getSessionId = () => sessionId;
const setSessionId = (id) => { sessionId = id; };

export const sendMessage = async (newMessage, history = []) => {
  try {
    const response = await fetch("https://nutritionist-chatbot-backend.onrender.com/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        message: newMessage, 
        history: history, // Keep for backward compatibility, but won't be used by backend when session is active
        session_id: getSessionId(),
        use_session: true
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // Store session ID from response for future requests
    if (data.session_id) {
      setSessionId(data.session_id);
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

// Function to reset session (for new conversations)
export const resetSession = () => {
  sessionId = null;
};

// Function to get current session info
export const getCurrentSessionId = () => {
  return getSessionId();
};

// Function to check if session exists
export const hasActiveSession = () => {
  return getSessionId() !== null;
};
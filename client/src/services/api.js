// client/src/services/api.js

// Store session per browser/tab using sessionStorage
const getSessionId = () => sessionStorage.getItem('nutritionist_session_id');
const setSessionId = (id) => sessionStorage.setItem('nutritionist_session_id', id);

export const sendMessage = async (newMessage, history) => {
  try {
    const response = await fetch("https://nutritionist-chatbot-backend.onrender.com/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        message: newMessage, 
        history: history,
        session_id: getSessionId(),  // Get session ID from browser storage
        use_session: true            // Enable session management
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
  sessionStorage.removeItem('nutritionist_session_id');
};

// Function to get current session ID
export const getCurrentSessionId = () => {
  return getSessionId();
};

// Function to check if session exists
export const hasActiveSession = () => {
  return getSessionId() !== null;
};

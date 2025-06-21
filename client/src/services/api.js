// client/src/services/api.js

export const sendMessage = async (newMessage, history) => {
  const response = await fetch("https://nutritionist-chatbot-backend.onrender.com/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: newMessage, history: history }),
  });

  return await response.json();
};

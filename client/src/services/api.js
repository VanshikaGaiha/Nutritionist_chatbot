import axios from 'axios';

// 💡 Directly use your deployed backend URL:
const API_BASE_URL = 'https://nutritionist-chatbot-backend.onrender.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sendMessage = async (newMessage, history) => {
  const response = await fetch("https://nutritionist-chatbot-backend.onrender.com/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: newMessage, history: history }),
  });
  return await response.json();
};


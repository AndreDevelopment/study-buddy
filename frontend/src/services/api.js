import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000', // Your FastAPI backend URL
});

export const uploadNote = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await API.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const askAgent = async (question) => {
  const response = await API.post('/ask', { question });
  return response.data;
};

<template>
  <div class="app-container">
    <!-- Sidebar for Note Management -->
    <aside class="sidebar">
      <h2>📚 Study Notes</h2>
      <p class="subtitle">Upload markdown or text notes to update your RAG database.</p>
      
      <div class="upload-box">
        <input type="file" @change="handleFileChange" accept=".md,.txt" class="modern-btn" style="background-color: #1f2937;"/>
        <button @click="uploadFile" :is-loading="uploading" class="modern-btn" style="background-color: #10b981;">
         <i class="pi pi-upload"></i> {{ uploading ? 'Ingesting & Vectorizing...' : 'Upload & Index' }}
        </button>
      </div>

      <div v-if="uploadMessage" class="message" :class="uploadStatus">
        {{ uploadMessage }}
      </div>
    </aside>

    <!-- Main Chat Interface -->
    <main class="chat-main">
      <header class="chat-header">
        <h1>AI Study Assistant</h1>
        <span>Grounded in your notes with citations</span>
      </header>

      <div class="chat-history" ref="chatHistoryRef">
        <div v-for="(msg, index) in messages" :key="index" :class="['message-bubble', msg.sender]">
          <div class="sender-label">{{ msg.sender === 'user' ? 'You' : 'Agent' }}</div>
          <div class="message-text">{{ msg.text }}</div>
        </div>
        <div v-if="loading" class="message-bubble agent">
          <div class="sender-label">Agent</div>
          <div class="message-text typing">Thinking and searching your notes...</div>
        </div>
      </div>

      <div class="chat-input-area">
        <input 
          type="text" 
          v-model="userInput" 
          @keyup.enter="sendMessage" 
          placeholder="Ask Study Buddy..." 
          :disabled="loading"
        />
        <button @click="sendMessage" :disabled="loading || !userInput.trim()" class="modern-btn" style="background-color: #10b981;">
          Send <i class="pi pi-send"></i>
        </button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import { uploadNote, askAgent } from './services/api';

const selectedFile = ref(null);
const uploading = ref(false);
const uploadMessage = ref('');
const uploadStatus = ref('');

const userInput = ref('');
const messages = ref([
  { sender: 'agent', text: 'Hello! Upload your study notes on the left, then ask me anything about them.' }
]);
const loading = ref(false);
const chatHistoryRef = ref(null);

const handleFileChange = (event) => {
  selectedFile.value = event.target.files[0];
};

const uploadFile = async () => {
  if (!selectedFile.value) {
    uploadMessage.value = 'Please select a file first.';
    uploadStatus.value = 'error';
    return;
  }

  uploading.value = true;
  uploadMessage.value = '';

  try {
    const data = await uploadNote(selectedFile.value);
    uploadMessage.value = data.message;
    uploadStatus.value = 'success';
    selectedFile.value = null;
  } catch (error) {
    uploadMessage.value = error.response?.data?.detail || 'Failed to upload note.';
    uploadStatus.value = 'error';
  } finally {
    uploading.value = false;
  }
};

const sendMessage = async () => {
  if (!userInput.value.trim() || loading.value) return;

  const question = userInput.value;
  messages.value.push({ sender: 'user', text: question });
  userInput.value = '';
  loading.value =true;
  scrollToBottom();

  try {
    const data = await askAgent(question);
    messages.value.push({ sender: 'agent', text: data.answer });
  } catch (error) {
    messages.value.push({ 
      sender: 'agent', 
      text: 'Sorry, I encountered an error querying the backend server.' 
    });
  } finally {
    loading.value = false;
    scrollToBottom();
  }
};

const scrollToBottom = () => {
  nextTick(() => {
    if (chatHistoryRef.value) {
      chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight;
    }
  });
};
</script>

<style scoped>
/* Modern, clean layout styling */
.app-container {
  display: flex;
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color:  #f7f9fc;
  background: #333;
  margin: -8px; /* Reset default body margins */
}

.sidebar {
  width: 300px;
  background: #000;
  /* border-right: 1px solid #e1e4e8; */
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar h2 {
  font-size: 1.25rem;
  margin-bottom: 0;
}

.subtitle {
  font-size: 0.85rem;
  color: #888888;
  margin-top: 0;
}

.upload-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 10px;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.message {
  font-size: 0.85rem;
  padding: 8px;
  border-radius: 4px;
}
.message.success { background: #d1fae5; color: #065f46; }
.message.error { background: #fee2e2; color: #991b1b; }

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.chat-header {
  padding: 16px 24px;
  background: #000;
  border-bottom: 1px solid #313131;
}

.chat-header h1 {
  font-size: 1.1rem;
  margin: 0;
}

.chat-header span {
  font-size: 0.8rem;
  color: #888;
}

.chat-history {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.4;
}

.message-bubble.user {
  background: #2563eb;
  color: white;
  align-self: flex-end;
  border-bottom-right-radius: 2px;
}

.message-bubble.agent {
  color: #ffffff;
  background: #4b5563;
  border: 1px solid #545454;
  align-self: flex-start;
  border-bottom-left-radius: 2px;
}

.sender-label {
  font-size: 0.75rem;
  font-weight: bold;
  margin-bottom: 4px;
  opacity: 0.8;
}

.chat-input-area {
  padding: 16px 24px;
  background: #000;
  /* border-top: 1px solid #4b4b4b; */
  display: flex;
  gap: 12px;
}

.chat-input-area input {
  flex: 1;
  padding: 10px 14px;
  /* border: 1px solid #d1d5db; */
  background: #1f2937;
  color: #f7f9fc;
  border-radius: 20px;
  outline: none;
}

.chat-input-area input:focus {
  border-color: #2563eb;
}

.btn-send {
  background: #10b981;
  color: white;
  border: none;
  padding: 0 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-send:hover {
  background: #059669;
}
.btn-send:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}
</style>
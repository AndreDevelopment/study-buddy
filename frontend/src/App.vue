<template>
  <div class="app-container">
    <!-- Sidebar for Note Management -->
    <aside class="sidebar">
      <h2><i class="pi pi-book"></i> Study Notes</h2>
      <p class="subtitle">Upload markdown or text notes to update your RAG database.</p>

      <div class="upload-box">
        <input type="file" @change="handleFileChange" accept=".md,.txt" class="file-input" aria-label="Choose a notes file" />
        <button @click="uploadFile" :is-loading="uploading" class="btn btn-upload">
          <i class="pi pi-upload"></i> {{ uploading ? 'Ingesting & Vectorizing...' : 'Upload & Index' }}
        </button>
      </div>

      <div v-if="uploadMessage" class="message" :class="uploadStatus" role="status">
        {{ uploadMessage }}
      </div>
    </aside>

    <!-- Main Chat Interface -->
    <main class="chat-main">
      <header class="chat-header">
        <h1>AI Study Assistant</h1>
        <span>Grounded in your notes with citations</span>
      </header>

      <div class="chat-history" ref="chatHistoryRef" aria-live="polite">
        <div v-for="(msg, index) in messages" :key="index" :class="['message-bubble', msg.sender]">
          <div class="sender-label">{{ msg.sender === 'user' ? 'You' : 'Agent' }}</div>
          <div class="message-text">
            <component
              v-for="(line, li) in formatText(msg.text)"
              :key="li"
              :is="line.level ? 'h' + line.level : 'div'"
              :class="['line', { blank: line.blank, heading: line.level }]"
            ><template v-for="(part, i) in line.parts" :key="i"><strong v-if="part.bold">{{ part.text }}</strong><template v-else>{{ part.text }}</template></template></component>
          </div>
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
          aria-label="Your question"
          :disabled="loading"
        />
        <button @click="sendMessage" :disabled="loading || !userInput.trim()" class="btn btn-send">
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

// The agent answer is a list of content blocks: a thinking block
// (signature/thinking/type) followed by a text block ({ text }).
// Keep only the text values.
const extractAnswerText = (answer) => {
  let blocks = answer;
  if (typeof answer === 'string') {
    try {
      blocks = JSON.parse(answer);
    } catch {
      return answer.replace(/\\n/g, '\n'); // plain string with literal "\n"
    }
  }
  if (!Array.isArray(blocks)) blocks = [blocks];
  const text = blocks
    .map((b) => (typeof b === 'string' ? b : b?.text))
    .filter((t) => typeof t === 'string')
    .join('\n\n');
  return text || String(answer);
};

// Split a line on **bold** markers into plain/bold parts (no v-html needed).
const parseInline = (text) =>
  text
    .split(/(\*\*[^*]+?\*\*)/g)
    .filter(Boolean)
    .map((p) =>
      p.startsWith('**') && p.endsWith('**') && p.length > 4
        ? { text: p.slice(2, -2), bold: true }
        : { text: p, bold: false }
    );

// Turn the answer text into lines. "# " to "###### " become h1-h6.
const formatText = (text) =>
  String(text)
    .split('\n')
    .map((raw) => {
      const m = raw.match(/^\s{0,3}(#{1,6})\s+(.*)$/);
      if (m) return { level: m[1].length, parts: parseInline(m[2].replace(/\s+#+\s*$/, '')) };
      return { level: 0, blank: raw.trim() === '', parts: parseInline(raw) };
    });

const handleFileChange =(event) => {
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
    messages.value.push({ sender: 'agent', text: extractAnswerText(data.answer) });
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
.app-container {
  display: flex;
  height: 100vh;
  height: 100dvh;
  color: var(--text);
  background: var(--paper);
}

/* ---------- Sidebar: the binder ---------- */
.sidebar {
  width: 320px;
  flex-shrink: 0;
  background: var(--ink);
  color: var(--on-ink);
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
}

.sidebar h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.sidebar h2 .pi {
  font-size: 1.15rem;
  color: var(--highlight);
}

.subtitle {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.5;
  color: var(--on-ink-muted);
}

.upload-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
  padding: 16px;
  border: 1.5px dashed var(--ink-line);
  border-radius: 10px;
  background: var(--ink-soft);
}

.file-input {
  width: 100%;
  font-family: inherit;
  font-size: 0.85rem;
  color: var(--on-ink-muted);
}

.file-input::file-selector-button {
  margin-right: 12px;
  padding: 8px 14px;
  font-family: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--on-ink);
  background: transparent;
  border: 1px solid var(--on-ink-muted);
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.file-input::file-selector-button:hover {
  background: var(--ink-line);
}

/* ---------- Buttons ---------- */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 11px 20px;
  font-family: inherit;
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.4;
  color: var(--ink);
  background: var(--highlight);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.15s ease, transform 0.1s ease;
}

.btn:hover:not(:disabled) {
  background: var(--highlight-deep);
}

.btn:active:not(:disabled) {
  transform: translateY(1px);
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-send {
  color: var(--on-ink);
  background: var(--ink);
  border-radius: 24px;
  padding: 0 24px;
}

.btn-send:hover:not(:disabled) {
  background: var(--ink-soft);
}

/* ---------- Upload status ---------- */
.message {
  font-size: 0.875rem;
  line-height: 1.45;
  padding: 10px 12px;
  border-radius: 8px;
  border-left: 4px solid currentColor;
}
.message.success { background: var(--ok-bg); color: var(--ok); }
.message.error { background: var(--err-bg); color: var(--err); }

/* ---------- Chat ---------- */
.chat-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  padding: 22px 32px 18px;
  background: var(--card);
  border-bottom: 1px solid var(--rule);
}

.chat-header h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.015em;
}

.chat-header span {
  font-family: var(--font-read);
  font-style: italic;
  font-size: 1rem;
  color: var(--muted);
}

/* Ruled notebook paper behind the conversation */
.chat-history {
  flex: 1;
  padding: 32px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background-color: var(--paper);
  background-image: repeating-linear-gradient(
    to bottom,
    transparent 0,
    transparent 31px,
    var(--rule) 31px,
    var(--rule) 32px
  );
  background-attachment: local;
}

.message-bubble {
  max-width: min(68ch, 78%);
  padding: 14px 18px 16px;
  border-radius: 10px;
}

/* Your questions read like highlighted text */
.message-bubble.user {
  align-self: flex-end;
  background: var(--highlight);
  color: var(--ink);
  border-bottom-right-radius: 2px;
}

/* Answers read like a printed handout */
.message-bubble.agent {
  align-self: flex-start;
  background: var(--card);
  color: var(--text);
  border: 1px solid var(--rule);
  border-left: 4px solid var(--ink);
  border-bottom-left-radius: 2px;
}

.sender-label {
  margin-bottom: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--muted);
}

.message-bubble.user .sender-label {
  color: var(--ink);
  opacity: 0.7;
}

.message-text .line {
  white-space: pre-wrap;
  margin: 0;
}

.message-text .line.blank {
  min-height: 0.8em;
}

.message-text .heading {
  font-family: var(--font-ui);
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: -0.01em;
  margin: 0.6em 0 0.25em;
}

.message-text h1 { font-size: 1.6rem; }
.message-text h2 { font-size: 1.4rem; }
.message-text h3 { font-size: 1.22rem; }
.message-text h4 { font-size: 1.1rem; }
.message-text h5 { font-size: 1rem; }
.message-text h6 { font-size: 0.9rem; color: var(--muted); }

.message-text .heading:first-child {
  margin-top: 0;
}

.message-text {
  overflow-wrap: anywhere;
  font-family: var(--font-read);
  font-size: 1.1rem;
  line-height: 1.6;
}

.message-text.typing {
  color: var(--muted);
  font-style: italic;
  animation: pulse 1.6s ease-in-out infinite;
}

@keyframes pulse {
  50% { opacity: 0.45; }
}

/* ---------- Input ---------- */
.chat-input-area {
  padding: 16px 32px 20px;
  background: var(--card);
  border-top: 1px solid var(--rule);
  display: flex;
  gap: 12px;
}

.chat-input-area input {
  flex: 1;
  min-width: 0;
  padding: 12px 18px;
  font-family: inherit;
  font-size: 1rem;
  color: var(--text);
  background: var(--paper);
  border: 1.5px solid var(--rule);
  border-radius: 24px;
  outline: none;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.chat-input-area input::placeholder {
  color: var(--muted);
}

.chat-input-area input:focus {
  border-color: var(--ink);
  background: var(--card);
}

.chat-input-area input:focus-visible {
  box-shadow: 0 0 0 3px var(--highlight);
}

.chat-input-area input:disabled {
  opacity: 0.6;
}

/* ---------- Small screens ---------- */
@media (max-width: 760px) {
  .app-container {
    flex-direction: column;
  }
  .sidebar {
    width: 100%;
    max-height: 42%;
    padding: 18px 16px;
    gap: 10px;
  }
  .upload-box {
    margin-top: 4px;
  }
  .chat-header,
  .chat-input-area {
    padding-left: 16px;
    padding-right: 16px;
  }
  .chat-history {
    padding: 20px 16px;
  }
  .message-bubble {
    max-width: 92%;
  }
}
</style>

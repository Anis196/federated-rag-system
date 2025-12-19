# React Frontend - Component Details

## Components Breakdown

### 1. App Component
**File:** `frontend/src/App.tsx`

**Responsibility:** Root component orchestrating the entire application

**Features:**
- Main layout structure
- Routes management (if using React Router)
- Global state setup
- CSS styling (`src/App.css`)

**Key Props:** None (root component)

**Children:**
- Navigation/Header
- Main Content (Chat Interface or Page Routes)
- Footer (optional)

---

### 2. Chat Interface Components
**Location:** `src/pages/Index.tsx` or `src/components/`

**Responsibility:** Display chat messages and input form

**Sub-components:**
- **Message List** - Displays conversation history
- **User Message** - Message bubble for user input
- **Assistant Message** - Message bubble for AI responses
- **Input Form** - Text input and send button

**Features:**
- Message history display with timestamps
- User vs. Assistant message differentiation (styling)
- Auto-scroll to latest message
- Responsive design for mobile/desktop
- Real-time response updates

**State Management:**
```typescript
const [messages, setMessages] = useState<Message[]>([]);
const [loading, setLoading] = useState(false);
```

---

### 3. ChatService
**File:** `src/services/chatApi.ts`

**Responsibility:** Centralized API communication with Spring Boot backend

**Key Functions:**

**`sendQuery(message: string): Promise<ChatResponse>`**
- Sends user query to `/api/rag/chat` endpoint
- Handles HTTP request/response
- Returns AI-generated answer
- Error handling and retry logic

**`getHistory(): Promise<Message[]>`**
- Retrieves chat history (if backend supports)
- Used for persistence across sessions

**Error Handling:**
- Catches network errors
- Returns user-friendly error messages
- Logs errors for debugging

**Configuration:**
```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';
const RAG_ENDPOINT = `${API_URL}/api/rag/chat`;
```

**Used by:** Chat interface components

---

### 4. Type Definitions
**File:** `frontend/src/types/chat.ts`

**Content:**
```typescript
interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: number;
}

interface ChatRequest {
  query: string;
  k?: number;  // Top-k results (optional)
}

interface ChatResponse {
  answer: string;
  query: string;
  timestamp: number;
}
```

**Used by:** All chat-related components and services

---

### 5. Custom Hooks
**Directory:** `frontend/src/hooks/`

**Hook: `useChatMessages.ts`**
- Manages chat state (messages array)
- Handles adding new messages
- Clears chat history
- Persists to localStorage (optional)

**Hook: `useToast.ts`**
- Displays toast notifications
- Shows errors, success messages
- Used for user feedback

**Hook: `use-mobile.tsx`**
- Detects if viewport is mobile
- Used for responsive design decisions
- CSS media query hook

**Usage:**
```typescript
const { messages, addMessage, clearChat } = useChatMessages();
const { toast } = useToast();
const isMobile = useMobile();
```

---

### 6. Utility Functions
**File:** `frontend/src/lib/utils.ts`

**Common Utilities:**
- `formatTimestamp(ts: number): string` - Format message timestamps
- `parseResponse(response: any): string` - Extract answer from response
- `sanitizeInput(input: string): string` - Prevent XSS attacks
- `debounce(fn, delay)` - Debounce function for search
- `cn(...classes)` - Merge CSS class names (clsx utility)

**Used by:** Components and services

---

### 7. Navigation Component
**File:** `frontend/src/components/NavLink.tsx`

**Responsibility:** Navigation links between pages

**Features:**
- Active link highlighting
- Responsive navigation menu
- Mobile hamburger menu (optional)

---

### 8. UI Components (shadcn/ui)
**Directory:** `frontend/src/components/ui/`

**Pre-built Components:**
- `button.tsx` - Styled button component
- `input.tsx` - Text input field
- `card.tsx` - Card container
- `dialog.tsx` - Modal dialog
- `toast.tsx` - Toast notifications
- etc.

**Benefits:**
- Accessible (WCAG compliant)
- Keyboard navigation support
- Fully customizable with Tailwind
- TypeScript support

**Usage:**
```typescript
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export function ChatInput() {
  return (
    <>
      <Input placeholder="Ask a question..." />
      <Button>Send</Button>
    </>
  )
}
```

---

### 9. Page Components
**File:** `frontend/src/pages/Index.tsx` - Main chat page
**File:** `frontend/src/pages/NotFound.tsx` - 404 page

---

## Component Communication Flow

```
App Component
├── Chat Page (Index.tsx)
│   ├── Message List (displays messages from state)
│   ├── Message Components (renders individual messages)
│   └── Chat Input Form
│       ├── Input Field (shadcn/ui)
│       └── Send Button
│           └── Calls ChatService.sendQuery()
│
Service Layer (chatApi.ts)
├── Makes HTTP POST to Spring Boot (/api/rag/chat)
├── Receives response
└── Updates component state via callback

State Updates
├── New message added to message array
└── Component re-renders with new message
```

---

## State Management Strategy

**Local Component State:**
```typescript
const [messages, setMessages] = useState<Message[]>([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

**Custom Hook State:**
```typescript
// useChatMessages hook manages message persistence
const { messages, addMessage } = useChatMessages();
```

**Global State (if needed):**
- Consider using Zustand or Context API for cross-component state
- Currently using local state is sufficient

---

## Dependencies

| Library | Purpose |
|---------|---------|
| react | UI framework |
| typescript | Type safety |
| vite | Build tool |
| tailwindcss | Styling |
| shadcn/ui | UI components |
| axios or fetch | HTTP requests |
| react-router-dom | Routing (if applicable) |
| zustand | Global state (if applicable) |
| clsx | Class name utilities |

---

## Best Practices Implemented

✅ Separation of concerns (components, services, hooks)
✅ TypeScript for type safety
✅ Reusable components from shadcn/ui
✅ Custom hooks for stateful logic
✅ Centralized API communication
✅ Error handling and user feedback
✅ Responsive design with Tailwind CSS
✅ Accessibility with shadcn/ui components

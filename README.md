# React LangChain Chatbot

A full-stack AI chatbot application built with React, FastAPI, and LangChain's ReAct agent pattern. Features intelligent tool selection, real-time web search via Tavily, Google Trends integration, streaming responses, Supabase authentication, and complete Docker containerization.

## Key Features

- **ReAct Agent** - Intelligent reasoning loop that decides when and which tools to use
- **Tool Visibility** - Real-time UI indicators showing which tool is being used (🔍 Web Search or 📈 Google Trends)
- **Tavily Web Search** - Current information and recent news integration
- **Google Trends** - Track trending topics and popular searches
- **Streaming Responses** - Real-time token streaming for immediate feedback
- **Supabase Auth** - Secure JWT-based authentication with email/password
- **Message Persistence** - Full conversation history stored in Supabase
- **SSE Streaming** - Server-Sent Events for efficient real-time communication
- **Docker Ready** - Complete containerization with health checks

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐         ┌──────────────────┐              │
│  │  Frontend        │         │  Backend         │              │
│  │  (React 18)      │◄───────►│  (FastAPI)       │              │
│  │  Port 3000       │         │  Port 8000       │              │
│  └──────────────────┘         └──────────────────┘              │
│         │                              │                        │
│         │                              ├─────────────┐          │
│         │                              │             │          │
│         │                      ┌───────▼────────┐   │          │
│         │                      │   Supabase     │   │          │
│         │                      │  (PostgreSQL)  │   │          │
│         │                      │  Auth + DB     │   │          │
│         │                      └────────────────┘   │          │
│         │                                           │          │
│         └───────────────────────────────────────────┤          │
│                                                     │          │
│                                    ┌────────────────▼──────┐   │
│                                    │  External APIs       │   │
│                                    │  - Tavily (Search)   │   │
│                                    │  - Groq (LLM)        │   │
│                                    │  - Google Trends     │   │
│                                    └──────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

**Frontend:**
- React 18 with TypeScript
- React Router for navigation
- Axios for HTTP requests
- CSS3 for styling
- Server-Sent Events (SSE) for streaming

**Backend:**
- FastAPI (Python web framework)
- Pydantic for data validation
- LangChain for agent orchestration
- Groq API for LLM (free tier)
- Tavily Python SDK for web search
- Supabase for authentication and database
- PyTrends for Google Trends data

**Infrastructure:**
- Docker & Docker Compose
- PostgreSQL (via Supabase)
- JWT authentication

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Supabase account (free tier available at https://supabase.com)
- Tavily API key (free tier at https://tavily.com)
- Groq API key (free tier at https://console.groq.com)

### Setup Instructions

1. **Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/react-langchain-chatbot.git
cd react-langchain-chatbot
```

2. **Create environment file:**
```bash
cp .env.example .env
```

3. **Configure `.env` with your credentials:**
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret

# API Keys
TAVILY_API_KEY=your-tavily-key
GROQ_API_KEY=your-groq-key

# Backend Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=False
```

4. **Start all services:**
```bash
docker-compose up --build
```

5. **Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Project Structure

```
react-langchain-chatbot/
│
├── frontend/                           # React TypeScript frontend
│   ├── src/
│   │   ├── api/
│   │   │   ├── chatClient.ts          # API client with SSE handling
│   │   │   └── config.ts              # API configuration
│   │   ├── components/
│   │   │   └── Message.tsx            # Message display component
│   │   ├── pages/
│   │   │   ├── Chat.tsx               # Main chat interface
│   │   │   ├── Login.tsx              # Login page
│   │   │   └── Signup.tsx             # Signup page
│   │   ├── state/
│   │   │   ├── authContext.tsx        # Auth state management
│   │   │   └── chatContext.tsx        # Chat state management
│   │   ├── styles/
│   │   │   ├── auth.css               # Auth pages styling
│   │   │   ├── chat.css               # Chat interface styling
│   │   │   └── message.css            # Message styling
│   │   ├── types/
│   │   │   └── index.ts               # TypeScript type definitions
│   │   ├── utils/
│   │   │   └── logger.ts              # Logging utility
│   │   ├── App.tsx                    # Main app component
│   │   └── index.tsx                  # React entry point
│   ├── public/
│   │   └── index.html                 # HTML template
│   ├── Dockerfile                     # Frontend Docker image
│   ├── package.json                   # Dependencies
│   └── tsconfig.json                  # TypeScript config
│
├── backend/                            # FastAPI backend
│   ├── app/
│   │   ├── main.py                    # FastAPI application
│   │   ├── core/
│   │   │   └── config.py              # Settings from environment
│   │   ├── middleware/
│   │   │   └── auth.py                # JWT authentication middleware
│   │   ├── routers/
│   │   │   ├── auth.py                # Auth endpoints (signup, login, logout)
│   │   │   ├── chat.py                # Chat endpoints (message, conversations)
│   │   │   └── health.py              # Health check endpoint
│   │   ├── schemas/
│   │   │   ├── auth.py                # Auth request/response models
│   │   │   └── chat.py                # Chat request/response models
│   │   ├── services/
│   │   │   ├── agent/
│   │   │   │   └── react_agent.py     # ReAct agent implementation
│   │   │   ├── tools/
│   │   │   │   ├── tavily.py          # Tavily web search wrapper
│   │   │   │   └── google_trends_mcp.py # Google Trends wrapper
│   │   │   └── db/
│   │   │       └── supabase_client.py # Supabase database client
│   │   └── utils/
│   │       ├── errors.py              # Custom error classes
│   │       └── logging.py             # Logging configuration
│   ├── migrations/
│   │   ├── 001_create_tables.sql      # Database schema
│   │   └── SETUP.md                   # Migration instructions
│   ├── Dockerfile                     # Backend Docker image
│   ├── requirements.txt                # Python dependencies
│   └── pytest.ini                     # Pytest configuration
│
├── docker-compose.yml                 # Docker Compose orchestration
├── .env.example                       # Environment template
└── README.md                          # This file
```

## API Endpoints

### Authentication (`/auth`)
- `POST /auth/signup` - Create new user account
  - Body: `{ "email": "user@example.com", "password": "password" }`
  - Returns: `{ "access_token": "jwt_token", "user": {...} }`

- `POST /auth/login` - Login with credentials
  - Body: `{ "email": "user@example.com", "password": "password" }`
  - Returns: `{ "access_token": "jwt_token", "user": {...} }`

- `POST /auth/logout` - Logout (requires auth)
  - Returns: `{ "message": "Logged out successfully" }`

### Chat (`/chat`)
- `POST /chat/message` - Send message with streaming response (SSE)
  - Headers: `Authorization: Bearer {token}`
  - Body: `{ "conversation_id": "uuid", "content": "message" }`
  - Returns: Server-Sent Events stream

- `GET /chat/conversations` - Get user's conversations (requires auth)
  - Returns: `{ "conversations": [...] }`

- `GET /chat/conversations/{id}/messages` - Get conversation messages (requires auth)
  - Returns: `{ "messages": [...] }`

### Health (`/health`)
- `GET /health` - Service health check
  - Returns: `{ "status": "healthy" }`

## How the ReAct Agent Works

### Agent Loop Flow

1. **User sends message** → Frontend sends to backend via HTTP POST
2. **Agent receives message** → Loads conversation history from Supabase
3. **Agent thinks** → Calls Groq LLM to decide if tools are needed
4. **Tool selection** → Agent parses LLM response for ACTION and INPUT
5. **UI shows tool** → Frontend displays which tool is being used
6. **Tool execution** → Invokes Tavily or Google Trends
7. **Response generation** → LLM synthesizes final answer with tool results
8. **Streaming** → Response tokens stream back to frontend via SSE
9. **Message saved** → Final response stored in Supabase

### Tool Selection Logic

The agent intelligently chooses tools based on query intent:

| Query Type | Tool Used | Example |
|-----------|-----------|---------|
| Trending topics | 📈 Google Trends | "What's trending today?" |
| Current news | 🔍 Web Search | "Latest AI developments" |
| General knowledge | None (LLM only) | "How does ML work?" |

### Streaming Events

The backend emits SSE events during processing:

```
event: loading
data: {"status": "Agent is thinking..."}

event: responding
data: {"status": "Generating response..."}

event: tool_selected
data: {"tool": "Tavily_Search", "tool_name": "Web Search"}

event: tool_activity
data: {"tool": "Tavily_Search", "status": "started"}

event: token
data: {"token": "The "}

event: token
data: {"token": "latest "}

event: tool_activity
data: {"tool": "Tavily_Search", "status": "completed"}

event: streaming
data: {"status": "Streaming response..."}

event: done
data: {"message_id": "generated"}
```

## Environment Variables

| Variable              | Description                          | Example                       |
| --------------------- | ------------------------------------ | ----------------------------- |
| `SUPABASE_URL`        | Supabase project URL                 | `https://project.supabase.co` |
| `SUPABASE_KEY`        | Supabase anon key                    | `eyJhbGc...`                  |
| `SUPABASE_JWT_SECRET` | JWT secret for token validation      | `super-secret-key`            |
| `TAVILY_API_KEY`      | Tavily web search API key            | `tvly-...`                    |
| `GROQ_API_KEY`        | Groq LLM API key (free tier)         | `gsk_...`                     |
| `ENVIRONMENT`         | Environment (production/development) | `production`                  |
| `LOG_LEVEL`           | Logging level (DEBUG/INFO/WARNING)   | `INFO`                        |
| `DEBUG`               | Debug mode                           | `False`                       |

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run locally with auto-reload
python -m uvicorn app.main:app --reload --port 8000

# Run tests
pytest

# Run with specific log level
LOG_LEVEL=DEBUG python -m uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

## Troubleshooting

### Services won't start

```bash
# Check Docker is running
docker ps

# Check if ports are in use
lsof -i :3000
lsof -i :8000

# View service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild from scratch
docker-compose down
docker-compose up --build
```

### Authentication issues

```bash
# Check Supabase credentials
cat .env | grep SUPABASE

# Verify JWT token in browser console
localStorage.getItem('auth_token')

# Check backend auth logs
docker-compose logs backend | grep -i auth
```

### Tool not working

**Tavily Search failing:**
- Verify API key at https://tavily.com/dashboard
- Check backend logs: `docker-compose logs backend | grep -i tavily`
- Ensure internet connectivity

**Google Trends failing:**
- Google may block automated requests (expected behavior)
- System gracefully falls back to LLM knowledge
- Check logs: `docker-compose logs backend | grep -i trends`

**Groq rate limit (429 error):**
- Free tier: 100k tokens/day limit
- Wait for limit to reset or upgrade to Dev Tier
- Alternative: Use OpenAI API instead

### Database connection issues

```bash
# Verify Supabase credentials
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Check if Supabase project is active
curl $SUPABASE_URL/rest/v1/

# View backend database logs
docker-compose logs backend | grep -i supabase
```

## Performance Notes

- **Streaming:** SSE provides real-time token streaming for responsive UX
- **Tool execution:** Typically 1-3 seconds for web search, <1 second for trends
- **Rate limits:** Groq free tier has 100k tokens/day; Tavily has generous free tier
- **Database:** Supabase free tier suitable for development/testing

## Security

- **JWT Authentication:** All API endpoints require valid JWT token
- **Row-Level Security:** Supabase RLS ensures users only access their data
- **CORS:** Configured to allow frontend origin only
- **Environment variables:** Sensitive keys stored in `.env` (not in git)

## Future Enhancements

- [ ] Conversation search/filtering
- [ ] Message editing and deletion
- [ ] User preferences and settings
- [ ] Multiple conversation threads
- [ ] Export conversation history
- [ ] Custom system prompts
- [ ] Rate limiting per user
- [ ] Analytics dashboard

## License

MIT

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Built with ❤️ using React, FastAPI, and LangChain**

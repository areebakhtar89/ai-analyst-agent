# AI Analyst Agent - Project Documentation

## Overview

The AI Analyst Agent is a conversational multi-agent analytics system that transforms natural language questions into SQL queries, executes them against a database, and provides intelligent visualizations and insights. The system uses LangGraph for orchestration and combines multiple specialized agents to deliver comprehensive data analysis.     

## Technical Stack

### Python Version
- **Python 3.11.0**

### Core Dependencies
```
fastapi               - Web framework for API backend
uvicorn               - ASGI server for FastAPI
streamlit             - Frontend UI framework
pandas                - Data manipulation and analysis
duckdb                - In-process SQL database
plotly                - Interactive visualizations
python-dotenv         - Environment variable management
langchain             - LLM orchestration framework
langchain-google-genai - Google AI integration
langgraph             - Multi-agent workflow orchestration
sentence-transformers - Text embeddings
scikit-learn          - Machine learning utilities
groq                  - LLM API client (in llm.py)
```

### LLM Configuration
- **Primary Model**: Llama 3.3 70B Versatile (via Groq API)
- **Temperature**: 0.2 (lower for better SQL generation)
- **Max Tokens**: 1500
- **Streaming**: Disabled for agent workflows

### Sentence Transformer
- **Model**: all-MiniLM-L6-v2
- **Purpose**: Table retrieval and semantic search

## Project Structure

```
ai-analyst-agent/
├── app/
│   ├── agents/                    # Multi-agent system
│   │   ├── __init__.py
│   │   ├── analysis.py           # Analysis agent for insights generation
│   │   ├── contextualizer.py    # Context and memory management
│   │   ├── error_fix_agent.py    # SQL error correction and retry logic
│   │   ├── graph.py              # LangGraph workflow orchestration
│   │   ├── planner.py            # Query planning and strategy
│   │   ├── sql_agent.py          # SQL generation from natural language
│   │   ├── sql_node.py           # SQL execution node
│   │   ├── state.py              # Shared state schema
│   │   └── visualization.py      # Chart generation and visualization
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py               # FastAPI backend endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py           # Database connection and utilities
│   │   ├── generate_data.py      # Sample data generation
│   │   ├── init_db.py            # Database initialization
│   │   ├── llm.py                # LLM client configuration
│   │   ├── logging_config.py     # Centralized logging setup
│   │   ├── schema_metadata.py    # Database schema information
│   │   ├── table_retriever.py    # Table and column discovery
│   │   ├── test_agent.py         # Agent testing utilities
│   │   ├── test_graph.py         # Workflow testing
│   │   └── test_llm.py           # LLM testing
│   ├── ui/
│   │   └── app.py                # Streamlit frontend application
│   ├── .streamlit/
│   │   └── config.toml           # Streamlit configuration
│   └── __init__.py
├── data/                         # Data storage
│   ├── chart.html with data type bar
│   ├── customers.csv
│   ├── orders.csv
│   └── order_items.csv
├── tests/                        # Test suite
├── .gitignore
├── notes.txt                     # Development notes
├── python                        # Python executable reference
├── readme.md                     # Basic project overview
├── requirements.txt              # Python dependencies
└── test-p.py                     # Test file
```

## Agentic Flow Architecture

### Workflow Overview
The system uses a LangGraph-based multi-agent architecture with the following flow:

```
User Question → Contextualizer → Planner → SQL Agent → Analysis → Visualization → Results
                                    ↓
                              Error Fix Agent (retry loop)
```

### Agent Responsibilities

#### 1. Contextualizer Agent
- **Purpose**: Refines user questions with conversational memory
- **Input**: User question + session history
- **Output**: Contextualized question with relevant background
- **Key Features**: 
  - Maintains session memory
  - Handles follow-up questions
  - Preserves conversation context

#### 2. Planner Agent
- **Purpose**: Creates analysis strategy and execution plan
- **Input**: Contextualized question
- **Output**: Structured analysis plan
- **Key Features**:
  - Determines required data sources
  - Plans visualization approach
  - Identifies necessary aggregations

#### 3. SQL Agent
- **Purpose**: Generates SQL queries from natural language
- **Input**: Analysis plan and question
- **Output**: SQL query string
- **Key Features**:
  - Schema-aware query generation
  - Handles complex joins and aggregations
  - Optimizes for DuckDB syntax

#### 4. Error Fix Agent
- **Purpose**: Corrects SQL errors and retries failed queries
- **Input**: Failed SQL query + error message
- **Output**: Corrected SQL query
- **Key Features**:
  - Automated error detection
  - Query correction logic
  - Retry mechanism (max 2 attempts)

#### 5. Analysis Agent
- **Purpose**: Extracts business insights from query results
- **Input**: Query results + original question
- **Output**: Structured insights and observations
- **Key Features**:
  - Pattern recognition
  - Statistical analysis
  - Business context interpretation

#### 6. Visualization Agent
- **Purpose**: Creates appropriate charts and visualizations
- **Input**: Query results + analysis insights
- **Output**: Interactive Plotly charts
- **Key Features**:
  - Smart chart type selection
  - Dynamic axis assignment
  - Responsive design

### State Management
The `AgentState` class maintains workflow context:

```python
class AgentState(TypedDict):
    question: str                    # User input
    context: str                     # Conversational context
    structured_memory: Dict[str, Any] # Session memory
    plan: str                        # Planner output
    sql: str                         # Generated SQL
    result: List[Dict[str, Any]]     # Query results
    insights: str                    # Analysis output
    chart_path: str                  # Visualization file path
    chart_type: str                  # Chart type
    error: str                       # Error messages
    retry_count: int                 # Retry counter
```

## API Architecture

### FastAPI Backend (`app/api/main.py`)

#### Endpoints
- **GET /**: Health check endpoint
- **GET /query/stream**: SSE streaming endpoint for real-time progress
- **POST /query**: Standard query endpoint (legacy compatibility)

#### Session Management
- In-memory session storage
- Maintains conversation history
- Structured memory for follow-up questions
- Automatic session cleanup

#### Streaming Features
- Real-time agent progress updates
- Progressive result delivery
- Error handling and recovery

### Frontend Architecture (`app/ui/app.py`)

#### Streamlit Configuration
- Dark theme with custom styling
- IBM Plex font family
- Responsive layout
- Real-time updates via SSE

#### Key Features
- **Interactive Chat Interface**: Natural language input
- **Live Agent Pipeline**: Visual progress tracking
- **Dynamic Chart Switching**: Client-side chart type changes
- **Data Table Viewer**: Paginated result display
- **SQL Query Explorer**: Expandable query display
- **Download Capabilities**: Charts and CSV exports
- **Session Management**: New session creation

#### Chart Types Supported
- Bar charts (grouped/stacked)
- Line charts (with markers)
- Scatter plots
- Pie charts (with percentages)
- Area charts

## Database Configuration

### DuckDB Integration
- **Database**: DuckDB (in-process analytical database)
- **Data Files**: CSV files in `/data` directory
- **Schema**: Auto-detected from CSV headers
- **Performance**: Optimized for analytical queries

### Data Schema
- **customers.csv**: Customer information and demographics
- **orders.csv**: Order transactions and metadata
- **order_items.csv**: Line items and product details

## Deployment and Configuration

### Environment Variables
```bash
GROQ_API_KEY=your_groq_api_key_here
```

### Running the Application

#### Backend (FastAPI)
```bash
cd app/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend (Streamlit)
```bash
cd app/ui
streamlit run app.py --server.port 8501
```

### Development Setup
1. Create virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Initialize database: `python app/core/init_db.py`
5. Run backend and frontend services

## Key Features and Capabilities

### Natural Language Processing
- Complex query understanding
- Context-aware responses
- Follow-up question handling
- Multi-turn conversations

### SQL Generation
- Schema-aware query construction
- Complex joins and aggregations
- Error detection and correction
- Performance optimization

### Visualization Intelligence
- Automatic chart type selection
- Smart axis assignment
- Color coding for categories
- Interactive and responsive designs

### Error Handling
- Automatic SQL error correction
- Retry mechanisms
- Graceful degradation
- User-friendly error messages

## Security Considerations

### Current Implementation
- API key management via environment variables
- Input validation and sanitization
- SQL injection prevention through parameterized queries
- Error message sanitization

### Recommendations for Production
- Add authentication and authorization
- Implement rate limiting
- Add audit logging
- Secure session management
- Input validation enhancements

## Performance Optimization

### Current Optimizations
- In-memory session storage
- Efficient SQL generation
- Streaming responses
- Client-side chart regeneration

### Future Improvements
- Database connection pooling
- Query result caching
- Horizontal scaling support
- Database query optimization

## Testing

### Test Coverage
- Agent unit tests (`test_agent.py`)
- Workflow integration tests (`test_graph.py`)
- LLM integration tests (`test_llm.py`)
- API endpoint testing

### Test Execution
```bash
python -m pytest tests/
```

## Monitoring and Logging

### Logging Configuration
- Centralized logging setup (`logging_config.py`)
- Structured log format
- Agent activity tracking
- Performance metrics

### Key Metrics
- Query execution time
- Agent success rates
- Error frequencies
- User interaction patterns

## Future Enhancements

### Planned Features
- Multi-database support
- Advanced visualization options
- Custom agent creation
- Export to multiple formats
- Integration with external data sources

### Technical Improvements
- Microservices architecture
- Container-based deployment
- Database migration support
- Advanced caching strategies
- Real-time collaboration features

## Contributing Guidelines

### Code Standards
- Follow PEP 8 guidelines
- Use type hints consistently
- Add comprehensive docstrings
- Implement proper error handling

### Development Workflow
1. Create feature branch
2. Add tests for new functionality
3. Update documentation
4. Submit pull request for review

## Support and Maintenance

### Common Issues
- API key configuration problems
- Database connection issues
- Frontend-backend connectivity
- Memory management in long sessions

### Troubleshooting Steps
1. Check environment variables
2. Verify database initialization
3. Review log files
4. Test individual components

---

**Last Updated**: March 2026
**Version**: 1.0.0
**Maintainer**: AI Analyst Agent Development Team

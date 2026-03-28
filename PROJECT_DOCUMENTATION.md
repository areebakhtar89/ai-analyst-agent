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
mysql-connector-python - MySQL database connector
psycopg2-binary       - PostgreSQL database connector
requests              - HTTP client for API calls
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
│   │   ├── connectors.py         # Multi-database connector layer
│   │   ├── database.py           # Database connection and utilities
│   │   ├── generate_data.py      # Sample data generation
│   │   ├── init_db.py            # Database initialization
│   │   ├── llm.py                # LLM client configuration
│   │   ├── logging_config.py     # Centralized logging setup
│   │   ├── schema_metadata.py    # Database schema information
│   │   ├── schema_store.py       # Live schema and metadata management
│   │   ├── table_retriever.py    # Table and column discovery
│   │   ├── test_agent.py         # Agent testing utilities
│   │   ├── test_graph.py         # Workflow testing
│   │   └── test_llm.py           # LLM testing
│   ├── Scripts/                  # Database setup scripts
│   │   ├── setup_kaggle.py       # Download Olist dataset from Kaggle
│   │   ├── setup_mysql.py        # Create MySQL database and load data
│   │   └── test_connection.py    # Database connection testing
│   ├── tools/
│   │   ├── __init__.py
│   │   └── sql_tool.py           # Safe SQL execution tool
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py                # Main Streamlit application
│   │   └── pages/
│   │       └── connect.py        # Database connection and schema configuration
│   ├── .streamlit/
│   │   └── config.toml           # Streamlit configuration
│   └── __init__.py
├── data/                         # Data storage
│   ├── chart.html with data type bar
│   ├── customers.csv
│   ├── orders.csv
│   ├── order_items.csv
│   └── schema_configs/           # Saved schema configurations
├── tests/                        # Test suite
├── .gitignore
├── notes.txt                     # Development notes
├── python                        # Python executable reference
├── readme.md                     # Basic project overview
├── requirements.txt              # Python dependencies
├── requirements1.txt             # Alternative dependencies
├── test-p.py                     # Test file
└── test.ipynb                    # Jupyter notebook
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

#### Core Endpoints
- **GET /**: Health check endpoint
- **GET /query/stream**: SSE streaming endpoint for real-time progress
- **POST /query**: Standard query endpoint (legacy compatibility)

#### Database Connection Endpoints
- **POST /connect**: Establish database connection
  ```json
  {
    "type": "mysql",
    "host": "localhost",
    "port": 3306,
    "user": "username",
    "password": "password",
    "database": "database_name"
  }
  ```
- **POST /disconnect**: Close active connection and reset schema
- **GET /schema**: Retrieve current database schema
- **POST /schema/test**: Test database connection

#### Schema Management Endpoints
- **GET /schema/saved**: List all saved schema configurations
- **POST /schema/load**: Load a saved configuration
- **POST /schema/table/select**: Toggle table selection
  ```json
  {
    "table": "customers",
    "selected": true
  }
  ```
- **POST /schema/table/describe**: Save table and column descriptions
  ```json
  {
    "table": "customers",
    "description": "Customer information and demographics",
    "columns": {
      "customer_id": "Unique customer identifier",
      "customer_city": "Customer's city of residence"
    }
  }
  ```
- **POST /schema/ai/rewrite**: Generate AI-enhanced descriptions
  ```json
  {
    "type": "table|column",
    "table": "customers",
    "column": "customer_id",
    "current_description": "Customer ID"
  }
  ```

#### Session Management
- In-memory session storage
- Maintains conversation history
- Structured memory for follow-up questions
- Automatic session cleanup
- Connection state persistence

#### Streaming Features
- Real-time agent progress updates
- Progressive result delivery
- Error handling and recovery
- Connection status updates

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

### Connection Management UI (`app/ui/pages/connect.py`)

#### Overview
The connection page provides a 3-step wizard for database setup and schema configuration:

#### Step 1: Database Connection
- **Database Type Selection**: MySQL, PostgreSQL, SQLite, DuckDB
- **Connection Form**: Dynamic fields based on database type
- **Connection Testing**: Real-time validation with error feedback
- **Saved Configurations**: Quick-load previously saved connections

#### Step 2: Table Selection
- **Schema Discovery**: Automatic table and column detection
- **Interactive Selection**: Choose which tables to expose to AI
- **Table Metadata**: Display row counts and column information
- **Bulk Operations**: Select/deselect all tables

#### Step 3: Schema Description
- **Table Descriptions**: Plain-English descriptions for business context
- **Column Descriptions**: Field-level documentation
- **AI Enhancement**: Automatic description generation using LLM
- **Save Management**: Individual and bulk save operations

#### Key Features
- **Visual Progress Indicator**: Step-by-step navigation
- **Real-time Validation**: Immediate connection feedback
- **AI-Powered Descriptions**: One-click description generation
- **Configuration Persistence**: Save and reuse database setups
- **Fallback Support**: Return to default Olist database

## Database Configuration

### Multi-Database Support
The system now supports multiple database types through a unified connector layer:

#### Supported Databases
- **MySQL**: Production-ready with mysql-connector-python
- **PostgreSQL**: Full support via psycopg2-binary
- **SQLite**: File-based database for local development
- **DuckDB**: In-memory analytical database (default for demos)

#### Connector Architecture (`app/core/connectors.py`)
- **Unified API**: Single `run_query()` function for all database types
- **Type Normalization**: Automatic conversion of database-specific types to JSON-safe Python types
- **Connection Management**: Secure connection handling with proper cleanup
- **Schema Discovery**: Automatic table and column metadata retrieval
- **Error Handling**: Database-specific error mapping

#### Connection Configuration
```python
# MySQL Example
config = {
    "type": "mysql",
    "host": "localhost",
    "port": 3306,
    "user": "username",
    "password": "password",
    "database": "database_name"
}

# PostgreSQL Example
config = {
    "type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "user": "username",
    "password": "password",
    "database": "database_name"
}

# SQLite Example
config = {
    "type": "sqlite",
    "file": "path/to/database.db"
}

# DuckDB Example
config = {
    "type": "duckdb",
    "file": "path/to/database.duckdb"  # or ":memory:"
}
```

### Schema Store System (`app/core/schema_store.py`)
#### Overview
The schema store provides persistent metadata management for database connections:
- **Live Schema Storage**: In-memory cache of database structure
- **User Descriptions**: Plain-English descriptions for tables and columns
- **Persistence**: Automatic saving/loading of configurations to JSON
- **Version Safety**: Merges saved descriptions with live schema changes

#### Key Features
- **Table Selection**: Choose which tables are available for NL2SQL
- **AI-Enhanced Descriptions**: Generate descriptions using LLM
- **Configuration Management**: Save and reuse database setups
- **Context Building**: Create schema context for agent prompts

#### Storage Location
```
data/schema_configs/
├── mysql_olist_db.json
├── postgresql_analytics.json
└── duckdb_demo.json
```

#### Schema Store API
```python
# Core operations
refresh_schema()           # Load schema from active database
reset_schema()            # Clear schema and fall back to defaults
get_schema_context()       # Build LLM context string
get_selected_tables()     # Get user-selected tables

# Metadata operations
save_table_metadata()     # Save table/column descriptions
set_table_selected()       # Toggle table selection
list_saved_configs()       # List all saved configurations
```

### Legacy DuckDB Integration
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
# LLM Configuration
GROQ_API_KEY=your_groq_api_key_here

# Database Connection (optional - for UI connection)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=olist_db

# Kaggle Data Download (optional)
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_API_KEY=your_kaggle_api_key

# PostgreSQL (optional)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DATABASE=database_name
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
3. Set up environment variables (see .env section below)
4. Initialize database: `python app/core/init_db.py`
5. Run backend and frontend services

### Database Setup Scripts

#### Kaggle Data Download (`app/Scripts/setup_kaggle.py`)
Downloads the Olist Brazilian E-Commerce dataset from Kaggle:
```bash
# Set Kaggle credentials in .env
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_API_KEY=your_kaggle_api_key

# Run the script
python app/Scripts/setup_kaggle.py
```

**Features:**
- Automatic credential loading from .env
- Downloads to `data/raw/` directory
- Validates expected files
- Progress tracking and error handling

#### MySQL Database Setup (`app/Scripts/setup_mysql.py`)
Creates MySQL database and loads Olist data:
```bash
# Set MySQL credentials in .env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=olist_db

# Run the script
python app/Scripts/setup_mysql.py
```

**Features:**
- Creates `olist_db` database with proper schema
- Loads 9 tables with correct data types
- Handles foreign key relationships
- Progress reporting and error handling

#### Connection Testing (`app/Scripts/test_connection.py`)
Validates database connectivity:
```bash
python app/Scripts/test_connection.py
```

**Features:**
- Tests all supported database types
- Validates connection parameters
- Reports schema information
- Performance metrics

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

## Tools and Utilities

### SQL Execution Tool (`app/tools/sql_tool.py`)
Provides a safe interface for executing read-only SQL queries:

#### Features
- **Safety First**: Blocks destructive operations (DROP, DELETE, UPDATE, INSERT, etc.)
- **Error Handling**: Comprehensive error reporting and logging
- **Type Safety**: Automatic type conversion and normalization
- **Security**: SQL injection prevention through parameterized queries

#### Usage
```python
from app.tools.sql_tool import execute_sql

# Execute a safe query
result = execute_sql("SELECT * FROM customers LIMIT 10")
if "error" in result:
    print(f"Query failed: {result['error']}")
else:
    print(f"Returned {len(result)} rows")
```

### Database Connectors (`app/core/connectors.py`)
Unified database connector layer supporting multiple database types:

#### Supported Operations
- `run_query(config, sql)`: Execute SQL and return DataFrame
- `test_connection(config)`: Test database connectivity
- `get_schema(config)`: Retrieve database schema

#### Type Normalization
- Decimal → float
- timedelta → string
- NaN → None (JSON-safe)
- Database-specific type handling

## Future Enhancements

### Planned Features
- Multi-database support ✅ **COMPLETED**
- Advanced visualization options
- Custom agent creation
- Export to multiple formats
- Integration with external data sources
- Schema management system ✅ **COMPLETED**
- Connection management UI ✅ **COMPLETED**

### Technical Improvements
- Microservices architecture
- Container-based deployment
- Database migration support
- Advanced caching strategies
- Real-time collaboration features
- Enhanced security with authentication
- Performance monitoring and metrics

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
**Version**: 2.0.0
**Maintainer**: AI Analyst Agent Development Team

## Recent Updates (v2.0.0)

### Major Enhancements
- ✅ **Multi-Database Support**: Full support for MySQL, PostgreSQL, SQLite, and DuckDB
- ✅ **Schema Management System**: Persistent schema configurations with AI-enhanced descriptions
- ✅ **Connection Management UI**: 3-step wizard for database setup and configuration
- ✅ **Enhanced API**: New endpoints for database and schema management
- ✅ **Setup Scripts**: Automated database setup and data loading utilities
- ✅ **Tools Framework**: Safe SQL execution with comprehensive error handling

### Technical Improvements
- Unified connector architecture with type normalization
- In-memory schema store with disk persistence
- AI-powered schema description generation
- Enhanced error handling and logging
- Comprehensive test coverage

### New Components
- `app/core/connectors.py` - Multi-database connector layer
- `app/core/schema_store.py` - Schema and metadata management
- `app/ui/pages/connect.py` - Database connection UI
- `app/tools/sql_tool.py` - Safe SQL execution tool
- `app/Scripts/` - Database setup utilities

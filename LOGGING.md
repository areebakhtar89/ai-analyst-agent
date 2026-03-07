# Logging Configuration

## Overview

The AI Analyst Agent uses a comprehensive logging system that tracks all activities across the application. Logs are essential for debugging, monitoring, and auditing the system's behavior.

## Log File Locations

### Default Location
- **Directory**: `logs/` (in project root)
- **Main Log**: `logs/ai_analyst_YYYYMMDD.log`
- **Error Log**: `logs/ai_analyst_errors_YYYYMMDD.log`
- **Rotated Logs**: `logs/ai_analyst_YYYYMMDD.log.1`, `.2`, etc.

### Session-Based Logging (NEW!)
- **Session Log**: `logs/ai_analyst_session_{SESSION_ID}_YYYYMMDD.log`
- **Session Error Log**: `logs/ai_analyst_errors_session_{SESSION_ID}_YYYYMMDD.log`

### Configurable via Environment Variables
```bash
# Set custom log directory
export AI_ANALYST_LOG_DIR="/path/to/custom/logs"

# Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export AI_ANALYST_LOG_LEVEL="DEBUG"

# Set log retention period in days
export AI_ANALYST_LOG_RETENTION_DAYS="30"

# Set maximum log file size in MB (default: 50MB)
export AI_ANALYST_MAX_LOG_SIZE_MB="100"

# Set number of backup files to keep (default: 5)
export AI_ANALYST_BACKUP_COUNT="10"
```

## Usage Examples

### Standard Date-Based Logging
```python
from app.core.logging_config import setup_logger

logger = setup_logger(__name__)
logger.info("This uses date-based logging")
```

### Session-Based Logging
```python
from app.core.logging_config import setup_session_logger

# With session ID
logger = setup_session_logger(__name__, session_id="user123abc")
logger.info("This goes to session-specific log file")

# Without session ID (falls back to date-based)
logger = setup_session_logger(__name__)
logger.info("This uses date-based logging when no session provided")
```

## Log File Management

### Daily Rotation with Size Limits
- **Format**: `ai_analyst_YYYYMMDD.log` (one file per day)
- **Size Limit**: 50MB by default (configurable)
- **Rotation**: When file reaches size limit, it creates `.1`, `.2`, etc.
- **Example**: 
  ```
  ai_analyst_20260307.log      # Current day's log
  ai_analyst_20260307.log.1    # First backup
  ai_analyst_20260307.log.2    # Second backup
  ai_analyst_20260306.log      # Previous day's log
  ```

### Benefits of This Approach
- **Easy Tracking**: One file per day makes it simple to find logs
- **Size Control**: Automatic rotation prevents huge files
- **Historical Access**: Keep several days of logs with rotation
- **Error Isolation**: Separate error files for quick debugging

## Log Levels

- **DEBUG**: Detailed information for debugging (function calls, variable values)
- **INFO**: General information about application flow (agent activities, query execution)
- **WARNING**: Unexpected behavior that doesn't stop the application
- **ERROR**: Serious issues that may cause partial failures
- **CRITICAL**: Critical errors that may crash the application

## Automatic Log Cleanup

The system automatically cleans up old log files based on the retention period:
- **Default**: 7 days
- **Configurable**: Via `AI_ANALYST_LOG_RETENTION_DAYS` environment variable
- **Trigger**: Automatically runs when the logging module is imported

## What Gets Logged

### Database Operations
- Database initialization and table creation
- SQL query execution with timing and row counts
- Connection management and errors

### Agent Activities
- SQL generation and refinement
- Data analysis and insight generation
- Chart creation and configuration
- API request/response handling

### System Events
- Application startup and shutdown
- Session management
- LLM interactions
- File operations

## Viewing Logs

### Real-time Monitoring
```bash
# Follow the latest log file
tail -f logs/ai_analyst_$(ls -t logs/ai_analyst_*.log | head -1 | cut -d'_' -f2-)

# View error logs only
tail -f logs/ai_analyst_errors_*.log
```

### Search Logs
```bash
# Search for specific agent activities
grep "SQL Agent" logs/ai_analyst_*.log

# Search for errors
grep "ERROR" logs/ai_analyst_*.log

# Search for specific queries
grep "Executing SQL" logs/ai_analyst_*.log
```

## Log Analysis

### Common Patterns
- **Query Performance**: Look for "Query executed" messages with timing
- **Agent Flow**: Follow "Starting" and "completed" messages for each agent
- **Error Tracking**: Check error logs for critical issues
- **Session Tracking**: Monitor session creation and memory updates

### Performance Monitoring
```bash
# Extract query execution times
grep "Query executed" logs/ai_analyst_*.log | grep -o "([0-9.]*s)" | sort -n

# Count agent activities
grep -c "Agent.*Starting" logs/ai_analyst_*.log
```

## Troubleshooting

### Common Issues

1. **Log Files Not Created**
   - Check write permissions to log directory
   - Verify `AI_ANALYST_LOG_DIR` environment variable
   - Ensure application has sufficient disk space

2. **Too Many Log Files**
   - Reduce `AI_ANALYST_LOG_RETENTION_DAYS`
   - Manually clean old files: `rm logs/ai_analyst_*.log`

3. **Missing Debug Information**
   - Set `AI_ANALYST_LOG_LEVEL=DEBUG`
   - Restart the application

### Manual Log Management
```python
from app.core.logging_config import get_log_info, cleanup_old_logs

# Get current log configuration
print(get_log_info())

# Manually trigger cleanup
cleanup_old_logs()
```

## Integration with Monitoring Tools

The structured log format makes it easy to integrate with monitoring tools:

- **ELK Stack**: Use filebeat to ship logs to Elasticsearch
- **Splunk**: Configure file-based inputs
- **CloudWatch**: Use AWS CloudWatch agent
- **Prometheus**: Use promtail for log aggregation

Example log parsing configuration:
```
Pattern: %(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s
Fields: timestamp, logger_name, level, function, line_number, message
```

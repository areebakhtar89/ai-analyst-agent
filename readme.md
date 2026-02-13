## System Architecture

The system uses a LangGraph-based multi-agent architecture where each agent performs a specialized task—planning, SQL generation, analysis, and visualization—while sharing a common execution state.

flowchart LR
    U[User] --> P[Planner Agent]
    P --> S[SQL Agent]
    S --> DB[(Database)]
    DB --> A[Analysis Agent]
    A --> V[Visualization Agent]
    V --> O[Insights + Chart]


flowchart TD

    A[User Question] --> B[Streamlit UI]

    B --> C[FastAPI Backend]

    C --> D[LangGraph Orchestrator]

    D --> E[Planner Agent]
    E --> F[SQL Agent]

    F --> G[SQL Tool]
    G --> H[(DuckDB Database)]

    H --> F
    F --> I[Analysis Agent]
    I --> J[Visualization Agent]

    J --> K[Plotly Chart]
    I --> L[Insights Text]

    K --> C
    L --> C

    C --> B
    B --> M[User Sees Chart + Insights]
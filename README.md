# butlerMCP
Contains tools to achieve day to day tasks


## FastMCP:
the canonical Python SDK for Model Context Protocol; supports HTTP transport + ASGI mounts (good for Uvicorn/Starlette). 
FastMCP
+2
PyPI
+2

ti run the server 
uvicorn server:app --host 127.0.0.1 --port 8080

optional 
uvicorn server:app --host 127.0.0.1 --port 8080 --timeout-waiter=5 --timeout-keep-alive=30

## HTTP transport via ASGI:
recommended over legacy SSE; clean app = mcp.http_app() for Uvicorn. 
FastMCP

## Gmail API with OAuth scopes:
start with gmail.readonly, then gmail.modify for labeling/deleting. 
Google for Developers
+1


gmail-mcp/
├── server.py # Main entry point (FastMCP + Starlette + Uvicorn)
├── gmail_client.py # Handles Gmail API authentication and email actions
├── rules.py # Contains cleanup/filtering logic or rules
├── requirements.txt # Python dependencies
├── .env.example # Example environment variables file
├── README.md # Project documentation
└── data/ # Local storage for cached or processed data
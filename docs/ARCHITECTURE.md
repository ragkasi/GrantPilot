# GrantPilot Architecture

## Overview

GrantPilot is split into three main systems:

1. Frontend web app
2. Backend API
3. Optional MCP tool server

The frontend handles user interaction. The backend owns authentication, document processing, database access, AI workflows, scoring, and report generation. The MCP server exposes grant-specific tools for agent workflows.

## System Diagram

```txt
User
 |
 v
Next.js Frontend
 |
 v
FastAPI Backend
 |
 |-- Postgres / pgvector
 |-- Supabase Storage or S3
 |-- AI Provider API
 |-- PDF Parser
 |-- Report Generator
 |
 v
grant-context-mcp
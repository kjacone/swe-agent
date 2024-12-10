from typing import Annotated, Any, Literal, TypedDict, List, Dict, Optional, cast
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from shared.utils import load_chat_model
from swe_graph.analyser_sub_graph.state import AnalyzerState
from swe_graph.configuration import AgentConfiguration
from swe_graph.review_and_documentation_sub_graph.state import (
    APIEndpoint,
    DocumentationSection,
    DocumentationState,
)


async def generate_api_docs(state: DocumentationState) -> Dict[str, Any]:
    """Generate API documentation from code base."""
    try:
        api_docs = {}
        base_path = "docs/api"

        # Extract API endpoints from codebase
        for module, code_info in state.code_base.items():
            if "api" in module:
                endpoint = APIEndpoint(
                    path=f"/api/{module}",
                    method="POST",  # Default method, should be extracted from code
                    description=f"API endpoint for {module}",
                    parameters=[
                        {
                            "name": "param1",
                            "type": "string",
                            "required": True,
                            "description": "Parameter description",
                        }
                    ],
                    responses={
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {"schema": {"type": "object"}}
                            },
                        },
                        "400": {"description": "Bad request"},
                    },
                    examples=[
                        {
                            "request": {"param1": "example"},
                            "response": {"status": "success"},
                        }
                    ],
                )
                api_docs[module] = endpoint

        # Generate OpenAPI specification
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {"title": "API Documentation", "version": "1.0.0"},
            "paths": {
                endpoint.path: {
                    endpoint.method.lower(): {
                        "summary": endpoint.description,
                        "parameters": endpoint.parameters,
                        "responses": endpoint.responses,
                    }
                }
                for endpoint in api_docs.values()
            },
        }

        return {
            "api_docs": api_docs,
            "architecture_docs": {
                "openapi": DocumentationSection(
                    id="openapi_spec",
                    title="OpenAPI Specification",
                    content=str(openapi_spec),
                    path=os.path.join(base_path, "openapi.yaml"),
                    format="yaml",
                    status="draft",
                )
            },
            "next_node": "generate_user_guides",
        }
    except Exception as e:
        return {
            "errors": [f"Error in API documentation generation: {str(e)}"],
            "next_node": "human_review",
        }


async def generate_user_guides(state: DocumentationState) -> Dict[str, Any]:
    """Generate user guides and documentation."""
    try:
        base_path = "docs/guides"
        user_guides = {
            "getting_started": DocumentationSection(
                id="getting_started",
                title="Getting Started Guide",
                content="""
# Getting Started

## Introduction
Welcome to our application! This guide will help you get started with using our platform.

## Installation
1. Clone the repository
2. Install dependencies
3. Configure environment
4. Start the application

## Basic Usage
Here are the basic operations you can perform...
                """,
                path=os.path.join(base_path, "getting-started.md"),
                format="md",
                status="draft",
            ),
            "user_manual": DocumentationSection(
                id="user_manual",
                title="User Manual",
                content="""
# User Manual

## Features
Detailed explanation of all features...

## Workflows
Common workflow examples...

## Troubleshooting
Common issues and solutions...
                """,
                path=os.path.join(base_path, "user-manual.md"),
                format="md",
                status="draft",
            ),
        }

        return {"user_guides": user_guides, "next_node": "generate_developer_docs"}
    except Exception as e:
        return {
            "errors": [f"Error in user guide generation: {str(e)}"],
            "next_node": "human_review",
        }


async def generate_developer_docs(state: DocumentationState) -> Dict[str, Any]:
    """Generate developer documentation."""
    try:
        base_path = "docs/developer"
        developer_docs = {
            "setup": DocumentationSection(
                id="dev_setup",
                title="Development Environment Setup",
                content="""
# Development Setup

## Prerequisites
- Required tools and versions
- System requirements

## Local Development
1. Setting up development environment
2. Running tests
3. Code style guidelines

## Contributing
- Contribution guidelines
- Pull request process
- Code review checklist
                """,
                path=os.path.join(base_path, "setup.md"),
                format="md",
                status="draft",
            ),
            "architecture": DocumentationSection(
                id="architecture",
                title="System Architecture",
                content="""
# System Architecture

## Overview
High-level architecture overview...

## Components
Detailed component descriptions...

## Data Flow
Data flow diagrams and explanations...
                """,
                path=os.path.join(base_path, "architecture.md"),
                format="md",
                status="draft",
            ),
        }

        return {
            "developer_docs": developer_docs,
            "next_node": "generate_deployment_guides",
        }
    except Exception as e:
        return {
            "errors": [f"Error in developer documentation generation: {str(e)}"],
            "next_node": "human_review",
        }


async def generate_deployment_guides(state: DocumentationState) -> Dict[str, Any]:
    """Generate deployment documentation."""
    try:
        base_path = "docs/deployment"
        deployment_guides = {
            "deployment": DocumentationSection(
                id="deployment_guide",
                title="Deployment Guide",
                content="""
# Deployment Guide

## Environments
- Development
- Staging
- Production

## Deployment Process
1. Build process
2. Environment configuration
3. Deployment steps
4. Verification

## Monitoring
- Logging setup
- Metrics collection
- Alert configuration
                """,
                path=os.path.join(base_path, "deployment.md"),
                format="md",
                status="draft",
            ),
            "operations": DocumentationSection(
                id="operations_guide",
                title="Operations Guide",
                content="""
# Operations Guide

## Maintenance
- Routine maintenance tasks
- Backup procedures
- Update processes

## Troubleshooting
- Common issues
- Debug procedures
- Support escalation
                """,
                path=os.path.join(base_path, "operations.md"),
                format="md",
                status="draft",
            ),
        }

        return {
            "deployment_guides": deployment_guides,
            "next_node": "compile_release_notes",
        }
    except Exception as e:
        return {
            "errors": [f"Error in deployment guide generation: {str(e)}"],
            "next_node": "human_review",
        }


async def compile_release_notes(state: DocumentationState) -> Dict[str, Any]:
    """Compile release notes and changelog."""
    try:
        release_notes = [
            {
                "version": "1.0.0",
                "date": "2024-12-10",
                "changes": [{"type": "feature", "description": "Initial release"}],
                "path": "docs/changelog/v1.0.0.md",
            }
        ]

        return {"release_notes": release_notes, "next_node": "review_documentation"}
    except Exception as e:
        return {
            "errors": [f"Error in release notes compilation: {str(e)}"],
            "next_node": "human_review",
        }


async def review_documentation(state: DocumentationState) -> Dict[str, Any]:
    """Review and finalize documentation."""
    try:
        # Collect all documentation sections
        all_docs = {
            **state.user_guides,
            **state.developer_docs,
            **state.deployment_guides,
            **state.architecture_docs,
        }

        # Update status for reviewed docs
        for doc_id, doc in all_docs.items():
            doc.status = "reviewed"

        return {
            "user_guides": state.user_guides,
            "developer_docs": state.developer_docs,
            "deployment_guides": state.deployment_guides,
            "architecture_docs": state.architecture_docs,
            "next_node": "human_review",
        }
    except Exception as e:
        return {
            "errors": [f"Error in documentation review: {str(e)}"],
            "next_node": "human_review",
        }

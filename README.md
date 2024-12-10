# LangGraph Software Engineering Agent

A powerful Software Engineering Agent that assists in the complete software development lifecycle - from requirements analysis to code generation and documentation.

## System Architecture

The following diagram illustrates the complete workflow of the Software Engineering Agent:



![Software Engineering Agent Workflow](https://www.mermaidchart.com/raw/95e8945d-928e-48ff-82bf-9e92d979b4a6?theme=light&version=v0.1&format=svg)

## Key Components

The project consists of four main graphs:

### 1. Analyzer Graph
- Processes natural language project requirements
- Extracts and categorizes requirements
- Creates detailed technical specifications
- Designs system architecture
- Generates project structure and setup

### 2. Codebase Graph
- Manages monorepo structure and setup
- Handles workspace and dependency management
- Analyzes repository structure
- Maintains code index and configurations

### 3. Development Graph
- Manages the software development workflow
- Routes and processes development tasks
- Handles code implementation and review
- Validates changes against requirements

### 4. Architect Graph
- Validates solutions against specifications
- Designs solution architecture
- Generates and refactors code
- Reviews implementations

## Getting Started

### Prerequisites
- [LangGraph Studio](https://github.com/langchain-ai/langgraph-studio) installed
- Python 3.8 or higher
- Git
- Jupyter Notebook (for running examples)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/swe-agent.git
cd swe-agent
```

2. Create and configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running in Jupyter Notebook

You can run the agent directly in a Jupyter notebook (`test.ipynb`). Here's an example:

```python
# Import necessary components
from langchain.schema import HumanMessage
from src.analyzer_graph import analyzer_graph

# Initialize the graph
app = analyzer_graph

# Configure the run
config = {
    "thread_id": "1",
    "checkpoint_ns": "test_namespace",
    "checkpoint_id": "1",
}

# Define input
inputs = {"messages": [HumanMessage(content="build ecommerce site")]}

# Run the graph
await app.ainvoke(inputs, config=config)
```

### Using Python API

#### 1. Requirements Analysis
```python
from src.analyzer_graph import analyze_requirements

requirements = """
Your project requirements in natural language
"""
analysis = analyze_requirements(requirements)
```

#### 2. Project Setup
```python
from src.codebase_graph import setup_project

project_config = {
    "name": "your-project",
    "structure": analysis.recommended_structure
}
setup_project(project_config)
```

#### 3. Development
```python
from src.development_graph import process_task

task = {
    "type": "feature",
    "description": "Implement user authentication"
}
result = process_task(task)
```

## Customization

### Modify Requirements Analysis
Customize how requirements are processed by updating rules in `src/analyzer_graph/rules.py`

### Change Code Storage
Configure different storage providers in `src/codebase_graph/storage.py`

### Adjust Development Workflow
Modify the development process in `src/development_graph/workflow.py`

### Update Prompts
Customize agent behavior by editing prompts in `src/prompts/`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

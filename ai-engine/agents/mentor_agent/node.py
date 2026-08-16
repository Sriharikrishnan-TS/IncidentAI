"""Mentor Agent powered by ChatGroq (Llama-3.3-70b).

Generates developer recommendations, TDD refactoring steps, code snippets,
and executive summary guidance.
"""

import logging
import json
import os
from typing import Any
from pydantic import BaseModel, Field
from reasoning.llm import get_llm

logger = logging.getLogger(__name__)


class RecommendationItem(BaseModel):
    priority: str = Field(description="Priority: high, medium, low")
    category: str = Field(description="Category e.g. code_quality, architecture, testing")
    title: str = Field(description="Title of recommendation")
    description: str = Field(description="Detailed explanation")
    action_items: list[str] = Field(description="List of specific actionable steps")
    related_incidents: list[str] = Field(description="IDs of related incidents")
    estimated_effort: str = Field(description="Estimated effort e.g. 2-3 hours")


class MentorGuidanceResult(BaseModel):
    summary: dict[str, Any]
    recommendations: list[RecommendationItem]
    learning_resources: list[dict[str, Any]]
    next_steps: list[str]


def generate_mentorship(
    repo_id: str,
    parsed_repo: dict[str, Any] | None,
    incidents: list[dict[str, Any]] | None,
    fragility_scores: dict[str, Any] | None,
) -> dict[str, Any]:
    """Generate mentorship guidance using ChatGroq Llama-3.3-70b LLM."""
    logger.info(f"[MentorAgent] Generating mentorship guidance for repo: {repo_id}")
    llm = get_llm(temperature=0.2)

    if llm and incidents:
        # Truncate lists passed to prompt to prevent Groq token context window errors
        top_incidents = incidents[:10]
        top_fragility = {
            "summary": fragility_scores.get("summary", {}) if fragility_scores else {},
            "components": fragility_scores.get("components", [])[:10] if fragility_scores else []
        }

        try:
            prompt = f"""You are a Principal Software Engineering Mentor and Tech Lead.
Repository ID: {repo_id}

Detected Incidents (top 10):
{json.dumps(top_incidents, indent=2)}

Fragility Metrics (top 10):
{json.dumps(top_fragility, indent=2)}

Provide actionable refactoring guidance, TDD strategies, and developer mentorship.
Respond ONLY in valid JSON matching this exact structure:
{{
  "summary": {{
    "total_incidents": {len(incidents)},
    "priority_actions": 2,
    "estimated_effort": "3-5 hours"
  }},
  "recommendations": [
    {{
      "priority": "high",
      "category": "code_quality",
      "title": "Refactor fragile main module",
      "description": "The main module shows high fragility. Break it down into decoupled services.",
      "action_items": ["Extract handler logic", "Add unit tests"],
      "related_incidents": ["INC-001"],
      "estimated_effort": "2 hours"
    }}
  ],
  "learning_resources": [
    {{
      "topic": "Clean Code Architecture",
      "description": "Learn decoupling & TDD patterns",
      "resources": ["https://example.com/clean-code"]
    }}
  ],
  "next_steps": [
    "Address high-priority incidents",
    "Add unit tests for fragile modules"
  ]
}}
"""
            structured_llm = llm.with_structured_output(MentorGuidanceResult)
            guidance: MentorGuidanceResult = structured_llm.invoke(prompt)
            
            logger.info(f"[MentorAgent] Groq LLM generated {len(guidance.recommendations)} mentorship recommendations")
            return guidance.model_dump()

        except Exception as e:
            logger.warning(f"[MentorAgent] Groq LLM invocation failed ({e}). Using intelligent fallback rules.")

    # Rule-Based Fallback Implementation
    inc_count = len(incidents) if incidents else 0
    return {
        "summary": {
            "total_incidents": inc_count,
            "priority_actions": min(inc_count, 3),
            "estimated_effort": "4-6 hours"
        },
        "recommendations": [
            {
                "priority": "high",
                "category": "code_quality",
                "title": "Improve test coverage for fragile files",
                "description": "High fragility detected in codebase files. Adding unit tests will reduce production incidents.",
                "action_items": [
                    "Write unit tests for core handlers",
                    "Add integration tests for main workflows",
                    "Target 80%+ test coverage"
                ],
                "related_incidents": [inc["id"] for inc in (incidents or []) if "id" in inc][:2],
                "estimated_effort": "2-3 hours"
            }
        ],
        "learning_resources": [
            {
                "topic": "Test-Driven Development",
                "description": "Learn TDD practices for python and go",
                "resources": ["https://example.com/tdd-guide"]
            }
        ],
        "next_steps": [
            "Address high-priority incidents first",
            "Implement recommended test coverage improvements",
            "Re-run analysis to verify risk reduction"
        ]
    }


from parsers.import_parser import parse_imports_from_file


def answer_mentor_question(
    repo_id: str,
    question: str,
    repo_path: str | None = None,
) -> str:
    """Answer user question dynamically using Groq LLM with detailed code & import analysis from cloned files."""
    logger.info(f"[MentorAgent] Answering user question for repo={repo_id}: {question}")
    llm = get_llm(temperature=0.2)
    
    file_details: list[dict[str, Any]] = []
    file_list: list[str] = []
    
    if repo_path and os.path.exists(repo_path):
        IGNORED_DIRS = {'.git', '.github', '.vscode', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build', '.next', 'repos'}
        CODE_EXTS = {'.py', '.go', '.js', '.ts', '.tsx', '.jsx', '.java', '.rs', '.cpp', '.c', '.html', '.css', '.json', '.md'}
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                file_list.append(rel_path)
                
                if ext in CODE_EXTS and len(file_details) < 40:
                    full_path = os.path.join(root, file)
                    line_count = 0
                    imports = []
                    snippet = ""
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()
                            line_count = len(lines)
                            snippet = "".join(lines[:15])  # Take first 15 lines (imports & headers)
                        imports = parse_imports_from_file(full_path)
                    except Exception:
                        pass
                        
                    file_details.append({
                        "file": rel_path,
                        "line_count": line_count,
                        "imports": imports,
                        "import_count": len(imports),
                        "header_snippet": snippet[:200]
                    })
                    
    sample_files = file_list[:50]
    
    if llm:
        try:
            prompt = f"""You are an elite AI Mentor & Engineering Lead analyzing a software codebase.
Repository ID: {repo_id}
Total Files in Repository: {len(file_list)}

Codebase Structure & Import Dependency Analysis:
{json.dumps(file_details, indent=2)}

User Question: "{question}"

CRITICAL INSTRUCTIONS:
- You ALREADY have full analysis of the repository files, line counts, imports, and code structure above.
- Do NOT ask the user to provide code or more context.
- Do NOT say "Without more information" or "it's not possible to determine".
- Answer the user's question directly, accurately, and concisely using the repository file analysis provided above.
- If asked which service/file has the most dependencies, identify the file with the highest number of imports from the analysis above.
"""
            response = llm.invoke(prompt)
            answer = response.content if hasattr(response, "content") else str(response)
            if isinstance(answer, list):
                answer = " ".join([str(item) for item in answer])
            return str(answer).strip()
        except Exception as e:
            logger.warning(f"[MentorAgent] LLM query failed: {e}")

    # Fallback if LLM unavailable or fails
    if file_details:
        sorted_by_deps = sorted(file_details, key=lambda x: x.get("import_count", 0), reverse=True)
        most_deps = sorted_by_deps[0] if sorted_by_deps else file_details[0]
        if "dependency" in question.lower() or "dependencies" in question.lower():
            return f"Based on static analysis of `{repo_id}`, `{most_deps['file']}` has the highest number of direct import dependencies ({most_deps['import_count']} imports: {', '.join(most_deps['imports'][:5])})."

    if "file" in question.lower() or "list" in question.lower():
        if file_list:
            files_str = "\n".join([f"- {f}" for f in sample_files[:20]])
            return f"Here are the files present in repository `{repo_id}` ({len(file_list)} total files):\n\n{files_str}"

    return f"Regarding your question '{question}': In repository `{repo_id}`, examine key modules like `{sample_files[0] if sample_files else 'main'}`."



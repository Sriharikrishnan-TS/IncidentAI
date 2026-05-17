"""Repository analysis node for the orchestration pipeline.

This node wraps the repository_agent and git_history_agent to provide
complete repository intelligence including structure, git history, and churn metrics.
"""

import logging
from typing import cast

from orchestration.state import IncidentState, log_node_execution
from agents.repository_agent import repository_agent_node
from agents.git_history_agent import git_history_agent_node
from graph.state import AgentState

logger = logging.getLogger(__name__)


def repository_node(state: IncidentState) -> IncidentState:
    """Parse and analyze repository structure with git intelligence.

    This node orchestrates two real agent implementations:
    1. repository_agent_node: Parses repository structure, detects services, languages, frameworks
    2. git_history_agent_node: Analyzes git history for churn metrics, contributors, PR analytics

    Args:
        state: Current pipeline state containing repo_id and repo_path

    Returns:
        Updated state with repository metadata, git intelligence, and parsed_repo populated
    """

    node_name = "repository_node"

    # ------------------------------------------------------------------
    # LOG START
    # ------------------------------------------------------------------

    state = log_node_execution(
        state,
        node_name,
        "started",
        f"Starting repository analysis for {state['repo_id']}"
    )

    logger.info(
        f"[{node_name}] Processing repository: "
        f"{state['repo_path']}"
    )

    try:

        # ------------------------------------------------------------------
        # STEP 1: Repository Structure Analysis
        # ------------------------------------------------------------------

        logger.info(
            f"[{node_name}] Invoking repository_agent_node..."
        )

        agent_state = cast(AgentState, {
            "repo_id": state["repo_id"],
            "repo_path": state["repo_path"]
        })

        repo_analysis = repository_agent_node(agent_state)

        # ------------------------------------------------------------------
        # FIXED:
        # Extract directly from agent output
        # ------------------------------------------------------------------

        services = repo_analysis.get("services", [])

        languages = repo_analysis.get("languages", [])

        frameworks = repo_analysis.get("frameworks", [])

        architecture_summary = repo_analysis.get(
            "architecture_summary",
            ""
        )

        logger.info(
            f"[{node_name}] Repository analysis complete: "
            f"{len(services)} services, "
            f"{len(languages)} languages, "
            f"{len(frameworks)} frameworks"
        )

        # ------------------------------------------------------------------
        # STEP 2: Git Intelligence Analysis
        # ------------------------------------------------------------------

        logger.info(
            f"[{node_name}] Invoking git_history_agent_node..."
        )

        git_agent_state = cast(AgentState, {
            "repo_id": state["repo_id"],
            "repo_path": state["repo_path"],
            "services": services,
            "languages": languages,
            "frameworks": frameworks,
            "architecture_summary": architecture_summary
        })

        git_analysis = git_history_agent_node(git_agent_state)

        # ------------------------------------------------------------------
        # FIXED:
        # Extract directly from git agent output
        # ------------------------------------------------------------------

        high_churn_services = git_analysis.get(
            "high_churn_services",
            []
        )

        recent_commits = git_analysis.get(
            "recent_commits",
            0
        )

        top_contributors = git_analysis.get(
            "top_contributors",
            []
        )

        pr_analytics = git_analysis.get(
            "pr_analytics",
            {}
        )

        logger.info(
            f"[{node_name}] Git analysis complete: "
            f"{len(high_churn_services)} high-churn services, "
            f"{recent_commits} recent commits, "
            f"{len(top_contributors)} contributors"
        )

        # ------------------------------------------------------------------
        # STEP 3: Build Parsed Repo Structure
        # ------------------------------------------------------------------

        parsed_repo = {
            "repo_id": state["repo_id"],
            "repo_path": state["repo_path"],

            "repository_metadata": {
                "services": services,
                "languages": languages,
                "frameworks": frameworks,
                "architecture_summary": architecture_summary,
                "total_services": len(services),
                "total_languages": len(languages),
                "total_frameworks": len(frameworks)
            },

            "git_intelligence": {
                "high_churn_services": high_churn_services,
                "recent_commits": recent_commits,
                "top_contributors": top_contributors,
                "pr_analytics": pr_analytics
            }
        }

        # ------------------------------------------------------------------
        # STEP 4: Update Shared State
        # ------------------------------------------------------------------

        state["parsed_repo"] = parsed_repo

        state["repository_metadata"] = parsed_repo[
            "repository_metadata"
        ]

        state["recent_commits"] = recent_commits

        state["top_contributors"] = top_contributors

        state["high_churn_services"] = high_churn_services

        # IMPORTANT:
        # Store these directly too for downstream nodes
        state["services"] = services

        state["languages"] = languages

        state["frameworks"] = frameworks

        state["architecture_summary"] = architecture_summary

        state["status"] = "repository_analyzed"

        # ------------------------------------------------------------------
        # STEP 5: Log Completion
        # ------------------------------------------------------------------

        state = log_node_execution(
            state,
            node_name,
            "completed",
            (
                f"Repository analysis completed. "
                f"Found {len(services)} services, "
                f"{len(languages)} languages, "
                f"{recent_commits} recent commits"
            ),
            data={
                "services_count": len(services),
                "languages_count": len(languages),
                "frameworks_count": len(frameworks),
                "recent_commits": recent_commits,
                "high_churn_services_count": len(
                    high_churn_services
                )
            }
        )

        logger.info(
            f"[{node_name}] Successfully completed repository "
            f"and git intelligence analysis"
        )

    except Exception as e:

        error_msg = (
            f"Repository analysis failed: {str(e)}"
        )

        state["error"] = error_msg

        state["status"] = "failed"

        state = log_node_execution(
            state,
            node_name,
            "failed",
            error_msg
        )

        logger.error(
            f"[{node_name}] {error_msg}",
            exc_info=True
        )

    return state
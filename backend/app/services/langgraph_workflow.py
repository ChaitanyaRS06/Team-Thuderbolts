# backend/app/services/langgraph_workflow.py
"""
LangGraph Agentic Workflow for UVA AI Research Assistant
Implements a multi-agent system with Generator, Evaluator, and Search agents
"""
from typing import Dict, List, Any, TypedDict, Annotated
from datetime import datetime
import json
import logging
import anthropic

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.config import settings

logger = logging.getLogger(__name__)

# Define the state structure for LangGraph
class AgenticRAGState(TypedDict):
    """State object that gets passed between nodes in the LangGraph workflow"""
    # Core query information
    question: str
    user_id: int
    is_admin: bool
    preferred_model: str

    # Workflow control
    iteration: int
    max_iterations: int
    current_stage: str
    needs_more_info: bool

    # Search results
    local_results: List[Dict]
    web_results: List[Dict]
    uva_results: List[Dict]
    github_results: List[Dict]

    # Processing chain
    messages: Annotated[List, add_messages]
    intermediate_answers: List[str]
    reasoning_steps: List[Dict]

    # Final outputs
    final_answer: str
    confidence_score: float
    sources: List[Dict]


class LangGraphAgenticWorkflow:
    """
    Multi-agent RAG workflow with specialized agents:
    - Generator Agent: Creates answers from context
    - Evaluator Agent: Assesses answer quality and completeness
    - Search Agent: Retrieves information from multiple sources
    - UVA Resource Agent: Searches UVA-specific resources
    - GitHub Agent: Searches code repositories and GitHub resources
    """

    def __init__(self, search_service, web_search_service, uva_scraper=None, github_mcp=None):
        self.search_service = search_service
        self.web_search_service = web_search_service
        self.uva_scraper = uva_scraper
        self.github_mcp = github_mcp

        # Initialize Anthropic client
        self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        # Store user and db for workflow execution
        self.current_user = None
        self.current_db = None
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with nodes and edges"""

        # Create the state graph
        workflow = StateGraph(AgenticRAGState)

        # Add nodes for each stage of the workflow
        workflow.add_node("analyze_question", self._analyze_question_node)
        workflow.add_node("local_search", self._local_search_node)
        workflow.add_node("uva_search", self._uva_search_node)
        workflow.add_node("github_search", self._github_search_node)
        workflow.add_node("evaluate_local", self._evaluate_local_node)
        workflow.add_node("web_search", self._web_search_node)
        workflow.add_node("generate_answer", self._generate_answer_node)
        workflow.add_node("evaluate_answer", self._evaluate_answer_node)
        workflow.add_node("synthesize_final", self._synthesize_final_node)

        # Set the entry point
        workflow.set_entry_point("analyze_question")

        # Add edges
        workflow.add_edge("analyze_question", "local_search")
        workflow.add_edge("local_search", "uva_search")
        workflow.add_edge("uva_search", "github_search")
        workflow.add_edge("github_search", "evaluate_local")

        # Conditional routing based on local search results
        workflow.add_conditional_edges(
            "evaluate_local",
            self._should_do_web_search,
            {
                "web_search": "web_search",
                "generate": "generate_answer"
            }
        )

        workflow.add_edge("web_search", "generate_answer")
        workflow.add_edge("generate_answer", "evaluate_answer")

        # Conditional routing for iteration control
        workflow.add_conditional_edges(
            "evaluate_answer",
            self._should_continue_iteration,
            {
                "continue": "web_search",
                "finish": "synthesize_final"
            }
        )

        workflow.add_edge("synthesize_final", END)

        return workflow.compile()

    # ==================== NODE IMPLEMENTATIONS ====================

    async def _analyze_question_node(self, state: AgenticRAGState) -> Dict:
        """Agent 1: Analyze the question and plan the approach"""
        logger.info(f"[Analyze] Question: {state['question'][:100]}...")

        prompt = f"""Analyze this question and determine:
1. Question complexity (1-5 scale)
2. What type of information is needed (factual, analytical, procedural)
3. Likely sources needed (documents, web, UVA resources)

Question: {state['question']}

Respond in JSON format."""

        response = await self._call_llm(
            state['preferred_model'],
            [{"role": "user", "content": prompt}]
        )

        # Parse analysis
        try:
            analysis = json.loads(response)
        except:
            analysis = {
                "complexity": 3,
                "type": "general",
                "sources": ["documents", "web"]
            }

        state['reasoning_steps'].append({
            "node": "analyze_question",
            "stage": "planning",
            "action": "Analyzed question complexity and requirements",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        })

        state['current_stage'] = "local_search"
        return state

    async def _local_search_node(self, state: AgenticRAGState) -> Dict:
        """Agent 2: Search local documents"""
        logger.info("[Local Search] Searching user documents...")

        try:
            results = await self.search_service.search(
                query=state['question'],
                user_id=state['user_id'],
                max_results=5,
                similarity_threshold=0.4
            )
            state['local_results'] = results

            state['reasoning_steps'].append({
                "node": "local_search",
                "stage": "retrieval",
                "action": f"Found {len(results)} relevant document chunks",
                "results_count": len(results),
                "avg_similarity": sum(r['similarity_score'] for r in results) / len(results) if results else 0,
                "timestamp": datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Local search error: {e}")
            state['local_results'] = []

        return state

    async def _uva_search_node(self, state: AgenticRAGState) -> Dict:
        """Agent 3: Search UVA resources"""
        logger.info("[UVA Search] Searching UVA IT resources...")

        state['uva_results'] = []

        if self.uva_scraper:
            try:
                # Check if question is related to UVA resources
                if any(keyword in state['question'].lower() for keyword in ['uva', 'virginia', 'onedrive', 'vpn', 'netbadge', 'campus']):
                    results = await self.uva_scraper.search_resources(
                        query=state['question'],
                        max_results=3
                    )
                    state['uva_results'] = results

                    state['reasoning_steps'].append({
                        "node": "uva_search",
                        "stage": "retrieval",
                        "action": f"Found {len(results)} relevant UVA resources",
                        "results_count": len(results),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except Exception as e:
                logger.error(f"UVA search error: {e}")

        return state

    async def _github_search_node(self, state: AgenticRAGState) -> Dict:
        """Agent: Search GitHub repositories and code"""
        logger.info("[GitHub Search] Searching GitHub repositories...")

        state['github_results'] = []

        if self.github_mcp:
            try:
                question_lower = state['question'].lower()

                # Keywords for different GitHub operations
                repo_list_keywords = ['list', 'show', 'my repo', 'my project', 'what repo', 'which repo', 'my github']
                code_search_keywords = ['code', 'function', 'class', 'implementation', 'find code', 'search code']
                github_keywords = ['repository', 'repo', 'github', 'git', 'pull request', 'pr', 'issue', 'commit', 'branch']

                # Check if question is asking to list user's repositories
                is_repo_list_request = any(keyword in question_lower for keyword in repo_list_keywords)
                is_code_search_request = any(keyword in question_lower for keyword in code_search_keywords)
                is_github_related = any(keyword in question_lower for keyword in github_keywords)

                if is_repo_list_request or is_github_related:
                    # User is asking to list their repositories
                    try:
                        logger.info("[GitHub] Listing user's repositories...")
                        repos = await self.github_mcp.list_repositories(per_page=30)

                        # Add all user's repositories
                        for repo in repos:
                            state['github_results'].append({
                                'type': 'repository',
                                'title': repo.get('full_name', 'Unknown'),
                                'content': repo.get('description', 'No description'),
                                'url': repo.get('html_url', ''),
                                'language': repo.get('language', 'Unknown'),
                                'stars': repo.get('stargazers_count', 0),
                                'private': repo.get('private', False),
                                'updated_at': repo.get('updated_at', ''),
                                'relevance_score': 0.9
                            })

                        logger.info(f"[GitHub] Found {len(state['github_results'])} user repositories")

                    except Exception as e:
                        logger.error(f"GitHub repository listing failed: {e}")

                elif is_code_search_request:
                    # User is asking about specific code - search within their repos
                    try:
                        logger.info("[GitHub] Searching user's code...")
                        # First get user's repos to scope the search
                        repos = await self.github_mcp.list_repositories(per_page=10)

                        # Search in user's repositories
                        for repo in repos[:5]:  # Search top 5 repos
                            try:
                                repo_name = repo.get('full_name', '')
                                # Try to get README or search files
                                readme = await self.github_mcp.get_readme(
                                    owner=repo_name.split('/')[0],
                                    repo=repo_name.split('/')[1]
                                )
                                if readme:
                                    state['github_results'].append({
                                        'type': 'repository',
                                        'title': f"{repo_name} - README",
                                        'content': readme.get('content', '')[:500],  # First 500 chars
                                        'url': repo.get('html_url', ''),
                                        'language': repo.get('language', 'Unknown'),
                                        'relevance_score': 0.7
                                    })
                            except:
                                pass

                    except Exception as e:
                        logger.warning(f"GitHub code search failed: {e}")

                if state['github_results']:
                    state['reasoning_steps'].append({
                        "node": "github_search",
                        "stage": "retrieval",
                        "action": f"Found {len(state['github_results'])} GitHub resources from user's account",
                        "results_count": len(state['github_results']),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                else:
                    logger.info("No GitHub results found for user's repositories")

            except Exception as e:
                logger.error(f"GitHub search error: {e}")

        return state

    async def _evaluate_local_node(self, state: AgenticRAGState) -> Dict:
        """Agent 4: Evaluate if local + UVA + GitHub results are sufficient"""
        logger.info("[Evaluate Local] Assessing information sufficiency...")

        total_results = len(state['local_results']) + len(state['uva_results']) + len(state['github_results'])

        if total_results == 0:
            state['needs_more_info'] = True
            decision = "No local, UVA, or GitHub resources found, will search web"
        elif total_results >= 3:
            avg_score = sum(r.get('similarity_score', r.get('relevance_score', 0))
                          for r in state['local_results'] + state['uva_results'] + state['github_results']) / total_results
            if avg_score >= 0.5:
                state['needs_more_info'] = False
                decision = "Sufficient information from local sources"
            else:
                state['needs_more_info'] = True
                decision = "Low relevance scores, will search web"
        else:
            state['needs_more_info'] = True
            decision = "Limited information found, will search web"

        state['reasoning_steps'].append({
            "node": "evaluate_local",
            "stage": "evaluation",
            "action": decision,
            "total_results": total_results,
            "needs_web_search": state['needs_more_info'],
            "timestamp": datetime.utcnow().isoformat()
        })

        return state

    async def _web_search_node(self, state: AgenticRAGState) -> Dict:
        """Agent 5: Perform web search"""
        logger.info("[Web Search] Searching the internet...")

        try:
            results = await self.web_search_service.search(
                query=state['question'],
                max_results=5
            )
            state['web_results'] = results

            state['reasoning_steps'].append({
                "node": "web_search",
                "stage": "retrieval",
                "action": f"Found {len(results)} web results",
                "results_count": len(results),
                "timestamp": datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Web search error: {e}")
            state['web_results'] = []

        return state

    async def _generate_answer_node(self, state: AgenticRAGState) -> Dict:
        """Agent 6: Generator - Create answer from all available context"""
        logger.info("[Generate] Creating answer from retrieved context...")

        # Compile context from all sources
        context_parts = []

        # Add local document context
        if state['local_results']:
            context_parts.append("=== UPLOADED DOCUMENTS ===")
            for idx, result in enumerate(state['local_results'][:3], 1):
                context_parts.append(
                    f"\n[Document {idx}: {result['document_name']} - Page {result.get('page_number', 'N/A')}]\n"
                    f"{result['chunk_text']}\n"
                )

        # Add UVA resources context
        if state['uva_results']:
            context_parts.append("\n=== UVA RESOURCES ===")
            for idx, result in enumerate(state['uva_results'], 1):
                context_parts.append(
                    f"\n[UVA Resource {idx}: {result['title']}]\n"
                    f"{result['content']}\n"
                    f"URL: {result['url']}\n"
                )

        # Add GitHub context
        if state['github_results']:
            context_parts.append("\n=== GITHUB REPOSITORIES & CODE ===")
            for idx, result in enumerate(state['github_results'], 1):
                if result['type'] == 'code':
                    context_parts.append(
                        f"\n[GitHub Code {idx}: {result['title']}]\n"
                        f"Repository: {result['repo']}\n"
                        f"File: {result['path']}\n"
                        f"{result['content']}\n"
                        f"URL: {result['url']}\n"
                    )
                else:  # repository
                    context_parts.append(
                        f"\n[GitHub Repository {idx}: {result['title']}]\n"
                        f"Description: {result['content']}\n"
                        f"Language: {result['language']}\n"
                        f"Stars: {result['stars']}\n"
                        f"URL: {result['url']}\n"
                    )

        # Add web context
        if state['web_results']:
            context_parts.append("\n=== WEB SEARCH RESULTS ===")
            for idx, result in enumerate(state['web_results'][:3], 1):
                context_parts.append(
                    f"\n[Web Result {idx}: {result['title']}]\n"
                    f"{result['content']}\n"
                    f"Source: {result.get('url', 'N/A')}\n"
                )

        context = "\n".join(context_parts)

        # Generate answer
        prompt = f"""You are a helpful AI research assistant for the University of Virginia (UVA).
Answer the question based on the provided context. Be specific and cite sources.

Context:
{context}

Question: {state['question']}

Provide a comprehensive answer with citations."""

        answer = await self._call_llm(
            state['preferred_model'],
            [{"role": "user", "content": prompt}]
        )

        state['intermediate_answers'].append(answer)
        state['iteration'] += 1

        state['reasoning_steps'].append({
            "node": "generate_answer",
            "stage": "generation",
            "action": "Generated answer from retrieved context",
            "iteration": state['iteration'],
            "timestamp": datetime.utcnow().isoformat()
        })

        return state

    async def _evaluate_answer_node(self, state: AgenticRAGState) -> Dict:
        """Agent 7: Evaluator - Assess answer quality and completeness"""
        logger.info("[Evaluate Answer] Assessing answer quality...")

        current_answer = state['intermediate_answers'][-1]

        evaluation_prompt = f"""Evaluate this answer for completeness and quality:

Question: {state['question']}
Answer: {current_answer}

Rate on a scale of 0-1:
- Completeness: Does it fully answer the question?
- Accuracy: Is the information accurate?
- Clarity: Is it clear and well-structured?

Respond in JSON with: {{"completeness": 0.0-1.0, "accuracy": 0.0-1.0, "clarity": 0.0-1.0, "overall": 0.0-1.0, "needs_improvement": true/false}}"""

        eval_response = await self._call_llm(
            state['preferred_model'],
            [{"role": "user", "content": evaluation_prompt}]
        )

        try:
            evaluation = json.loads(eval_response)
            confidence = evaluation.get('overall', 0.7)
            needs_improvement = evaluation.get('needs_improvement', False)
        except:
            confidence = 0.7
            needs_improvement = False

        state['confidence_score'] = confidence
        state['reasoning_steps'].append({
            "node": "evaluate_answer",
            "stage": "evaluation",
            "action": f"Evaluated answer quality: {confidence:.2f}",
            "confidence": confidence,
            "needs_improvement": needs_improvement,
            "timestamp": datetime.utcnow().isoformat()
        })

        return state

    async def _synthesize_final_node(self, state: AgenticRAGState) -> Dict:
        """Final synthesis and source compilation"""
        logger.info("[Synthesize] Creating final response...")

        # Use the best answer (usually the last one)
        state['final_answer'] = state['intermediate_answers'][-1] if state['intermediate_answers'] else "I couldn't generate an answer."

        # Compile sources
        sources = []

        for result in state['local_results']:
            sources.append({
                "type": "document",
                "title": result['document_name'],
                "page": result.get('page_number'),
                "relevance": result['similarity_score']
            })

        for result in state['uva_results']:
            sources.append({
                "type": "uva_resource",
                "title": result['title'],
                "url": result['url'],
                "relevance": result['relevance_score']
            })

        for result in state['github_results']:
            sources.append({
                "type": "github",
                "title": result['title'],
                "url": result['url'],
                "github_type": result['type'],
                "relevance": result['relevance_score']
            })

        for result in state['web_results']:
            sources.append({
                "type": "web",
                "title": result['title'],
                "url": result.get('url'),
                "relevance": result.get('score', 0.5)
            })

        state['sources'] = sources

        state['reasoning_steps'].append({
            "node": "synthesize_final",
            "stage": "synthesis",
            "action": "Compiled final answer and sources",
            "total_sources": len(sources),
            "timestamp": datetime.utcnow().isoformat()
        })

        return state

    # ==================== CONDITIONAL ROUTING ====================

    def _should_do_web_search(self, state: AgenticRAGState) -> str:
        """Decide whether to perform web search"""
        if state['needs_more_info']:
            return "web_search"
        else:
            return "generate"

    def _should_continue_iteration(self, state: AgenticRAGState) -> str:
        """Decide whether to continue iterating or finish"""
        if state['iteration'] >= state['max_iterations']:
            return "finish"
        elif state['confidence_score'] >= 0.8:
            return "finish"
        else:
            return "finish"  # For now, single iteration
            # return "continue"  # Enable for multi-iteration

    # ==================== LLM INTERFACE ====================

    async def _call_llm(self, model: str, messages: List[Dict]) -> str:
        """Call Anthropic Claude LLM"""
        try:
            # Convert messages format for Anthropic
            system_msg = ""
            user_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # Use Anthropic Claude
            response = self.anthropic_client.messages.create(
                model=settings.anthropic_model,
                max_tokens=2000,
                system=system_msg if system_msg else "You are a helpful AI research assistant.",
                messages=user_messages if user_messages else [{"role": "user", "content": messages[0]["content"]}]
            )
            return response.content[0].text

        except Exception as e:
            logger.error(f"LLM call error: {e}")
            return "Error generating response"

    # ==================== EXECUTION ====================

    async def execute(
        self,
        question: str,
        user_id: int,
        is_admin: bool,
        max_iterations: int = 3,
        enable_detailed_reasoning: bool = True,
        preferred_model: str = "gpt-4o",
        db = None
    ) -> Dict[str, Any]:
        """Execute the workflow"""
        self.current_db = db

        # Initialize state
        initial_state = {
            "question": question,
            "user_id": user_id,
            "is_admin": is_admin,
            "preferred_model": preferred_model,
            "iteration": 0,
            "max_iterations": max_iterations,
            "current_stage": "analyze",
            "needs_more_info": False,
            "local_results": [],
            "web_results": [],
            "uva_results": [],
            "github_results": [],
            "messages": [],
            "intermediate_answers": [],
            "reasoning_steps": [],
            "final_answer": "",
            "confidence_score": 0.0,
            "sources": []
        }

        # Execute workflow
        try:
            final_state = await self.workflow.ainvoke(initial_state)

            return {
                "final_answer": final_state["final_answer"],
                "confidence_score": final_state["confidence_score"],
                "sources": final_state["sources"],
                "reasoning_steps": final_state["reasoning_steps"] if enable_detailed_reasoning else [],
                "iterations_used": final_state["iteration"]
            }

        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return {
                "final_answer": f"I encountered an error while processing your question: {str(e)}",
                "confidence_score": 0.0,
                "sources": [],
                "reasoning_steps": [],
                "iterations_used": 0
            }

from langgraph.graph import END, START, StateGraph

from app.clients.gemini_client import GeminiClient
from app.clients.qdrant_client import QdrantClientWrapper
from app.graph.nodes.embed_requirement import make_embed_requirement_node
from app.graph.nodes.finalize_output import finalize_output_node
from app.graph.nodes.generate_from_rules import generate_from_rules_node
from app.graph.nodes.llm_refine import make_llm_refine_node
from app.graph.nodes.merge_partial_match import merge_partial_match_node
from app.graph.nodes.parse_requirement import make_parse_requirement_node
from app.graph.nodes.retrieve_candidates import make_retrieve_candidates_node
from app.graph.nodes.reuse_high_match import reuse_high_match_node
from app.graph.nodes.score_coverage import score_coverage_node
from app.graph.routing import route_by_coverage
from app.schemas.graph_state import PipelineState


def build_graph(gemini_client: GeminiClient, qdrant_client: QdrantClientWrapper):
    graph = StateGraph(PipelineState)

    graph.add_node("parse_requirement", make_parse_requirement_node(gemini_client))
    graph.add_node("embed_requirement", make_embed_requirement_node(gemini_client))
    graph.add_node("retrieve_candidates", make_retrieve_candidates_node(qdrant_client))
    graph.add_node("score_coverage", score_coverage_node)
    graph.add_node("reuse_high_match", reuse_high_match_node)
    graph.add_node("merge_partial_match", merge_partial_match_node)
    graph.add_node("generate_from_rules", generate_from_rules_node)
    graph.add_node("llm_refine", make_llm_refine_node(gemini_client))
    graph.add_node("finalize_output", finalize_output_node)

    graph.add_edge(START, "parse_requirement")
    graph.add_edge("parse_requirement", "embed_requirement")
    graph.add_edge("embed_requirement", "retrieve_candidates")
    graph.add_edge("retrieve_candidates", "score_coverage")

    graph.add_conditional_edges(
        "score_coverage",
        route_by_coverage,
        {
            "reuse_high_match": "reuse_high_match",
            "merge_partial_match": "merge_partial_match",
            "generate_from_rules": "generate_from_rules",
        },
    )

    graph.add_edge("reuse_high_match", "llm_refine")
    graph.add_edge("merge_partial_match", "llm_refine")
    graph.add_edge("generate_from_rules", "llm_refine")
    graph.add_edge("llm_refine", "finalize_output")
    graph.add_edge("finalize_output", END)

    return graph.compile()

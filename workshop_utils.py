"""Workshop utility helpers — visual progress and logging control."""
import logging


def quiet_logs():
    """Suppress verbose third-party SDK logging so notebook output stays clean."""
    for name in ['botocore', 'boto3', 'neo4j', 'httpx', 'opentelemetry',
                 'strands', 'urllib3', 'anthropic']:
        logging.getLogger(name).setLevel(logging.WARNING)
    logging.root.setLevel(logging.WARNING)


def lego_progress(completed: int):
    """Print a visual progress tower showing modules completed so far.

    Args:
        completed: number of modules completed (1-4).
    """
    modules = [
        "Module 1 — Vectorial RAG Hallucinates",
        "Module 2 — Graph-RAG Fixes It",
        "Module 3 — Production Agent with AgentCore",
        "Module 4 — Inspectable Neo4j Memory",
    ]
    total = len(modules)
    print("\n" + "=" * 56)
    print("  Workshop progress")
    print("  " + "🟦" * completed + "⬜" * (total - completed))
    for i, label in enumerate(modules):
        if i < completed:
            print(f"  ✅  {label}")
        elif i == completed:
            print(f"  ▶️   {label}  ← you are here")
        else:
            print(f"  ⬜  {label}")
    print("=" * 56 + "\n")

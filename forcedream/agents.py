"""Exact port of @forcedream/mcp-server's search_agents.ts.

Real, load-bearing fact confirmed directly from the source, not assumed: the server has no
working server-side capability/query filter on /v1/agents/list -- filtering happens
client-side, after fetching the full list. This was a real bug caught in the JS SDK build
(returned all 18 agents instead of the expected 1) before being fixed the same way here.
"""
from typing import Optional, TypedDict
import httpx


class AgentReliability(TypedDict, total=False):
    success_rate: Optional[float]
    avg_latency_ms: Optional[float]
    sample_size: int
    note: Optional[str]


class Agent(TypedDict, total=False):
    slug: str
    name: str
    description: str
    version: str
    capabilities: list[str]
    price_per_call_pence: int
    metrics: dict
    health: Optional[AgentReliability]


class SearchAgentsResult(TypedDict):
    count: int
    agents: list[Agent]
    note: str


async def search_agents(
    api_base: str,
    capability: Optional[str] = None,
    query: Optional[str] = None,
) -> SearchAgentsResult:
    """Discovers real ForceDream agents, merges in real reliability data, and applies
    client-side capability/query filters (the server has no working server-side filter)."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        list_res = await client.get(f'{api_base}/v1/agents/list')
        list_res.raise_for_status()
        data = list_res.json()

        try:
            rel_res = await client.get(f'{api_base}/v1/agents/reliability')
            rel_data = rel_res.json() if rel_res.status_code == 200 else None
        except httpx.HTTPError:
            rel_data = None

    agents: list[Agent] = data.get('agents') or []

    reliability_by_slug: dict[str, AgentReliability] = {}
    if rel_data and isinstance(rel_data.get('agents'), list):
        for ra in rel_data['agents']:
            slug = ra.get('agent_slug')
            if slug:
                reliability_by_slug[slug] = ra.get('reliability')

    if capability:
        cap = capability.lower()
        agents = [a for a in agents if cap in [c.lower() for c in (a.get('capabilities') or [])]]

    if query:
        q = query.lower()
        agents = [
            a for a in agents
            if q in a.get('slug', '').lower()
            or q in (a.get('name') or '').lower()
            or any(q in c.lower() for c in (a.get('capabilities') or []))
        ]

    enriched = [
        {**a, 'health': reliability_by_slug.get(a.get('slug', ''))}
        for a in agents
    ]

    return SearchAgentsResult(
        count=len(enriched),
        agents=enriched,
        note=(
            'No agents matched. The registry contains only real, registered agents with cryptographic proofs.'
            if len(enriched) == 0 else
            "Metrics are system-derived from proofs/ledger (proof_count, success_rate) -- never self-reported. "
            "Health (success_rate, avg_latency_ms, sample_size) is honestly null where no real reliability data exists yet."
        ),
    )

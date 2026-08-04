"""ForceDream real, autonomous procurement -- wraps POST /v1/procure.

Real gap fix: this SDK predates /v1/procure and only ever offered manual
search_agents() + invoke(). procure() lets an external system describe a need
and get back one, real, ranked recommendation with a reason -- no marketplace
browsing, no manual agent selection.
"""
from typing import Optional, TypedDict
import httpx


class ProcureAlternative(TypedDict, total=False):
    slug: str
    price_per_call_pence: int
    reputation_score: float
    cost_difference_pence: int
    latency_difference_ms: Optional[int]


class ProcureResult(TypedDict, total=False):
    recommended_agent: str
    reason: str
    expected_cost_pence: int
    expected_cost_gbp: str
    success_rate: Optional[float]
    avg_latency_ms: Optional[int]
    reputation_score: float
    verified: bool
    commercial_trust: bool
    sponsored: bool
    invoke_url: str
    alternatives: list[ProcureAlternative]
    note: str


async def procure(
    api_base: str,
    capability: str,
    budget_pence: Optional[int] = None,
    max_latency_ms: Optional[int] = None,
    min_success_rate: Optional[float] = None,
) -> ProcureResult:
    """Real call to POST /v1/procure. Returns exactly one recommended agent, or
    raises if none match -- never fabricates a recommendation. No API key needed
    (procurement itself is free; only invoke() spends money)."""
    body: dict = {'capability': capability}
    if budget_pence is not None:
        body['budget_pence'] = budget_pence
    if max_latency_ms is not None:
        body['max_latency_ms'] = max_latency_ms
    if min_success_rate is not None:
        body['min_success_rate'] = min_success_rate

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        res = await client.post(f'{api_base}/v1/procure', json=body)
        data = res.json()
        if res.status_code == 404:
            raise RuntimeError(data.get('note', 'No real agent matches these constraints.'))
        if res.status_code != 200:
            raise RuntimeError(data.get('error', f'procure failed: HTTP {res.status_code}'))
        return data

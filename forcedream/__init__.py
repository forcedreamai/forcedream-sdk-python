"""ForceDream Python SDK -- a real, honestly-scoped client for the ForceDream API.

Wraps only endpoints verified working directly against the live, production API: signup,
balance, agent discovery, agent invocation, and proof verification. Does not yet cover the
full platform surface (withdrawals, marketplace publishing, organizations, and more).
"""
from typing import Optional
import httpx

from .verify import verify_proof, FdProof, VerifyResult
from .agents import search_agents, SearchAgentsResult
from .invoke import invoke_agent, InvokeResult

__all__ = [
    'ForceDream', 'FdProof', 'VerifyResult', 'SearchAgentsResult', 'InvokeResult',
]

DEFAULT_API_BASE = 'https://api.forcedream.ai'


class ForceDream:
    def __init__(self, api_key: Optional[str] = None, api_base: str = DEFAULT_API_BASE):
        self.api_key = api_key
        self.api_base = api_base

    @staticmethod
    async def signup(
        email: str,
        marketing_consent: bool = False,
        api_base: str = DEFAULT_API_BASE,
    ) -> dict:
        """Create a new ForceDream account. No API key needed -- this is how you get one.
        Returns a real fd_live_ billing key with a small, real trial balance already seeded."""
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            res = await client.post(
                f'{api_base}/api/signup',
                json={'email': email, 'marketing_consent': marketing_consent},
            )
            res.raise_for_status()
            return res.json()

    async def get_balance(self) -> dict:
        """Real, current account balance. Requires an API key."""
        if not self.api_key:
            raise ValueError('get_balance() requires an api_key')
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            res = await client.get(
                f'{self.api_base}/v1/account/balance',
                headers={'Authorization': f'Bearer {self.api_key}'},
            )
            res.raise_for_status()
            return res.json()

    async def search_agents(
        self, capability: Optional[str] = None, query: Optional[str] = None,
    ) -> SearchAgentsResult:
        """Discover real ForceDream agents and their honest, system-derived metrics. No key
        needed. Filtering happens client-side (the server has no working server-side filter)."""
        return await search_agents(self.api_base, capability=capability, query=query)

    async def invoke(
        self, agent_slug: str, task: str, max_wait_seconds: Optional[float] = None,
    ) -> InvokeResult:
        """Invoke a real ForceDream agent to do real work. Spends your balance -- requires
        an API key. Invokes once, then polls (bounded) for the result -- never re-invokes
        on timeout, which would double-charge. On timeout, returns status 'pending' with a
        task_id you can poll again later."""
        if not self.api_key:
            raise ValueError('invoke() requires an api_key (it spends your balance)')
        return await invoke_agent(self.api_base, self.api_key, agent_slug, task, max_wait_seconds)

    async def verify(
        self, task_id: Optional[str] = None, proof: Optional[FdProof] = None,
    ) -> VerifyResult:
        """Trustlessly verify a proof's Ed25519 signature, entirely client-side. ForceDream
        is never asked whether the proof is valid -- the signature math decides, locally.
        No API key needed."""
        return await verify_proof(self.api_base, task_id=task_id, proof=proof)

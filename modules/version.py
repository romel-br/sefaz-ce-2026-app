"""
Lê a versão do build a partir do .git local (sem depender do binário git).

Streamlit Cloud clona o repo no deploy, então o .git folder está disponível.
Localmente também funciona.

Retorna:
- short_sha: primeiros 7 chars do commit hash
- full_sha: hash completo
- ref_name: nome do branch ou "detached" se HEAD desconectado
- deploy_time: mtime de app.py (proxy razoável para "quando esse build subiu")
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).parent.parent
GIT_DIR = ROOT / ".git"


@dataclass(frozen=True)
class BuildInfo:
    short_sha: str
    full_sha: str
    ref_name: str
    deploy_time: datetime | None  # UTC

    @property
    def label(self) -> str:
        """Label curto pra exibir na UI: 'a1b2c3d · 03/05 14:25'."""
        parts = [self.short_sha]
        if self.deploy_time:
            parts.append(self.deploy_time.strftime("%d/%m %H:%M UTC"))
        return " · ".join(parts)


def _read_packed_ref(ref_path: str) -> str | None:
    """Lê refs/heads/master de .git/packed-refs caso o ref não exista solto."""
    packed = GIT_DIR / "packed-refs"
    if not packed.exists():
        return None
    for line in packed.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "^")):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2 and parts[1] == ref_path:
            return parts[0]
    return None


def _resolve_head() -> tuple[str, str]:
    """Resolve .git/HEAD → (full_sha, ref_name). ref_name='detached' se HEAD direto."""
    head_file = GIT_DIR / "HEAD"
    if not head_file.exists():
        return ("unknown", "unknown")

    content = head_file.read_text(encoding="utf-8", errors="ignore").strip()

    # Detached HEAD: direct SHA
    if not content.startswith("ref:"):
        return (content, "detached")

    # Symbolic ref: ref: refs/heads/master
    ref_path = content.split(maxsplit=1)[1].strip()
    ref_name = ref_path.rsplit("/", 1)[-1]

    # Try loose ref first
    ref_file = GIT_DIR / ref_path
    if ref_file.exists():
        return (ref_file.read_text(encoding="utf-8", errors="ignore").strip(), ref_name)

    # Fallback: packed refs
    if sha := _read_packed_ref(ref_path):
        return (sha, ref_name)

    return ("unknown", ref_name)


def _deploy_time() -> datetime | None:
    """mtime de app.py como proxy do deploy time."""
    app_py = ROOT / "app.py"
    if not app_py.exists():
        return None
    return datetime.fromtimestamp(app_py.stat().st_mtime, tz=timezone.utc)


@lru_cache(maxsize=1)
def get_build_info() -> BuildInfo:
    full_sha, ref_name = _resolve_head()
    return BuildInfo(
        short_sha=full_sha[:7] if full_sha != "unknown" else "unknown",
        full_sha=full_sha,
        ref_name=ref_name,
        deploy_time=_deploy_time(),
    )

"""Backend package for PaperMem Copilot."""
import os

# 禁用 ChromaDB telemetry（在所有模块导入之前）
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_DISABLED"] = "1"

try:
    import posthog

    posthog.disabled = True

    def _safe_capture(*_args, **_kwargs) -> None:
        return None

    posthog.capture = _safe_capture
except Exception:
    pass

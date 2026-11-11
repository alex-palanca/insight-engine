import logging
from datetime import datetime

from intelligence import briefing_generator
from storage import storage_utils as storage
from telemetry.recorder import TelemetryRecorder

logger = logging.getLogger(__name__) 
today = datetime.now().strftime("%Y-%m-%d")

def synthesize(
    run_id: str,
    recorder: 'TelemetryRecorder'
):
    """Synthesize daily briefing."""
    run_id = recorder.get_or_create_current_run_id()

    metrics: dict = {"duration_ms": 0}
    started_at = datetime.now()

    recorder.start_stage(run_id, "synthesize")
    logger.info("Synthesizing briefing.")

    try:
        prompt = storage.obtain_markdown(today)
        id_to_url = storage.download_id_to_url(today)

        briefing, briefing_metrics = briefing_generator.generate_briefing(prompt, id_to_url, temperature=0.35)
        metrics.update(briefing_metrics)

        try:
            storage.upload_briefing(today,briefing)
        except Exception:
            logger.warning("Failed to upload briefing", exc_info=True)

        metrics["duration_ms"] = int((datetime.now() - started_at).total_seconds() * 1000)
        recorder.finish_stage(
            run_id,
            "synthesize",
            status="success",
            metrics=metrics,
        )

    except Exception as exc:
        metrics["duration_ms"] = int((datetime.now() - started_at).total_seconds() * 1000)
        metrics["error_type"] = type(exc).__name__

        recorder.finish_stage(
            run_id,
            "synthesize",
            status="failed",
            metrics=metrics,
        )
        logger.exception("Synthesis stage failed.")
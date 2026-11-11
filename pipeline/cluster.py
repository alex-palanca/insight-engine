import logging
import time

from processing import clustering_engine
from storage.db_service import get_db_service
from telemetry.recorder import TelemetryRecorder

logger = logging.getLogger(__name__)

def cluster(
        run_id: str,
        recorder: TelemetryRecorder,
        score = 30,
        **hyperparameters
):
        """Cluster articles into events and link them to existing events in the database."""
        run_id = recorder.get_or_create_current_run_id()

        try:
                metrics: dict = {"duration_ms": 0}
                started_at = time.perf_counter()
                recorder.start_stage(run_id, "cluster")

                db_service = get_db_service()

                logger.info("Phase 1 - Matching unclustered articles against open events.")
                match_metrics = clustering_engine.match_and_attach_articles(score, **hyperparameters)
                metrics.update(match_metrics)

                logger.info("Intermediate Phase - Updating opened events state")
                update_metrics = db_service.update_stale_events_status()
                metrics.update(update_metrics)

                logger.info("Phase 2 - Clustering remaining unclustered articles into new events.")
                clustering_metrics = clustering_engine.events_clustering(score, **hyperparameters)
                metrics.update(clustering_metrics)

                metrics["duration_ms"] = int((time.perf_counter() - started_at) * 1000)
                
                recorder.finish_stage(
                run_id,
                "cluster",
                status="success",
                metrics=metrics,
                )

        except Exception as exc:
                metrics["duration_ms"] = int((time.perf_counter() - started_at) * 1000)
                metrics["error_type"] = type(exc).__name__

                recorder.finish_stage(
                run_id,
                "cluster",
                status="failed",
                metrics=metrics,
                )
                logger.exception("Clustering stage failed.")
                raise
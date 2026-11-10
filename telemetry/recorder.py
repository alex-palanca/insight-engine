import logging
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB

from storage.db_service import Base, NeonDatabaseService, get_db_service

logger = logging.getLogger(__name__)


class PipelineRun(Base):
    """
    Represents a run of the data processing pipeline, storing metadata about the run.
    """
    __tablename__ = "log_pipeline"

    run_id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="running")
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    metrics = Column(JSONB, nullable=True)

class StageRun(Base):
    """
    Represents a stage in the data processing pipeline, storing metadata about the stage.
    """
    __tablename__ = "log_stage"

    run_id = Column(Integer, nullable=False, primary_key=True)
    stage_name = Column(Text, nullable=False, primary_key=True)
    status = Column(Text, nullable=False, default="running")
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    metrics = Column(JSONB, nullable=True)

class TelemetryRecorder:
    """
    Records pipeline execution state in PostgreSQL.

    This class owns telemetry behavior:
    - creating/updating run and stage rows
    - merging JSONB metrics
    - translating Python exceptions into telemetry status
    - ensuring telemetry is recorded even if the pipeline fails
    """
    def __init__(self, db_service: NeonDatabaseService | None = None):
        self._db = db_service or get_db_service()

    def get_or_create_current_run_id(self) -> str:
        """
        Return the latest pipeline run whose status is 'running'.

        Creates a new run if none exists. This allows every stage process
        to attach to the same logical pipeline execution.
        """
        try:
            with self._db.share_session() as session:
                run = (
                    session.query(PipelineRun)
                    .filter(PipelineRun.status == "running")
                    .order_by(PipelineRun.started_at.desc())
                    .first()
                )

                if run:
                    return str(run.run_id)

                run = PipelineRun(
                    status="running",
                    started_at=datetime.now(tz=UTC),
                )

                session.add(run)
                session.flush()

                logger.info("Started recording pipeline run %s.", run.run_id)
                return str(run.run_id)

        except Exception:
            logger.exception("Failed to get or create current pipeline run.")
            return ""

    def finish_run(
        self,
        run_id: str,
        status: str
    ) -> None:
        """Mark the pipeline run as finished."""
        if not run_id:
            return

        try:
            with self._db.share_session() as session:
                run = session.get(PipelineRun, run_id)

                if not run:
                    logger.warning("Cannot finish unknown pipeline run %s.", run_id)
                    return

                run.status = status
                run.finished_at = datetime.now(tz=UTC)
                logger.info("Finished recording pipeline run %s.", run.run_id)

        except Exception:
            logger.exception("Failed to finish pipeline run telemetry.")

    def start_stage(
        self,
        run_id: str,
        stage_name: str
    ) -> str:
        """Create a StageRun row."""
        if not run_id:
            return ""

        try:
            with self._db.share_session() as session:
                stage = StageRun(
                    run_id=run_id,
                    stage_name=stage_name,
                    status="running",
                    metrics={},
                    started_at=datetime.now(tz=UTC),
                )

                session.add(stage)
                session.flush()
                logger.info("Started recording stage %s for run %s.", stage_name, run_id)


        except Exception:
            logger.exception("Failed to start telemetry for stage %s.", stage_name)
            return ""

    def finish_stage(
        self,
        run_id: str,
        stage_name: str,
        status: str,
        metrics: dict
    ) -> None:
        """Mark a stage attempt as finished."""
        if not run_id:
            return

        try:
            with self._db.share_session() as session:
                stage = session.get(
                    StageRun, 
                    {
                        "run_id": int(run_id),
                        "stage_name": stage_name,
                    }
                )

                if not stage:
                    logger.warning("Cannot finish unknown stage run %s.", run_id)
                    return

                stage.status = status
                stage.finished_at = datetime.now(tz=UTC)
                current_metrics = stage.metrics or {}
                current_metrics.update(metrics)
                stage.metrics = current_metrics
                logger.info("Finished recording stage %s for run %s.", stage_name, run_id)

        except Exception:
            logger.exception("Failed to finish telemetry for stage run %s.", run_id)
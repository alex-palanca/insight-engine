import datetime
import logging
import uuid

from sqlalchemy import Column, DateTime, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB

from storage.db_service import Base, share_session

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

    run_id = Column(Integer, nullable=False)
    stage_name = Column(Text, nullable=False)
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
    def __init__(self):
        pass

    def get_or_create_current_run_id(self) -> str:
        """
        Return the latest pipeline run whose status is 'running'.

        Creates a new run if none exists. This allows every stage process
        to attach to the same logical pipeline execution.
        """
        try:
            with share_session() as session:
                run = (
                    session.query(PipelineRun)
                    .filter(PipelineRun.status == "running")
                    .order_by(PipelineRun.started_at.desc())
                    .first()
                )

                if run:
                    return str(run.run_id)

                run = PipelineRun(status="running")
                session.add(run)
                session.flush()

                logger.info("Started pipeline run %s.", run.run_id)
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
            with share_session() as session:
                run = session.get(PipelineRun, uuid.UUID(run_id))

                if not run:
                    logger.warning("Cannot finish unknown pipeline run %s.", run_id)
                    return

                run.status = status
                run.finished_at = datetime.now(datetime.UTC)

        except Exception:
            logger.exception("Failed to finish pipeline run telemetry.")

    def start_stage(
        self,
        run_id: str,
        stage_name: str
    ) -> str:
        """Create a StageRun row and return its ID."""
        if not run_id:
            return ""

        try:
            with share_session() as session:
                stage = StageRun(
                    pipeline_run_id=run_id,
                    stage_name=stage_name,
                    status="running",
                    metrics={},
                    started_at=datetime.now(datetime.UTC),
                )

                session.add(stage)
                session.flush()

                return str(stage.id)

        except Exception:
            logger.exception("Failed to start telemetry for stage %s.", stage_name)
            return ""

    def finish_stage(
        self,
        stage_run_id: str,
        status: str,
        metrics: dict
    ) -> None:
        """Mark a stage attempt as finished."""
        if not stage_run_id:
            return

        try:
            with share_session() as session:
                stage = session.get(StageRun, uuid.UUID(stage_run_id))

                if not stage:
                    logger.warning("Cannot finish unknown stage run %s.", stage_run_id)
                    return

                stage.status = status
                stage.finished_at = datetime.now(datetime.UTC)
                current_metrics = stage.metrics or {}
                current_metrics.update(metrics)
                stage.metrics = current_metrics

        except Exception:
            logger.exception("Failed to finish telemetry for stage run %s.", stage_run_id)
import argparse
import asyncio
import logging

from config import env_ini  # noqa: F401
from config.logging_config import setup_logging
from pipeline.assemble import assemble
from pipeline.backfill import backfill
from pipeline.cluster import cluster
from pipeline.describe import describe
from pipeline.enrich import enrich
from pipeline.ingest import ingest
from pipeline.synthesize import synthesize
from telemetry.recorder import TelemetryRecorder

logger = logging.getLogger("isolate_pipeline")
recorder = TelemetryRecorder()

def main():
    run_id = recorder.get_or_create_current_run_id()
    setup_logging()
    parser = argparse.ArgumentParser(description="ISOLATE Intelligence Pipeline")
    parser.add_argument(
        'stage', 
        choices=['ingest','ing','enrich','enrichment','cluster','cluster','describe','assemble','synthesize','synth', 'backfill', 'all'], 
        nargs='?', 
        default='all',
        help="Pipeline stage to execute (default: all)"
    )
    parser.add_argument(
    "--min-date",
    help="Backfill start date, inclusive, in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--max-date",
        help="Backfill end date, inclusive, in YYYY-MM-DD format.",
    )
    args = parser.parse_args()

    # Core pipeline jobs
    if args.stage in ['ingest', 'ing','all']:
        logger.info("Running ingestion stage.")
        ingest(run_id,recorder)
    
    if args.stage in ['enrich', 'enrichment','all']:
        logger.info("Running enrichment stage.")
        enrich()
    
    if args.stage in ['cluster', 'events','all']:
        logger.info("Running clustering and linking stage.")
        cluster(similarity_threshold=0.375, max_df=0.85, min_df=2)

    if args.stage in ['describe','all']:
        logger.info("Running events processing stage.")
        asyncio.run(describe())

    if args.stage in ['assemble','all']:
        logger.info("Running assemble stage.")
        assemble()
    
    if args.stage in ['synthesize', 'synth','all']:
        logger.info("Running synthesis stage.")
        synthesize()

    # Adittional jobs
    if args.stage == 'backfill':
        logger.info("Running backfill for selected dates.")
        backfill(args.min_date,args.max_date)

    recorder.finish_run(run_id, status="success")

if __name__ == "__main__":
  
    main()

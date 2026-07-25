from config import env_ini # noqa: F401
import logging
import argparse
from config.logging_config import setup_logging

from pipeline.ingest import ingest
from pipeline.enrich import enrich
from pipeline.cluster import cluster
from pipeline.synthesize import synthesize

logger = logging.getLogger("isolate_pipeline")

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="ISOLATE Intelligence Pipeline")
    parser.add_argument(
        'stage', 
        choices=['ingest','ing','enrich','enrichment','events_processing','events','format','fmt','synthesize','syn', 'all'], 
        nargs='?', 
        default='all',
        help="Pipeline stage to execute (default: all)"
    )
    args = parser.parse_args()
    
    if args.stage in ['ingest', 'ing','all']:
        logger.info("Running ingestion stage.")
        ingest()
    
    if args.stage in ['enrich', 'enrichment','all']:
        logger.info("Running enrichment stage.")
        enrich()
    
    if args.stage in ['events_processing', 'events','all']:
        logger.info("Running events processing stage.")
        cluster()
    
    if args.stage in ['synthesize', 'syn','all']:
        logger.info("Running synthesis stage.")
        synthesize()

if __name__ == "__main__":
  
    main()

import logging
import sys
import time

import click

from autoscaler.cluster import Cluster

logger = logging.getLogger('autoscaler')

DEBUG_LOGGING_MAP = {
    0: logging.CRITICAL,
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG
}


@click.command()
@click.option("--cluster-name")
@click.option("--regions", default="us-west-1")
@click.option("--sleep", default=60)
@click.option("--kubeconfig", default=None,
              help='Full path to kubeconfig file. If not provided, '
                   'we assume that we\'re running on kubernetes.')
@click.option("--idle-threshold", default=3600)
@click.option("--type-idle-threshold", default=3600*24*7)
@click.option("--aws-access-key", default=None, envvar='AWS_ACCESS_KEY_ID')
@click.option("--aws-secret-key", default=None, envvar='AWS_SECRET_ACCESS_KEY')
@click.option("--instance-init-time", default=25 * 60)
@click.option("--parkingspot-api-key", default=None, envvar='PARKINGSPOT_API_KEY')
@click.option("--slack-hook", default=None, envvar='SLACK_HOOK',
              help='Slack webhook URL. If provided, post scaling messages '
                   'to Slack.')
@click.option("--dry-run", is_flag=True)
@click.option('--verbose', '-v',
              help="Sets the debug noise level, specify multiple times "
                   "for more verbosity.",
              type=click.IntRange(0, 3, clamp=True),
              count=True)
def main(cluster_name, regions, sleep, kubeconfig,
         aws_access_key, aws_secret_key, idle_threshold, type_idle_threshold,
         instance_init_time, parkingspot_api_key, slack_hook, dry_run, verbose):
    if verbose > 0:
        logger_handler = logging.StreamHandler(sys.stderr)
        logger_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(logger_handler)
        logger.setLevel(DEBUG_LOGGING_MAP.get(verbose, logging.DEBUG))

    if not (aws_secret_key and aws_access_key):
        logger.error("Missing AWS credentials. Please provide aws-access-key and aws-secret-key.")
        sys.exit(1)

    cluster = Cluster(aws_access_key=aws_access_key,
                      aws_secret_key=aws_secret_key,
                      regions=regions.split(','),
                      kubeconfig=kubeconfig,
                      idle_threshold=idle_threshold,
                      instance_init_time=instance_init_time,
                      type_idle_threshold=type_idle_threshold,
                      cluster_name=cluster_name,
                      parkingspot_api_key=parkingspot_api_key,
                      slack_hook=slack_hook,
                      dry_run=dry_run
                      )
    backoff = sleep
    while True:
        scaled = cluster.scale_loop()
        if scaled:
            time.sleep(sleep)
            backoff = sleep
        else:
            logger.warn("backoff: %s" % backoff)
            backoff *= 2
            time.sleep(backoff)


if __name__ == "__main__":
    main()

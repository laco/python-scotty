from __future__ import print_function
import click
# import yaml
from .core import load_config, log, rnd_scotty_quote, init_cluster_service_ctx
from .ecs import deploy as ecs_deploy


@click.group()
@click.option('-c', '--config', type=click.File('r'), default="scotty.yml", help="Config file path, default: scotty.yml")
@click.option('-q', '--quiet', default=False, is_flag=True, help="Don't print deploy steps on the console.")
@click.pass_context
def cli(ctx, config, quiet):
    """AWS ECS Docker Deployment Tool"""
    ctx.obj = {}
    ctx.obj['config'] = load_config(config.read())  # yaml.load(config.read())
    ctx.obj['quiet'] = quiet
    log(ctx, ' * ' + rnd_scotty_quote() + ' * ')


@cli.command()
@click.argument('cluster')
@click.argument('service')
@click.argument('tag')
@click.option('--strategy', default='canary')
@click.pass_context
def deploy(ctx, cluster, service, tag, strategy):
    # click.echo("""AWS Credetinals {access_key} {secret_key}""".format(access_key=ctx.obj['config']['access_key'], secret_key=ctx.obj['config']['secret_key']))
    ctx = init_cluster_service_ctx(ctx, cluster, service)
    if ctx.obj['cluster_type'] == 'ecs':
        return ecs_deploy(ctx, tag, strategy)


@cli.command()
@click.argument('cluster')
@click.argument('service')
@click.pass_context
def status(ctx, cluster, service):
    pass


@cli.command()
@click.pass_context
def delete(ctx):
    pass


@cli.command()
@click.pass_context
def init(ctx):
    pass


# @cli.command()
# @click.argument('cluster')
# @click.argument('service')
# @click.argument('tag')
# @click.pass_context
# def print_task_definition(ctx, environment, project, tag):
#     # _validate_params(ctx, environment=environment, project=project, tag=tag)
#     click.echo(build_task_definition(ctx.obj['config'], environment, project, tag))


def main():
    return cli(auto_envvar_prefix='SCOTTY')

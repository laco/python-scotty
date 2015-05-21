from logging import getLogger
import yaml
import click
logger = getLogger(__name__)


def log(ctx, msg):
    if not ctx.obj['quiet']:
        click.echo(msg)


def rnd_scotty_quote():
    quotes = [
        "I'm giving her all she's got, Captain!",
        "I like this ship! You know, it's exciting!",
        "I've never beamed three people from two targets onto one pad before!",

        "So, the Enterprise has had its maiden voyage, has it? She is one well-endowed lady. "
        "I'd like to get my hands on her \"ample nacelles,\" if you pardon the engineering parlance.",

        "I, um, yes. Can I get a towel, please?",
        "Dilithium chamber at maximum, Captain.",
        "I know what time it is. I don't need a bloomin' cuckoo clock.",
        "Aye. It was an emotional statement. I don't expect you to understand it. (to Mr. Spock)",

        "For the love of God, don't use those torpedoes.",
        "Computer! Computer? ",
        "Hello, computer. ",
        "Keyboard. How quaint. ",
        "Admiral, there be whales here! ",
        "Damage control is easy. Reading Klingon - that's hard. ",
        "All systems automated and ready. A chimpanzee and two trainees could run her. ",
        "Aye, sir, I'm working on it! ",
        "There's nothing amazing about it. I know this ship like the back of my hand. ",

        "USS Enterprise, shakedown crew's report. I think this new ship was put together by monkeys. \n"
        "Oh, she's got a fine engine, but half the doors won't open, and guess whose job it is to make it right. ",

        "Don't you worry, Captain. We'll beat those Klingon devils, even if I have to get out and push. ",
        "We can beam IT aboard anytime now, sir. ",
        "The best diplomat I know is a fully activated phaser bank.",
        " Aye, sir. Before they went into warp, I transported the whole kit 'n' caboodle into their engine room, where they'll be no tribble at all. ",
        "That phaser is set to kill. ",
        "Hold together little darling, hold together. ",
    ]
    import random
    return random.choice(quotes)


def load_config(config_text):
    config = yaml.load(config_text)
    logger.info('Config loaded.')

    if 'clusters' not in config:
        raise ValueError('"clusters" key missing from config file')
    elif 'services' not in config:
        raise ValueError('"services" key missing from config file')
    else:
        logger.info('Clusters({0}): {1}'.format(len(config['clusters']), ', '.join(config['clusters'].keys())))
        return config


def init_cluster_service_ctx(ctx, cluster, service):
    ctx.obj['cluster'] = {'name': cluster}
    ctx.obj['service'] = {'name': service}
    try:
        ctx.obj['cluster']['config'] = ctx.obj['config']['clusters'][cluster]
        ctx.obj['cluster_type'] = ctx.obj['cluster']['config'].get('type', 'ecs')
    except KeyError:
        raise ValueError('Unknown cluster:{}'.format(cluster))
    try:
        ctx.obj['service']['config'] = ctx.obj['config']['services'][service]
    except KeyError:
        raise ValueError('Unknown service:{}'.format(cluster))
    return ctx

# from jinja2 import Environment, FileSystemLoader

SCOTTY_PREFIX = 'sc0'
# SCOTTY_SEPARATOR_STR = '-I-'


# def task_definition_name(env, project):
#     return SCOTTY_SEPARATOR_STR.join([SCOTTY_PREFIX, env, project])


# def service_name_prefix(env, project):
#     return SCOTTY_SEPARATOR_STR.join([SCOTTY_PREFIX, env, project])


# def build_task_definition(config, env, project, tag):
#     task_definition_template_name = '.'.join([config['projects'][project].get('template', project), 'j2'])
#     return _render_template(config,
#                             template_name=task_definition_template_name,
#                             variables=_build_variables(config, env, project, tag))


# def _render_template(config, template_name, variables):
#     env = Environment(loader=FileSystemLoader(config['defaults'].get('template_dir', 'scotty_templates')))
#     template = env.get_template(template_name)
#     return template.render(**variables)


# def _build_variables(config, env, project, tag):
#     common_variables = {
#         'SCOTTY_FAMILY': task_definition_name(env, project),
#         'SCOTTY_TAG': tag,
#         'SCOTTY_ENV': env,
#         'SCOTTY_PROJECT': project,
#     }
#     common_variables.update(config['projects'][project].get('context'))
#     common_variables.update(config['environments'][env].get('context'))
#     return common_variables


# def create_service():
#     pass


# def update_service():
#     pass


# def delete_service():
#     pass

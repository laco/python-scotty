from json import dumps
from time import sleep
# from boto.ec2containerservice.layer1 import EC2ContainerServiceConnection
# from boto.regioninfo import get_regions
from .core import log, SCOTTY_PREFIX
import boto3


def ecs_connection(region_name='us-east-1'):
    # """The original boto function is broken on python3, this works!"""

    # def regions():
    #     return get_regions('ec2containerservice', connection_cls=EC2ContainerServiceConnection)

    # def connect_to_region(region_name, **kw_params):
    #     for region in regions():
    #         if region.name == region_name:
    #             return region.connect(**kw_params)
    #     return None
    # return connect_to_region(region_name)
    return boto3.client('ecs', region_name=region_name)


def deploy(ctx, tag, strategy='canary'):
    ctx = _init_ecs_connection(ctx)
    if _check_cluster_health(ctx):
        task_def = _register_task_definition(ctx, tag)
        service_descriptions = _get_services(ctx)
        if not service_descriptions:
            services = _create_services(ctx, task_def)
        elif strategy == 'canary':
            services = _update_services_with_canary(ctx, service_descriptions, task_def, strategy)
        return services
    else:
        log(ctx, 'Cluster error.')


def _init_ecs_connection(ctx):
    region_name = ctx.obj['cluster']['config'].get('region', 'us-east-1')
    ctx.obj['ecs_conn'] = ecs_connection(region_name)
    result_ = ctx.obj['ecs_conn'].list_clusters()
    cccount_ = len(result_['clusterArns'])
    if cccount_ >= 1:
        log(ctx, 'I found {0} cluster(s) in this region.'.format(cccount_))
        return ctx
    else:
        raise Exception('Missing clusters! Check the "region" settings!')


def _check_cluster_health(ctx):
    result_ = ctx.obj['ecs_conn'].describe_clusters(clusters=[ctx.obj['cluster']['name']])
    cluster_data_ = result_['clusters'][0]
    log(ctx, """The cluster {name} is {status}. With
 -> {instance_count} ec2 instances,
 -> {running_task_count} running tasks,
 -> {pending_task_count} pending tasks.
    """.format(
        name=cluster_data_['clusterName'],
        status=cluster_data_['status'],
        instance_count=cluster_data_['registeredContainerInstancesCount'],
        running_task_count=cluster_data_['runningTasksCount'],
        pending_task_count=cluster_data_['pendingTasksCount']
    ))
    # log(ctx, str(result_))
    return cluster_data_['status'] == 'ACTIVE'


def _register_task_definition(ctx, tag):
    def _get_td_container_definitions(ctx, family_name, tag):
        return [_get_one_td_c_def(ctx, family_name, i, cc, tag) for i, cc in enumerate(ctx.obj['service']['config']['containers'])]

    def _get_one_td_c_def(ctx, family_name, index, cconfig, tag):
        return {
            'name': cconfig.get('name', '__c'.join([family_name, str(index)])),  # name
            'image': ':'.join([cconfig['image_path'], tag]),  # image FIXME this is just for the first container!
            'cpu': cconfig['cpu'],
            'memory': cconfig['memory'],
            'links': cconfig.get('links', []),
            'portMappings': [_get_one_pm(cc_pm) for cc_pm in cconfig['ports']],  # FIXME
            'essential': cconfig.get('essential') or True,
            'entryPoint': [],
            'command': cconfig['command'],
            'environment': [_get_one_env(ctx, cc_env) for cc_env in cconfig['env']]
        }

    def _get_one_pm(ports_str):
        ports = [p for p in ports_str.split(':') if p not in [None, '', '0']]
        if len(ports) == 2:
            host, container = ports[0], ports[1]
            return {
                'containerPort': int(container),
                'hostPort': int(host)
            }
        elif len(ports) == 1:
            return {'containerPort': int(ports[0])}
        else:
            return {}

    def _get_one_env(ctx, env_name):
        if env_name in ctx.obj['cluster']['config'].get('context', {}):
            value = ctx.obj['cluster']['config']['context'][env_name]
        elif env_name in ctx.obj['service']['config'].get('context', {}):
            value = ctx.obj['service']['config']['context'][env_name]
        elif env_name in ctx.obj['config']['globals']['context']:
            value = ctx.obj['config']['globals']['context'][env_name]
        else:
            raise ValueError('Missing env variable: {0}'.format(env_name))
        return {
            'name': env_name,
            'value': value,
        }

    td_family = _get_td_family_name(ctx)
    result_ = ctx.obj['ecs_conn'].register_task_definition(family=td_family, containerDefinitions=_get_td_container_definitions(ctx, td_family, tag))

    # log(ctx, str(result_))

    new_task_definition = ':'.join([
        result_['taskDefinition']['family'],
        str(result_['taskDefinition']['revision'])
    ])
    log(ctx, 'Registering task definition for tag {tag} tD family: {family} -> {new_td}'.format(tag=tag, family=td_family, new_td=new_task_definition))
    return new_task_definition


def _get_td_family_name(ctx):
    return '__'.join([SCOTTY_PREFIX, ctx.obj['cluster']['name'], ctx.obj['service']['name']])


def _get_services(ctx):
    service_names = _get_service_names(ctx)
    result_ = ctx.obj['ecs_conn'].describe_services(services=service_names, cluster=ctx.obj['cluster']['name'])
    # log(ctx, str(result_))
    services = [service for service in result_['services'] if service['status'] != 'INACTIVE']
    return services


def _get_task_count(ctx):
    return ctx.obj['service']['config'].get(
        'task_count', ctx.obj['cluster']['config'].get(
            'task_count', ctx.obj['config']['globals'].get(
                'task_count', 2))) or 2


def _get_service_names(ctx):
    prefix = _get_td_family_name(ctx)
    return [prefix + '__s' + str(i) for i in range(0, 2)]


def _create_services(ctx, task_def):
    log(ctx, 'Creating services...')
    service_names = _get_service_names(ctx)
    ret = []
    for i, sn in enumerate(service_names):
        result_ = ctx.obj['ecs_conn'].create_service(
            cluster=ctx.obj['cluster']['name'],
            serviceName=sn,
            taskDefinition=task_def,
            desiredCount=_get_task_count(ctx) if i == 0 else 0,  # just the first!
        )
        # log(ctx, str(result_))
        log(ctx, '{0} is created'.format(sn))
        if result_['service']:
            ret.append(result_['service'])
    return ret


def _update_services_with_canary(ctx, service_descriptions, task_def, strategy):

    def _decrement_desired_count(service_name, current_desired_count):
        ctx.obj['ecs_conn'].update_service(
            cluster=ctx.obj['cluster']['name'],
            service=service_name, desiredCount=max(0, current_desired_count - 1))

        log(ctx, '{0}: decrement desired count (-1)'.format(service_name))
        return service_name, current_desired_count - 1, current_desired_count - 1  # FIXME!

    def _increment_desired_count(service_name, current_desired_count, new_task_def):
        ctx.obj['ecs_conn'].update_service(
            cluster=ctx.obj['cluster']['name'],
            service=service_name,
            taskDefinition=new_task_def,
            desiredCount=min(_get_task_count(ctx), current_desired_count + 1))

        log(ctx, '{0}: increment desired count (+1)'.format(service_name))
        return service_name, current_desired_count + 1, current_desired_count + 1  # FIXME!

    _inactive_services = [(sd['serviceName'], sd['runningCount'], sd['desiredCount']) for sd in service_descriptions if sd['desiredCount'] == 0]
    _running_services = [(sd['serviceName'], sd['runningCount'], sd['desiredCount']) for sd in service_descriptions if sd['desiredCount'] > 0]
    if len(_inactive_services) == 1 and len(_running_services) == 1:
        current = _running_services[0]
        canary = _inactive_services[0]
        log(ctx, 'Cluster state is fine. I found 1 "inactive" service and 1 "active" service.')
        log(ctx, 'Starting canary deploy.')
        log(ctx, """Current service is {cu_name} with {cu_running} running and {cu_desired} desired tasks,
      -> Canary service is {ca_name} with {ca_running} running and {ca_desired} desired tasks.
        """.format(
            cu_name=current[0],
            cu_running=current[1],
            cu_desired=current[2],
            ca_name=canary[0],
            ca_running=canary[1],
            ca_desired=canary[2]
        ))
        while current[2] > 0 or canary[2] < _get_task_count(ctx):
            current = _decrement_desired_count(current[0], current[2])
            canary = _increment_desired_count(canary[0], canary[2], task_def)
            sleep(15)  # TODO: check result!

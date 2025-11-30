# -*- mode: Python -*-
TARGET_ARCH = 'arm64'

ENV = 'local'
LOG_LEVEL=os.getenv('LOG_LEVEL', 'INFO')
OPENAI_API_KEY=os.getenv('OPENAI_API_KEY', '')
AWS_ACCESS_KEY_ID=os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY", '')
AWS_REGION=os.getenv('AWS_REGION', 'us-east-1')
REGION=os.getenv('REGION', 'ap-south-1')
LLM_MODEL=os.getenv('LLM_MODEL', 'bedrock/anthropic.claude-3-haiku-20240307-v1:0')
BEDROCK_REGION=os.getenv('BEDROCK_REGION', 'us-east-1')

PLANNER_AGENT_URL=os.getenv('PLANNER_AGENT_URL', 'http://localhost:8081')
LEGAL_AGENT_URL=os.getenv('LEGAL_AGENT_URL', 'http://localhost:8082')

DATABASE_HOST = 'postgresql.real-estate-agentic-ai.svc.cluster.local'
DATABASE_URL = 'postgresql.real-estate-agentic-ai.svc.cluster.local'
DATABASE_USER = 'postgres'
DATABASE_PASSWORD = 'postgres'
DATABASE_NAME = 'real_estate_agents'
DATABASE_PORT = 5432


shared_config_map_data = {
    'LOG_LEVEL': LOG_LEVEL,
    'ENV': ENV,
    'OPENAI_API_KEY': OPENAI_API_KEY,
    'AWS_ACCESS_KEY_ID': AWS_ACCESS_KEY_ID,
    'AWS_SECRET_ACCESS_KEY': AWS_SECRET_ACCESS_KEY,
    'AWS_REGION': AWS_REGION,
    'REGION': REGION,
    'LLM_MODEL': LLM_MODEL,
    'BEDROCK_REGION': BEDROCK_REGION,
    'LEGAL_AGENT_URL': LEGAL_AGENT_URL,
    'PLANNER_AGENT_URL': PLANNER_AGENT_URL,
}


postgres_config_map_data = {
    'DATABASE_HOST': DATABASE_HOST,
    'DATABASE_URL': DATABASE_URL,
    'POSTGRES_USER': DATABASE_USER,
    'POSTGRES_PASSWORD': DATABASE_PASSWORD,
    'POSTGRES_DB': DATABASE_NAME,
}


load('ext://namespace', 'namespace_create', 'namespace_inject')

namespace = 'real-estate-agentic-ai'
namespace_create(namespace)
load('ext://configmap', 'configmap_from_dict')

shared_configmap = configmap_from_dict('shared-config', inputs=shared_config_map_data)
k8s_yaml(namespace_inject(shared_configmap, namespace))

postgres_configmap = configmap_from_dict('postgres-config', inputs=postgres_config_map_data)
k8s_yaml(namespace_inject(postgres_configmap, namespace))

yaml = kustomize('./infra-as-code/k8s/tilt')
k8s_yaml(namespace_inject(yaml, namespace))
k8s_resource('postgresql', port_forwards='5432:5432')


# Database Migration - using direct psql command
local_resource(
  'db-migration',
  cmd='sleep 5 && PGPASSWORD=%s psql -h localhost -p %s -U %s -d %s -f backend/shared/database/migrations/001_init.sql' % (DATABASE_PASSWORD, DATABASE_PORT, DATABASE_USER, DATABASE_NAME),
  resource_deps=['postgresql'],
  labels=['database'],
  auto_init=True,
  trigger_mode=TRIGGER_MODE_MANUAL,
)

# Watch migration files for changes
watch_file('backend/shared/database/migrations/')




docker_build('backend-api', './backend',
    dockerfile='./backend/api/Dockerfile',
    target='localdev',
    live_update=[
        sync('./backend/api', '/workspace/api'),
    ], build_args={
        'TARGET_ARCH': TARGET_ARCH,
    })

docker_build('planner-agent', './backend',
    dockerfile='./backend/agents/planner/Dockerfile',
    target='localdev',
    live_update=[
        sync('./backend/agents/planner', '/workspace/agents/planner'),
    ], build_args={
        'TARGET_ARCH': TARGET_ARCH,
    })

docker_build('legal-agent', './backend',
    dockerfile='./backend/agents/legal/Dockerfile',
    target='localdev',
    live_update=[
        sync('./backend/agents/legal', '/workspace/agents/legal'),
    ], build_args={
        'TARGET_ARCH': TARGET_ARCH,
    })

k8s_resource('backend-api', port_forwards='8080:8080')
k8s_resource('planner-agent', port_forwards='8081:8081')
k8s_resource('legal-agent', port_forwards='8082:8082')
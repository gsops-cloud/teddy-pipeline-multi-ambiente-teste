#!/usr/bin/env python3

import argparse
import boto3
import sys
import time
from typing import Dict, Any

def get_current_task_definition(ecs_client, cluster_name: str, service_name: str) -> str:
    try:
        response = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        if not response['services']:
            raise Exception(f"Serviço {service_name} não encontrado no cluster {cluster_name}")
        
        service = response['services'][0]
        task_def_arn = service['taskDefinition']
        
        print(f"Task definition atual: {task_def_arn}")
        return task_def_arn
    except Exception as e:
        print(f"Erro ao obter task definition atual: {str(e)}", file=sys.stderr)
        sys.exit(1)

def get_task_definition_details(ecs_client, task_def_arn: str) -> Dict[str, Any]:
    try:
        response = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
        return response['taskDefinition']
    except Exception as e:
        print(f"Erro ao obter detalhes da task definition: {str(e)}", file=sys.stderr)
        sys.exit(1)

def update_task_definition_image(task_def: Dict[str, Any], new_image_tag: str, base_image: str = None) -> Dict[str, Any]:
    new_task_def = {
        'family': task_def['family'],
        'containerDefinitions': [],
        'requiresCompatibilities': task_def.get('requiresCompatibilities', ['FARGATE']),
        'cpu': task_def.get('cpu'),
        'memory': task_def.get('memory'),
        'networkMode': task_def.get('networkMode', 'awsvpc'),
        'executionRoleArn': task_def.get('executionRoleArn'),
        'taskRoleArn': task_def.get('taskRoleArn'),
    }
    
    if 'volumes' in task_def:
        new_task_def['volumes'] = task_def['volumes']
    if 'placementConstraints' in task_def:
        new_task_def['placementConstraints'] = task_def['placementConstraints']
    
    for container in task_def['containerDefinitions']:
        new_container = container.copy()
        for field in ['containerArn', 'taskArn', 'lastStatus', 'name']:
            if field in new_container and field != 'name':
                del new_container[field]
        
        if base_image:
            new_container['image'] = f"{base_image}:{new_image_tag}"
        elif ':' in new_image_tag:
            new_container['image'] = new_image_tag
        else:
            current_image = container['image']
            image_parts = current_image.split(':')
            base = image_parts[0] if ':' in current_image else current_image
            new_container['image'] = f"{base}:{new_image_tag}"
        
        print(f"Atualizando imagem do container '{container['name']}': {container['image']} -> {new_container['image']}")
        new_task_def['containerDefinitions'].append(new_container)
    
    return new_task_def

def register_new_task_definition(ecs_client, new_task_def: Dict[str, Any]) -> str:
    try:
        cleaned_task_def = {k: v for k, v in new_task_def.items() if v is not None}
        response = ecs_client.register_task_definition(**cleaned_task_def)
        new_task_def_arn = response['taskDefinition']['taskDefinitionArn']
        print(f"Nova task definition registrada: {new_task_def_arn}")
        return new_task_def_arn
    except Exception as e:
        print(f"Erro ao registrar nova task definition: {str(e)}", file=sys.stderr)
        sys.exit(1)

def update_service(ecs_client, cluster_name: str, service_name: str, task_def_arn: str) -> None:
    try:
        print(f"Atualizando serviço {service_name} no cluster {cluster_name}...")
        response = ecs_client.update_service(
            cluster=cluster_name,
            service=service_name,
            taskDefinition=task_def_arn,
            forceNewDeployment=True
        )
        
        deployment_id = response['service']['deployments'][0]['id']
        print(f"Deploy iniciado. Deployment ID: {deployment_id}")
        
        wait_for_deployment(ecs_client, cluster_name, service_name, deployment_id)
        
    except Exception as e:
        print(f"Erro ao atualizar serviço: {str(e)}", file=sys.stderr)
        sys.exit(1)

def wait_for_deployment(ecs_client, cluster_name: str, service_name: str, deployment_id: str, timeout: int = 600) -> None:
    print("Aguardando deployment completar...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = ecs_client.describe_services(
                cluster=cluster_name,
                services=[service_name]
            )
            
            service = response['services'][0]
            deployment = next((d for d in service['deployments'] if d['id'] == deployment_id), None)
            
            if not deployment:
                print("Deployment não encontrado. Pode ter sido substituído por outro.")
                break
            
            status = deployment['status']
            running_count = deployment['runningCount']
            desired_count = deployment['desiredCount']
            
            print(f"Status: {status}, Running: {running_count}/{desired_count}")
            
            if status == 'PRIMARY' and running_count == desired_count:
                print("Deployment concluído com sucesso!")
                return
            elif status == 'FAILED':
                raise Exception("Deployment falhou!")
            
            time.sleep(10)
        except Exception as e:
            print(f"Erro ao verificar status do deployment: {str(e)}", file=sys.stderr)
            raise
    
    raise Exception(f"Timeout aguardando deployment (>{timeout}s)")

def rollback_service(ecs_client, cluster_name: str, service_name: str, previous_image_tag: str, base_image: str = None) -> None:
    print(f"Realizando rollback para imagem tag: {previous_image_tag}")
    
    current_task_def_arn = get_current_task_definition(ecs_client, cluster_name, service_name)
    current_task_def = get_task_definition_details(ecs_client, current_task_def_arn)
    
    new_task_def = update_task_definition_image(current_task_def, previous_image_tag, base_image)
    new_task_def_arn = register_new_task_definition(ecs_client, new_task_def)
    
    update_service(ecs_client, cluster_name, service_name, new_task_def_arn)

def main():
    parser = argparse.ArgumentParser(description='Deploy de serviço no ECS')
    parser.add_argument('--environment', required=True, choices=['dev', 'staging', 'prod'])
    parser.add_argument('--image-tag', required=True)
    parser.add_argument('--base-image')
    parser.add_argument('--action', choices=['deploy', 'rollback'], default='deploy')
    parser.add_argument('--cluster-name')
    parser.add_argument('--service-name')
    parser.add_argument('--region', default='us-east-1')
    
    args = parser.parse_args()
    
    cluster_name = args.cluster_name or f"teddy-cluster-{args.environment}"
    service_name = args.service_name or f"teddy-service-{args.environment}"
    
    ecs_client = boto3.client('ecs', region_name=args.region)
    
    try:
        if args.action == 'rollback':
            rollback_service(ecs_client, cluster_name, service_name, args.image_tag, args.base_image)
        else:
            current_task_def_arn = get_current_task_definition(ecs_client, cluster_name, service_name)
            current_task_def = get_task_definition_details(ecs_client, current_task_def_arn)
            
            new_task_def = update_task_definition_image(current_task_def, args.image_tag, args.base_image)
            new_task_def_arn = register_new_task_definition(ecs_client, new_task_def)
            
            update_service(ecs_client, cluster_name, service_name, new_task_def_arn)
        
        print("Deploy concluído com sucesso!")
    except Exception as e:
        print(f"Erro durante deploy: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
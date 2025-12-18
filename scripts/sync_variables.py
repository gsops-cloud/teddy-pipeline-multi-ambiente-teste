#!/usr/bin/env python3

import argparse
import boto3
import os
import sys
from typing import Dict

def get_ci_variables(environment: str) -> Dict[str, str]:
    prefix = f"{environment.upper()}_"
    variables = {}
    
    for key, value in os.environ.items():
        if key.startswith(prefix):
            param_name = key[len(prefix):].lower()
            if value and value.strip():
                variables[param_name] = value
            else:
                print(f"Ignorando variável vazia: {key}")
    
    return variables

def sync_to_aws_ssm(environment: str, variables: Dict[str, str], region: str = "us-east-1") -> None:
    ssm_client = boto3.client('ssm', region_name=region)
    base_path = f"/teddy/{environment}"
    
    print(f"Sincronizando variáveis para AWS SSM em {base_path}...")
    
    filtered_variables = {k: v for k, v in variables.items() if v and v.strip()}
    
    if not filtered_variables:
        print(f"Nenhuma variável válida encontrada para sincronizar (variáveis vazias foram ignoradas)")
        return
    
    print(f"Encontradas {len(filtered_variables)} variáveis válidas para sincronizar")
    
    for key, value in filtered_variables.items():
        param_name = f"{base_path}/{key}"
        
        try:
            try:
                existing = ssm_client.get_parameter(Name=param_name)
                if existing['Parameter']['Value'] != value:
                    print(f"Atualizando parâmetro: {param_name}")
                    ssm_client.put_parameter(
                        Name=param_name,
                        Value=value,
                        Type='SecureString' if 'secret' in key.lower() or 'password' in key.lower() else 'String',
                        Overwrite=True
                    )
                else:
                    print(f"Parâmetro já está sincronizado: {param_name}")
            except ssm_client.exceptions.ParameterNotFound:
                print(f"Criando novo parâmetro: {param_name}")
                ssm_client.put_parameter(
                    Name=param_name,
                    Value=value,
                    Type='SecureString' if 'secret' in key.lower() or 'password' in key.lower() else 'String'
                )
        except Exception as e:
            print(f"Erro ao sincronizar {param_name}: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    print("Sincronização concluída com sucesso!")

def sync_from_aws_ssm(environment: str, region: str = "us-east-1") -> Dict[str, str]:
    ssm_client = boto3.client('ssm', region_name=region)
    base_path = f"/teddy/{environment}"
    
    print(f"Obtendo variáveis do AWS SSM em {base_path}...")
    
    variables = {}
    try:
        paginator = ssm_client.get_paginator('get_parameters_by_path')
        page_iterator = paginator.paginate(Path=base_path, Recursive=True)
        
        for page in page_iterator:
            for param in page['Parameters']:
                key = param['Name'].replace(f"{base_path}/", "")
                variables[key] = param['Value']
        
        print(f"Encontradas {len(variables)} variáveis no AWS SSM")
    except Exception as e:
        print(f"Erro ao obter variáveis do AWS SSM: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    return variables

def main():
    parser = argparse.ArgumentParser(description='Sincronizar variáveis entre CI/CD e AWS')
    parser.add_argument('--environment', required=True, choices=['dev', 'staging', 'prod'])
    parser.add_argument('--direction', choices=['to-aws', 'from-aws'], default='to-aws')
    parser.add_argument('--region', default='us-east-1')
    
    args = parser.parse_args()
    
    if args.direction == 'to-aws':
        variables = get_ci_variables(args.environment)
        if not variables:
            print(f"Nenhuma variável encontrada com prefixo {args.environment.upper()}_")
            return
        
        sync_to_aws_ssm(args.environment, variables, args.region)
    else:
        variables = sync_from_aws_ssm(args.environment, args.region)
        for key, value in variables.items():
            env_var = f"{args.environment.upper()}_{key.upper()}"
            print(f"export {env_var}='{value}'")

if __name__ == "__main__":
    main()
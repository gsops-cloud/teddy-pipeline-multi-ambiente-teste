#!/usr/bin/env python3

import argparse
import os
import sys
from twilio.rest import Client
from datetime import datetime

def send_whatsapp_message(
    account_sid: str,
    auth_token: str,
    from_number: str,
    to_number: str,
    message: str
) -> bool:
    try:
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            from_=f'whatsapp:{from_number}',
            body=message,
            to=f'whatsapp:{to_number}'
        )
        
        print(f"Mensagem enviada com sucesso! SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Erro ao enviar mensagem WhatsApp: {str(e)}", file=sys.stderr)
        return False

def format_deployment_message(environment: str, status: str, commit: str, pipeline_url: str = None) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    status_emoji = "✅" if status == "success" else "❌"
    status_text = "SUCESSO" if status == "success" else "FALHA"
    
    message = f"""
{status_emoji} *Deploy {status_text}*

*Ambiente:* {environment.upper()}
*Status:* {status_text}
*Commit:* {commit}
*Data/Hora:* {timestamp}
"""
    
    if pipeline_url:
        message += f"*Pipeline:* {pipeline_url}\n"
    
    if status == "failed":
        message += "\n⚠️ *Ação necessária:* Verifique os logs da pipeline e corrija os problemas antes de tentar novamente."
    else:
        message += "\n🎉 Deploy concluído com sucesso!"
    
    return message.strip()

def main():
    parser = argparse.ArgumentParser(description='Enviar notificação WhatsApp via Twilio')
    parser.add_argument('--environment', required=True, choices=['dev', 'staging', 'prod'])
    parser.add_argument('--status', required=True, choices=['success', 'failed'])
    parser.add_argument('--commit', required=True)
    parser.add_argument('--pipeline-url')
    parser.add_argument('--twilio-account-sid', default=os.getenv('TWILIO_ACCOUNT_SID'))
    parser.add_argument('--twilio-auth-token', default=os.getenv('TWILIO_AUTH_TOKEN'))
    parser.add_argument('--twilio-from', default=os.getenv('TWILIO_WHATSAPP_FROM'))
    parser.add_argument('--twilio-to', default=os.getenv('TWILIO_WHATSAPP_TO'))
    
    args = parser.parse_args()
    
    if not all([args.twilio_account_sid, args.twilio_auth_token, args.twilio_from, args.twilio_to]):
        print("ERRO: Credenciais Twilio não fornecidas!", file=sys.stderr)
        sys.exit(1)
    
    pipeline_url = args.pipeline_url or os.getenv('CI_PIPELINE_URL', '')
    message = format_deployment_message(
        environment=args.environment,
        status=args.status,
        commit=args.commit,
        pipeline_url=pipeline_url
    )
    
    print(f"Enviando notificação para {args.twilio_to}...")
    
    success = send_whatsapp_message(
        account_sid=args.twilio_account_sid,
        auth_token=args.twilio_auth_token,
        from_number=args.twilio_from,
        to_number=args.twilio_to,
        message=message
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
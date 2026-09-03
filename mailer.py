import random
import os

def generate_verification_code():
    """Gera um código de verificação numérico de 6 dígitos."""
    return str(random.randint(100000, 999999))

def send_verification_email(email, code):
    """
    Simula / Envia e-mail com código de confirmação.
    Exibe no console e logs para testes de desenvolvimento rápidos.
    """
    print("==========================================================")
    print(f" 📧 E-MAIL DE VERIFICAÇÃO ENVIADO PARA: {email}")
    print(f" 🔑 CÓDIGO DE CONFIRMAÇÃO: {code}")
    print("==========================================================")
    
    # Se houver configuração SMTP de ambiente, envia via smtplib
    smtp_host = os.environ.get("SMTP_HOST")
    if smtp_host:
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            msg = MIMEText(f"Seu código de confirmação de cadastro na BiblioTech é: {code}")
            msg['Subject'] = "BiblioTech - Código de Confirmação"
            msg['From'] = os.environ.get("SMTP_FROM", "noreply@bibliotech.com")
            msg['To'] = email
            
            with smtplib.SMTP(smtp_host, int(os.environ.get("SMTP_PORT", 587))) as server:
                server.starttls()
                server.login(os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASS"))
                server.sendmail(msg['From'], [email], msg.as_string())
            print(f"E-mail real entregue a {email}")
        except Exception as e:
            print(f"Aviso ao enviar e-mail via SMTP real: {e}")
            
    return True

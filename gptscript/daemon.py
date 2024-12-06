import base64
import ssl
import os
import tempfile


def start_uvicorn(app):
    cert, key, client_cert = save_certificates_from_env()

    @app.on_event("shutdown")
    def cleanup():
        os.remove(cert)
        os.remove(key)
        os.remove(client_cert)

    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.getenv("PORT")),
        ssl_certfile=cert,
        ssl_keyfile=key,
        ssl_ca_certs=client_cert,
        ssl_cert_reqs=ssl.CERT_REQUIRED,
    )

def save_certificates_from_env():
    cert = base64.b64decode(os.getenv("CERT", ""))
    key = base64.b64decode(os.getenv("PRIVATE_KEY", ""))
    client_cert = base64.b64decode(os.getenv("GPTSCRIPT_CERT", ""))

    if cert == "":
        print("error: CERT env var is empty")
        exit(1)
    elif key == "":
        print("error: PRIVATE_KEY env var is empty")
        exit(1)
    elif client_cert == "":
        print("error: GPTSCRIPT_CERT env var is empty")
        exit(1)

    cert_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    key_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    client_cert_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")

    os.chmod(cert_file.name, 0o600)
    os.chmod(key_file.name, 0o600)
    os.chmod(client_cert_file.name, 0o600)

    cert_file.write(cert)
    key_file.write(key)
    client_cert_file.write(client_cert)

    cert_file.close()
    key_file.close()
    client_cert_file.close()

    return cert_file.name, key_file.name, client_cert_file.name

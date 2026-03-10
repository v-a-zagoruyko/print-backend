import base64

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def test_qz_sign_requires_post(client):
    resp = client.get("/qz/sign/")
    assert resp.status_code == 405


def test_qz_sign_empty_body_returns_400(client):
    resp = client.post("/qz/sign/", data=b"", content_type="application/octet-stream")
    assert resp.status_code == 400


def test_qz_sign_returns_base64_signature(client, settings, tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    private_key_path = tmp_path / "private-key.pem"
    private_key_path.write_bytes(pem)
    settings.QZ_PRIVATE_KEY_PATH = str(private_key_path)

    payload = b"hello"
    resp = client.post("/qz/sign/", data=payload, content_type="application/octet-stream")
    assert resp.status_code == 200
    sig_b64 = resp.content.decode("ascii")
    sig = base64.b64decode(sig_b64, validate=True)
    assert isinstance(sig, (bytes, bytearray))
    assert len(sig) > 0


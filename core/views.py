import redis
import base64
import logging
from django.shortcuts import redirect
from django.db.utils import OperationalError
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from django.conf import settings
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils.health import check_db, check_redis, check_celery
from .utils.redirect import is_allowed_redirect_url

logger = logging.getLogger(__name__)

@api_view(['GET'])
def health(request):
    status = {"db": True, "redis": True, "celery": True, "status": "ok"}

    try:
        check_db()
    except OperationalError as e:
        status["db"] = False
        status["status"] = "error"
        logger.error("DB health check failed", exc_info=e)

    try:
        check_redis()
    except redis.exceptions.RedisError as e:
        status["redis"] = False
        status["status"] = "error"
        logger.error("Redis health check failed", exc_info=e)

    try:
        if not check_celery():
            status["celery"] = False
            status["status"] = "error"
            logger.error("Celery health check failed: no workers responding")
    except Exception as e:
        status["celery"] = False
        status["status"] = "error"
        logger.error("Celery health check failed", exc_info=e)

    return Response(status)

def qz_cert(request):
    with open(settings.BASE_DIR / "core/static/certs/digital-certificate.txt") as f:
        resp = HttpResponse(f.read(), content_type="text/plain")
    return resp

@require_POST
@csrf_exempt
def qz_sign(request):
    private_key_path = getattr(settings, "QZ_PRIVATE_KEY_PATH", None)
    if not private_key_path:
        private_key_path = (
            str(settings.BASE_DIR / "private-key.pem")
            if settings.DEBUG
            else "/app/certs/private-key.pem"
        )
    to_sign = request.body
    if not to_sign:
        return HttpResponseBadRequest("Missing request")
    with open(private_key_path, "rb") as f:
        key = serialization.load_pem_private_key(f.read(), password=None)
    signature = key.sign(to_sign, padding.PKCS1v15(), hashes.SHA512())
    return HttpResponse(base64.b64encode(signature).decode("ascii"), content_type="text/plain")

def post_login_redirect(request):
    dest = request.GET.get('url') or request.POST.get('url')
    if not dest:
        return redirect('admin:index')
    if not is_allowed_redirect_url(dest):
        logger.warning(f"Attempt to redirect on forbidden URL: {dest}, User: {request.user.username}")
        return redirect('admin:index')
    return redirect(dest)

import logging
import base64
import urllib.parse
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from main.models import BaseInfo, Template, Product, Contractor
from core.settings import BASE_DIR, DEBUG
from .serializers import (
    UserInfoModelSerializer,
    TemplatePayloadSerializer,
    ProductPayloadSerializer,
    ContractorPayloadSerializer,
    ProductTemplateSerializer,
    ProductTemplateListSerializer,
    ContractorTemplateSerializer,
    ContractorTemplateListSerializer
)
from .services.label_service import label_service
from .permissions import IsPrintOperator, IsContractor
from .utils.admin import admin_has_change_perm, admin_change_url
from .utils.format import extract_template_from_mapping

logger = logging.getLogger(__name__)


class InfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        info = BaseInfo.get_solo()
        if not info:
            return Response({}, status=404)
        result = {
            "company_name": info.name,
            "username": request.user.username,
            "is_staff": request.user.is_staff,
            "is_superuser": request.user.is_superuser,
            "groups": list(request.user.groups.values_list('name', flat=True)),
        }
        serializer = UserInfoModelSerializer(data=result)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class TemplateLabelViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='template')
    def template(self, request):
        serializer = TemplatePayloadSerializer(instance=request.data)
        image = label_service.generate_template_png_preview_base64(serializer.data)
        return Response({'image': image})

    @action(detail=False, methods=['post'], url_path='product')
    def product(self, request):
        serializer = ProductPayloadSerializer(instance=request.data)
        template = extract_template_from_mapping(request.data)

        if not template:
            logger.error("Missing field: template")
            return Response({'error': 'Missing field: template'}, status=400)

        image = label_service.generate_png_preview_base64(template, serializer.data)
        pdf = label_service.generate_pdf_preview_base64(template, serializer.data)
        return Response({'image': image, 'pdf': pdf})

    @action(detail=False, methods=['post'], url_path='contractor')
    def contractor(self, request):
        serializer = ContractorPayloadSerializer(instance=request.data)
        template = extract_template_from_mapping(request.data)

        if not template:
            logger.error("Missing field: template")
            return Response({'error': 'Missing field: template'}, status=400)

        image = label_service.generate_png_preview_base64(template, serializer.data)
        pdf = label_service.generate_pdf_preview_base64(template, serializer.data)
        return Response({'image': image, 'pdf': pdf})


class ProductLabelViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsPrintOperator]

    def list(self, request):
        products = (
            Product.objects
            .filter(status=Product.ProductStatus.AVAILABLE)
            .select_related('category',)
            .prefetch_related('org_standart__org_standart')
        )

        results = []
        for product in products:
            res = {
                "id": product.pk,
                "template": product.entity_template.template.name,
                "name": product.name,
                "category": getattr(product.category, 'name', None),
            }
            if admin_has_change_perm(request.user, Product):
                res["edit_url"] = request.build_absolute_uri(admin_change_url(Product, product.pk))
            results.append(res)
        return Response(ProductTemplateListSerializer(results, many=True).data)

    def retrieve(self, request, pk=None):
        product = get_object_or_404(Product, id=pk)
        serializer = ProductPayloadSerializer(instance=product, context={'request': request})
        pdf = label_service.generate_pdf_preview_base64(product.entity_template.template, serializer.data)

        result = {
            "name": product.name,
            "category": getattr(product.category, 'name', None),
            "pdf": pdf,
        }
        return Response(ProductTemplateSerializer(result).data)


class ContractorLabelViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsPrintOperator]

    def list(self, request):
        contractors = (
            Contractor.objects
            .all()
            .select_related('category')
            .prefetch_related('category')
        )

        results = []
        for contractor in contractors:
            res = {
                "id": contractor.pk,
                "name": contractor.name,
                "street": contractor.street,
                "category": getattr(contractor.category, 'name', None),
            }
            if admin_has_change_perm(request.user, Contractor):
                res["edit_url"] = request.build_absolute_uri(admin_change_url(Contractor, contractor.pk))
            results.append(res)
        return Response(ContractorTemplateListSerializer(results, many=True).data)

    def retrieve(self, request, pk=None):
        contractor = get_object_or_404(Contractor, id=pk)
        serializer = ContractorPayloadSerializer(instance=contractor)
        pdf = label_service.generate_pdf_preview_base64(contractor.entity_template.template, serializer.data)

        result = {
            "name": contractor.name,
            "category": getattr(contractor.category, 'name', None),
            "pdf": pdf,
        }
        return Response(ContractorTemplateSerializer(result).data)


def qz_cert(request):
    with open(BASE_DIR / "api/static/certs/digital-certificate.txt") as f:
        resp = HttpResponse(f.read(), content_type="text/plain")
    return resp


@require_POST
@csrf_exempt
def qz_sign(request):
    if DEBUG:
        PRIVATE_KEY_PATH = BASE_DIR / "private-key.pem"
    else:
        print('*'*100)
        PRIVATE_KEY_PATH = "/app/certs/private-key.pem"
    to_sign = request.body
    if not to_sign:
        return HttpResponseBadRequest("Missing request")
    with open(PRIVATE_KEY_PATH, "rb") as f:
        key = serialization.load_pem_private_key(f.read(), password=None)
    signature = key.sign(to_sign, padding.PKCS1v15(), hashes.SHA512())
    return HttpResponse(base64.b64encode(signature).decode("ascii"), content_type="text/plain")

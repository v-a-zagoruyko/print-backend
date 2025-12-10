import logging
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from main.models import Template, Product, Contractor
from .serializers import (
    TemplatePayloadSerializer,
    ProductPayloadSerializer,
    ContractorPayloadSerializer,
    ProductModelSerializer,
    ProductLabelSerializer,
    ProductLabelListSerializer,
    ContractorModelSerializer,
    ContractorLabelSerializer,
    ContractorLabelListSerializer
)
from .services.label_service import label_service

logger = logging.getLogger(__name__)


class LabelPreviewViewSet(ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='template')
    def template(self, request):
        serializer = TemplatePayloadSerializer(instance=request.data)
        image = label_service.generate_template_png_preview_base64(serializer.data)
        return Response({'image': image})

    @action(detail=False, methods=['post'], url_path='product')
    def product(self, request):
        serializer = ProductPayloadSerializer(instance=request.data)

        if 'template' not in request.data:
            logger.error("Missing field: template")
            return Response({'error': 'Missing field: template'}, status=400)

        template = get_object_or_404(Template, id=request.data['template'])
        image = label_service.generate_png_preview_base64(template, serializer.data)
        pdf = label_service.generate_pdf_preview_base64(template, serializer.data)
        return Response({'image': image, 'pdf': pdf})

    @action(detail=False, methods=['post'], url_path='contractor')
    def contractor(self, request):
        serializer = ContractorPayloadSerializer(instance=request.data)

        if 'template' not in request.data:
            logger.error("Missing field: template")
            return Response({'error': 'Missing field: template'}, status=400)

        template = get_object_or_404(Template, id=request.data['template'])
        image = label_service.generate_png_preview_base64(template, serializer.data)
        pdf = label_service.generate_pdf_preview_base64(template, serializer.data)
        return Response({'image': image, 'pdf': pdf})


class ProductLabelViewSet(ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        products = (
            Product.objects
            .all()
            .select_related('category', 'template')
            .prefetch_related('org_standart__org_standart')
        )

        results = []
        for product in products:
            serializer = ProductModelSerializer(product)

            results.append({
                "id": product.pk,
                "name": product.name,
                "category": getattr(product.category, 'name', None),
            })
        return Response(ProductLabelListSerializer(results, many=True).data)

    def retrieve(self, request, pk=None):
        product = get_object_or_404(Product, id=pk)
        template = getattr(product, 'template', None)
        serializer = ProductPayloadSerializer(instance=product)
        pdf = label_service.generate_pdf_preview_base64(template, serializer.data)

        result = {
            "name": product.name,
            "category": getattr(product.category, 'name', None),
            "pdf": pdf,
        }
        return Response(ProductLabelSerializer(result).data)


class ContractorLabelViewSet(ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        contractors = (
            Contractor.objects
            .all()
            .select_related('category', 'template')
            .prefetch_related('category')
        )

        results = []
        for contractor in contractors:
            serializer = ContractorModelSerializer(contractor)

            results.append({
                "id": contractor.pk,
                "name": contractor.name,
                "street": contractor.street,
                "category": getattr(contractor.category, 'name', None),
            })
        return Response(ContractorLabelListSerializer(results, many=True).data)

    def retrieve(self, request, pk=None):
        contractor = get_object_or_404(Contractor, id=pk)
        template = getattr(contractor, 'template', None)
        serializer = ContractorPayloadSerializer(instance=contractor)
        pdf = label_service.generate_pdf_preview_base64(template, serializer.data)

        result = {
            "name": contractor.name,
            "category": getattr(contractor.category, 'name', None),
            "pdf": pdf,
        }
        return Response(ContractorLabelSerializer(result).data)

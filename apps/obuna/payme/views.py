"""
Payme Merchant API webhook.

Payme barcha metodlarni bitta endpointga JSON-RPC 2.0 formatida yuboradi.
Autentifikatsiya — HTTP Basic Auth:
    login: "Paycom"
    parol: settings.PAYME_KEY
"""
import base64
import json

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from . import exceptions as exc
from .service import PaymeService


@method_decorator(csrf_exempt, name="dispatch")
class PaymeWebhookView(APIView):
    """Payme JSON-RPC webhook endpointi."""
    permission_classes = [AllowAny]
    authentication_classes = []  # Payme JWT emas, Basic Auth ishlatadi

    @extend_schema(exclude=True)
    def post(self, request):
        rpc_id = None
        try:
            self._check_auth(request)

            payload = self._parse_body(request)
            rpc_id = payload.get("id")
            method = payload.get("method")
            params = payload.get("params", {}) or {}

            if not method:
                raise exc.InvalidJsonRPC(data="method")

            result = PaymeService().call(method, params)
            return Response({"result": result, "id": rpc_id})

        except exc.PaymeError as e:
            return Response({"error": e.as_rpc_error(), "id": rpc_id})

    # ===== Yordamchilar =====
    def _check_auth(self, request):
        """Payme Basic Auth: login 'Paycom', parol PAYME_KEY."""
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith("Basic "):
            raise exc.InsufficientPrivilege(data="auth")

        try:
            decoded = base64.b64decode(header[6:]).decode("utf-8")
            login, _, password = decoded.partition(":")
        except Exception:
            raise exc.InsufficientPrivilege(data="auth")

        if login != "Paycom" or password != settings.PAYME_KEY or not settings.PAYME_KEY:
            raise exc.InsufficientPrivilege(data="auth")

    def _parse_body(self, request) -> dict:
        try:
            if isinstance(request.data, dict) and request.data:
                return request.data
            return json.loads(request.body.decode("utf-8"))
        except Exception:
            raise exc.InvalidJsonRPC(data="json")

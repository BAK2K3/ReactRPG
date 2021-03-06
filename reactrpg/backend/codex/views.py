from .models import Codex
from rest_framework import permissions, viewsets
from .serializers import CodexSerializer


class CodexViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Codex to be viewed.
    """
    queryset = Codex.objects.filter_queryset({}, 'pk')
    serializer_class = CodexSerializer
    permission_classes = [permissions.IsAuthenticated]


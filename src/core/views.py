from rest_framework import viewsets

from users.activity_log import ActivityLogMixin


class CustomModelViewSet(ActivityLogMixin, viewsets.ModelViewSet):
    pass

import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from rest_framework.exceptions import ValidationError

from users.models import CREATE
from users.models import DELETE
from users.models import FAILED
from users.models import READ
from users.models import SUCCESS
from users.models import UPDATE
from users.models import UserActionLog
from users.utils import create_message
from users.utils import get_action_name


class ActivityLogMixin:
    """
    Mixin to track user actions
    :cvar log_message:
        Log message to populate remarks in LogAction
        type --> str
        set this value or override get_log_message
        If not set then, default log message is generated
    """

    log_message = None

    def _get_action_type(self, request) -> str:
        return self.action_type_mapper().get(f"{request.method.upper()}")

    @staticmethod
    def action_type_mapper():
        return {
            "GET": READ,
            "POST": CREATE,
            "PUT": UPDATE,
            "PATCH": UPDATE,
            "DELETE": DELETE,
        }

    @staticmethod
    def _get_user(request):
        return request.user if request.user.is_authenticated else None

    def _write_log(self, request, response):
        action_type = self._get_action_type(request)
        if action_type in [READ, DELETE]:
            return
        object_ids = None
        if isinstance(response.data.get("data"), list):
            object_ids = [item.get("id") for item in response.data.get("data") if "id" in item]
        elif action_type == UPDATE:
            if self.kwargs.get("pk"):
                object_ids = [self.kwargs.get("pk")]
        elif action_type == CREATE:
            object_ids = [response.data.get("id")]
        # elif action_type == DELETE:
        #     object_ids = [self.instance.id]

        status = SUCCESS if response.status_code < 400 else FAILED
        actor = self._get_user(request)

        if actor and not getattr(settings, "TESTING", False):
            logging.info("Started Log Entry")
            model = self.get_queryset().model
            data = {
                "user": actor,
                "action_type": action_type,
                "status": status,
            }
            objs = None
            if action_type != DELETE:
                objs = model.objects.filter(id__in=object_ids)
            # else:
            #     objs = [self.instance]

            for obj in objs:
                message = create_message(action_type, model.__name__, obj)

                try:
                    content_type = ContentType.objects.get_for_model(model)
                    data["object_id"] = obj.id
                    data["content_type"] = content_type
                    data["action_name"] = get_action_name(content_type.app_label)
                    data["content_object"] = obj
                except (AttributeError, ValidationError):
                    data["content_type"] = None
                except AssertionError:
                    pass
                data["message"] = message

                UserActionLog.objects.create(**data)  # send memphis here

    def finalize_response(self, request, *args, **kwargs):
        response = super().finalize_response(request, *args, **kwargs)
        try:
            self._write_log(request, response)
        except Exception as e:
            logging.error("Error in logging: %s", e)
        return response

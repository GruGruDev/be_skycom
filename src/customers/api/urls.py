from django.urls import path
from rest_framework.routers import DefaultRouter

from customers.api.views import BulkAddUsersToGroupView
from customers.api.views import BulkRemoveUsersGroupView
from customers.api.views import CustomerGroupMemberCreateDestroyView
from customers.api.views import CustomerGroupView
from customers.api.views import CustomerHistoryViewset
from customers.api.views import CustomerPhoneCreateDestroyView
from customers.api.views import CustomerRankViewSet
from customers.api.views import CustomerTagDetailCreateDestroyView
from customers.api.views import CustomerTagView
from customers.api.views import CustomerViewSet

router = DefaultRouter()
router.register("tags", CustomerTagView, basename="customer-tags")
router.register("tags/detail", CustomerTagDetailCreateDestroyView, basename="customer-tags-detail")
router.register("groups", CustomerGroupView, basename="customer-groups")
router.register("groups/member", CustomerGroupMemberCreateDestroyView, basename="customer-groups-members")
router.register("phones", CustomerPhoneCreateDestroyView, basename="customer-phones")
router.register("history", CustomerHistoryViewset, basename="customers-history")
router.register("ranks", CustomerRankViewSet, basename="customerrankviewset")
router.register("", CustomerViewSet, basename="customers")


urlpatterns = [
    path("groups/bulk-add-customers", BulkAddUsersToGroupView.as_view(), name="bulk-add-customers-to-gr"),
    path("groups/bulk-remove-customers", BulkRemoveUsersGroupView.as_view(), name="bulk-remove-customers-gr"),
    *router.urls,
]

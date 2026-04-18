from django.urls import path, include

from api.views.travel_metrics import TravelMetricsView

urlpatterns = [
    path("branch/", include("api.branch.urls")),
    path("courier/", include("api.courier.urls")),
    path("customer/", include("api.customer.urls")),

    # Services
    path("travel-metrics/", TravelMetricsView.as_view(), name="travel-metrics"),
]

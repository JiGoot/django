from django.db.models.query import QuerySet
from common.serializers.zone import ZoneSrz
from courier.models import CourierShift


class CourierShiftSrz:
    """
    Serialize [Order] for [Jigoot kitchen] app's [homePage].
    NOTE For [Jigoot kitchen] the user is defacto a kitchen, so kitchen's details do
    not need to be sent back to the kitchen.
    """

    @staticmethod
    def default(data: object):
        def __srz(obj: CourierShift):
            return {
                "id": obj.pk,
                "zone": ZoneSrz.default(obj.zone) if obj.zone else None,
                "slots": [v.pk for v in obj.slots.all()],
                "start": obj.start.isoformat(),
                "end": obj.end.isoformat(),
                "status": obj.status,
                "pause_count": obj.pause_count,
                "paused_at": (obj.paused_at.isoformat() if obj.paused_at else None),
                "activated_at": (
                    obj.activated_at.isoformat() if obj.activated_at else None
                ),
                "cancelled_at": (
                    obj.cancelled_at.isoformat() if obj.cancelled_at else None
                ), 
            }

        if isinstance(data, CourierShift):
            return __srz(data)
        elif isinstance(data, QuerySet):
            if data.model == CourierShift:
                return [__srz(order) for order in data]
        return None

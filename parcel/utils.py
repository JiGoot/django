from django.utils.functional import classproperty


class ParcelUtils:
    class Status:
        pending = "pending"
        picked_up = "picked-up"
        on_the_way = "on-the-way"
        in_custody = "in-custody"
        delivered = "delivered"
        cancelled = "cancelled"

        @classproperty
        def choices(cls):
            return (
                (cls.pending, "Pending"),
                (cls.picked_up, "Picked up"),
                (cls.on_the_way, "On the way"),
                (cls.in_custody, "In Custody"),
                (cls.delivered, "Delivered"),
                (cls.cancelled, "Cancelled"),
            )

        @classproperty
        def values(cls):
            return (cls.pending, cls.picked_up, cls.on_the_way, cls.in_custody, cls.delivered, cls.cancelled)

    """
    | Type        | Example                                                                  |
    | ----------- | ------------------------------------------------------------------------ |
    | document    | Passport, legal papers                                                   |
    | food        | Cake, lunch, groceries that need fast delivery                           |
    | grocery     | Vegetables, fruits, household items                                      |
    | flower      | Bouquets                                                                 |
    | pharmacy    | Medicine, health products                                                |
    | electronics | Phones, laptops                                                          |
    | package     | Clothing, shoes, boxed gifts, toys                                       |
    | other       | Unusual items not covered above, e.g., furniture, artwork, fragile items |
    """

    class Type:
        document = "document"
        food = "food"
        grocery = "grocery"
        flower = "flower"
        pharmacy = "pharmacy"
        electronics = "electronics"
        package = "package"
        other = "other"

        @classproperty
        def choices(cls):
            return (
                (cls.document, "Document"),
                (cls.food, "Food"),
                (cls.grocery, "Grocery"),
                (cls.flower, "Flower"),
                (cls.pharmacy, "Pharmacy"),
                (cls.electronics, "Electronics"),
                (cls.package, "Package"),
                (cls.other, "Other"),
            )

        @classproperty
        def values(cls):
            return (
                cls.document,
                cls.food,
                cls.grocery,
                cls.flower,
                cls.pharmacy,
                cls.electronics,
                cls.package,
                cls.other,
            )

    class CancelledBy:
        sender = "sender"
        courier = "courier"
        staff = "staff"
        system = "system"

        @classproperty
        def choices(cls):
            return (
                (cls.sender, "Sender"),
                (cls.courier, "Courier"),
                (cls.staff, "Staff"),
                (cls.system, "System"),
            )

        @classproperty
        def values(cls):
            return (cls.sender, cls.courier, cls.staff, cls.system)

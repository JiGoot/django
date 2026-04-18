from django.utils.functional import classproperty


class EventUtils:
    class Age:
        six = 6
        twelve = 12
        sixteen = 16
        eighteen = 18

        @classproperty
        def choices(cls):
            return [
                (cls.six, 6),
                (cls.twelve, 12),
                (cls.sixteen, 16),
                (cls.eighteen, 18),
            ]

        @classproperty
        def values(cls):
            return [cls.six, cls.twelve, cls.sixteen, cls.eighteen]

    class Category:
        concert = "concert"
        conference = "conference"
        theater = "theater"
        sport = "sport"
        movies = "movies"
        excursion = "excursion"
        show = "show"
        course = "course"
        seminary = "seminary"
        # faith = this is for something like cherch events (production, )

        @classproperty
        def choices(cls):
            return (
                (cls.concert, "Concert"),
                (cls.conference, "Conference"),
                (cls.theater, "Theater"),
                (cls.sport, "Sport"),
                (cls.movies, "Movies"),
                (cls.excursion, "Excursion"),
                (cls.show, "Show"),
                (cls.course, "Course"),
            )

        @classproperty
        def values(cls):
            return (
                cls.concert,
                cls.conference,
                cls.theater,
                cls.sport,
                cls.movies,
                cls.excursion,
                cls.show,
                cls.course,
                cls.seminary,
            )
    
    class Status:
        draft = "draft"
        published = "published"
        cancelled = "cancelled"
        archived = "archived"

        @classproperty
        def choices(cls):
            return (
                (cls.draft, "Draft"),
                (cls.published, "Published"),
                (cls.cancelled, "Cancelled"),
                (cls.archived, "Archived"),
            )

        @classproperty
        def values(cls):
            return (cls.draft, cls.published, cls.cancelled, cls.archived)

    class Tag:
        pop = "pop"
        rock = "rock"
        jazz = "jazz"
        classical = "classical"
        hip_hop = "hip_hop"
        rnb = "rnb"
        electronic = "electronic"
        country = "country"
        reggae = "reggae"
        football = "football"
        ...

        @classproperty
        def choices(cls):
            return (
                (cls.pop, "Pop"),
                (cls.rock, "Rock"),
                (cls.jazz, "Jazz"),
                (cls.classical, "Classical"),
                (cls.hip_hop, "Hip Hop"),
                (cls.rnb, "R&B"),
                (cls.electronic, "Electronic"),
                (cls.country, "Country"),
                (cls.reggae, "Reggae"),
                (cls.football, "Football"),
                # ...
            )

        @classproperty
        def values(cls):
            return (
                cls.pop,
                cls.rock,
                cls.jazz,
                cls.classical,
                cls.hip_hop,
                cls.rnb,
                cls.electronic,
                cls.country,
                cls.reggae,
            )


"""
| Tier     | Price Level | Notes / Description                                                                                                                                      |
| -------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Standard | Low         | Basic access, general admission or standard seat, minimal perks. Intended for general audience.                                                          |
| VIP      | Medium      | Premium access with better location (closer to stage/field), priority entry, possible small perks.                                                       |
| Business | Medium-High | Comfortable seating, good view, additional perks (lounge access, refreshments, etc.). Often aimed at corporate or frequent attendees.                    |
| Premium  | High        | Best available experience: prime location, exclusive perks (backstage, meet & greet, early access). Intended for enthusiasts or high-spending customers. |


| Tier (Location) | Price Level | Notes / Intended For                                                                                                       |
| --------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------- |
| Floor           | Basic       | Standard seating or standing area; closest to stage/floor level for general access                                         |
| Mezzanine       | Mid         | Elevated mid-level seating; better sightlines than floor but not premium                                                   |
| Balcony         | High        | Upper-level seating; good overview of the stage/arena; often quieter or more private                                       |
| Suite           | Premium     | Private or semi-private area; best view and comfort; often includes extra perks (VIP services, catering, exclusive access) |


# View Quality / Stadium Sections
| Tier | Price Level | Notes / Intended For                                             |
| ---- | ----------- | ---------------------------------------------------------------- |
| D    | Low         | Farthest seats, restricted view, budget-friendly                 |
| C    | Medium      | Average view, partial sightline, standard experience             |
| B    | High        | Good view, center/side balance, recommended for most             |
| A    | Premium     | Best view, front/center, premium experience, VIP access possible |


"""


class TicketUtils:

    class OrderStatus:
        pending = "pending"
        paid = "paid"
        cancelled = "cancelled"
        refunded = "refunded"

        @classproperty
        def choices(cls):
            return (
                (cls.pending, "Pending"),
                (cls.paid, "Paid"),
                (cls.cancelled, "Cancelled"),
                (cls.refunded, "Refunded"),
            )

        @classproperty
        def values(cls):
            return (cls.pending, cls.paid, cls.cancelled, cls.refunded)

    class Status:
        reserved = "reserved"
        active = "active"  # valid ticket (paid)
        cancelled = "cancelled"
        used = "used"  # scanned / checked-in

        @classproperty
        def choices(cls):
            return (
                (cls.reserved, "Reserved"),
                (cls.active, "Active"),
                (cls.cancelled, "Cancelled"),
                (cls.used, "Used"),
            )

        @classproperty
        def values(cls):
            return (cls.reserved, cls.active, cls.cancelled, cls.used)

    class Tier:
        standard = "standard"
        vip = "v.i.p"
        business = "business"
        premium = "premium"

        @classproperty
        def choices(cls):
            return (
                (cls.standard, "Standard"),
                (cls.vip, "VIP"),
                (cls.business, "Business"),
                (cls.premium, "Premium"),
            )

        @classproperty
        def values(cls):
            return (cls.standard, cls.vip, cls.business, cls.premium)

        class Location:
            floor = "floor"
            mezzanine = "mezzanine"
            balcony = "balcony"
            suite = "suite"

            @classproperty
            def choices(cls):
                return (
                    (cls.floor, "Floor"),
                    (cls.mezzanine, "Mezzanine"),
                    (cls.balcony, "Balcony"),
                    (cls.suite, "Suite"),
                )

            @classproperty
            def values(cls):
                return (cls.floor, cls.mezzanine, cls.balcony, cls.suite)

        class SectionCode:
            a = "a"
            b = "b"
            c = "c"
            d = "d"

            @classproperty
            def choices(cls):
                return ((cls.a, "A"), (cls.b, "B"), (cls.c, "C"), (cls.d, "D"))

            @classproperty
            def values(cls):
                return (cls.a, cls.b, cls.c, cls.d)

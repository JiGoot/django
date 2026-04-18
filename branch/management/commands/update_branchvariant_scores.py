from django.core.management.base import BaseCommand
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta

from branch.models.variant import BranchVariant, BranchVariantDailySales


class Command(BaseCommand):
    help = "Recalculate popularity and trend scores for all BranchVariants"

    def handle(self, *args, **options):
        today = timezone.localdate()

        # Aggregate all variants in ONE query
        stats = (
            BranchVariantDailySales.objects.filter(date__gte=today - timedelta(days=90))
            .values("branch_variant")
            .annotate(
                sold_1d=Sum("qty", filter=Q(date=today)),
                sold_7d=Sum("qty", filter=Q(date__gte=today - timedelta(days=7))),
                sold_30d=Sum("qty", filter=Q(date__gte=today - timedelta(days=30))),
                sold_90d=Sum("qty", filter=Q(date__gte=today - timedelta(days=90))),
            )
        )

        variants_to_update = []

        for row in stats:
            sold_1d = row["sold_1d"] or 0
            sold_7d = row["sold_7d"] or 0
            sold_30d = row["sold_30d"] or 0
            sold_90d = row["sold_90d"] or 0

            popularity_score = (sold_90d * 0.3) + (sold_30d * 1.5) + (sold_7d * 3)
            trend_score = ((sold_1d * 4) + sold_7d) / (sold_30d + 1)

            variants_to_update.append(
                BranchVariant(
                    id=row["branch_variant"],
                    popularity_score=popularity_score,
                    trend_score=trend_score,
                )
            )

        BranchVariant.objects.bulk_update(
            variants_to_update,
            ["popularity_score", "trend_score"],
            batch_size=1000,
        )

        self.stdout.write(self.style.SUCCESS("Scores updated successfully."))

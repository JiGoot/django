from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from common.models.slot import Slot  # adjust import


class Command(BaseCommand):
    help = "Create 32 daily Slots (45min) with capacities for peak/off-peak periods"

    SLOT_LENGTH_MINUTES = 45
    TOTAL_SLOTS = int(24 * 60 / SLOT_LENGTH_MINUTES)  # 32 slots
    PEAK_PERIODS = [
        (6, 10),   # 6:00 - 10:00
        (12, 14),  # 12:00 - 14:00
        (17, 20),  # 17:00 - 20:00
    ]
    OFF_PEAK_CAPACITY = 5
    MID_CAPACITY = 15
    PEAK_CAPACITY = 25

    def handle(self, *args, **options):
        current_time = datetime.strptime("00:00", "%H:%M").time()

        for index in range(1, self.TOTAL_SLOTS + 1):
            dt = datetime.combine(datetime.today(), current_time) + timedelta(minutes=self.SLOT_LENGTH_MINUTES)
            end_time = dt.time()

            # Determine max capacity
            if any(start_hour <= current_time.hour < end_hour for start_hour, end_hour in self.PEAK_PERIODS):
                capacity = self.PEAK_CAPACITY
            elif  current_time.hour in range(10, 12) or current_time.hour in range(15, 17):
                capacity = self.MID_CAPACITY
            else:
                capacity = self.OFF_PEAK_CAPACITY

            # Create slot
            Slot.objects.create(
                start=current_time,
                end=end_time,
                max_capacity=capacity
            )
            print(f"{current_time} - {end_time} :: {capacity}")

            current_time = end_time

        self.stdout.write(self.style.SUCCESS(f"✅ Created {self.TOTAL_SLOTS} Slots successfully."))

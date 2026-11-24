from django.core.management.base import BaseCommand

from bookings.models import Service


class Command(BaseCommand):
    help = "Добавить демонстрационные услуги без изменения существующих цен."

    def handle(self, *args, **options):
        for name, price in [("Сезонная смена шин", "2000.00"), ("Балансировка", "800.00"),
                            ("Осмотр и ремонт шины", "500.00")]:
            Service.objects.get_or_create(name=name, defaults={"price": price})
        self.stdout.write(self.style.SUCCESS("Демонстрационные услуги добавлены."))

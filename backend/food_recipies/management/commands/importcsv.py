import csv

from django.conf import settings
from django.core.management import BaseCommand
from food.models import Ingredient

FILE_LIST = {
    Ingredient: 'ingredients.csv',
}


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for model, filename in FILE_LIST.items():
            with open(
                f'{settings.BASE_DIR}/data/{filename}',
                'r', encoding='utf-8'
            ) as file_csv:
                reader = csv.DictReader(file_csv, delimiter=',')
                try:
                    model.objects.bulk_create(
                        model(**data) for data in reader)
                    print(
                        f'File {filename} imported.'
                    )
                except Exception as error:
                    print(f'Cant import {filename}. ', error)
        self.stdout.write(self.style.SUCCESS('Done!'))

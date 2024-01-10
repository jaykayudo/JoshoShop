from django.core.management.base import BaseCommand
from collections import Counter
import os.path
import csv
from django.core.files.images import ImageFile
from django.template.defaultfilters import slugify
from core.models import Product, Category
from django.conf import settings


class Command(BaseCommand):
    help = "Import Data in Josho Shop"
    def add_arguments(self, parser):
        parser.add_argument("csvfile", type=open)
        parser.add_argument("--imagebasedir", type=str)
    
    def handle(self, *args, **options):
        count = Counter()
        csvreader = csv.DictReader(options.pop("csvfile"))
        imagebasedir = options["imagebasedir"] if options["imagebasedir"] else settings.IMPORT_IMAGES_DIR

        for row in csvreader:
            product = Product()
            product.name = row['name']
            product.price = row['price']
            product.description = row['description']
            self.stdout.write(row['image'])
            with open(os.path.join(imagebasedir,row['image']), "rb") as f:
                image = ImageFile(f,row['image'])
                product.image = image
                product.save()
            categories = row['category'].split("|")
            for c in categories:
                category, created = Category.objects.get_or_create(name = c, slug = slugify(c))
                if created:
                    count['category_created'] += 1
                product.tags.add(category)
            product.save()
            count['products'] += 1

        self.stdout.write("Product Created = %d "%(count['product']))
        self.stdout.write("Product Categories Created = %d"%(count['created']))

        



        
import json

from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from authenbite.restaurants.models import Cuisine, Restaurant


class Command(BaseCommand):
    help = "Import restaurants from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="Path to the JSON file")

    def handle(self, *args, **options):
        json_file_path = options["json_file"]

        with open(json_file_path, "r") as file:
            data = json.load(file)

        for restaurant_data in data:
            try:
                # Get image URLs
                image_urls = restaurant_data.get("imageUrls", [])
                main_image_url = image_urls[0] if image_urls else ""

                # Create or get the restaurant
                restaurant, created = Restaurant.objects.get_or_create(
                    name=restaurant_data.get("title", ""),
                    defaults={
                        "address": restaurant_data.get("address", ""),
                        "phone_number": restaurant_data.get("phone", ""),
                        "website": restaurant_data.get("website", ""),
                        "rating": restaurant_data.get("totalScore", 0),
                        "main_image_url": main_image_url,
                    },
                )

                # Set location
                if "location" in restaurant_data:
                    lat = restaurant_data["location"].get("lat")
                    lng = restaurant_data["location"].get("lng")
                    if lat and lng:
                        restaurant.location = Point(float(lng), float(lat))

                # Add cuisines
                if "categories" in restaurant_data:
                    for category in restaurant_data["categories"]:
                        cuisine, _ = Cuisine.objects.get_or_create(name=category)
                        restaurant.cuisines.add(cuisine)

                restaurant.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Imported/Updated: {restaurant.name}")
                )

            except ValidationError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Validation error for restaurant {restaurant_data.get('title', '')}: {str(e)}"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error importing restaurant {restaurant_data.get('title', '')}: {str(e)}"
                    )
                )

        self.stdout.write(self.style.SUCCESS("Import completed"))

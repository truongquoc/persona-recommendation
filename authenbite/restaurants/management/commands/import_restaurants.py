import json
import re

from django.contrib.gis.geos import Point
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

                offerings = restaurant_data.get("Offerings", [])
                for offering in offerings:

                    restaurant.vegan_options = bool(
                        offering.get("Vegan options", False)
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

                # Set opening hours
                if "openingHours" in restaurant_data:
                    self.set_opening_hours(restaurant, restaurant_data["openingHours"])

                restaurant.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Imported/Updated: {restaurant.name}")
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error importing restaurant {restaurant_data.get('title', '')}: {str(e)}"
                    )
                )

        self.stdout.write(self.style.SUCCESS("Import completed"))

    def set_opening_hours(self, restaurant, opening_hours):
        formatted_hours = {}
        for day_data in opening_hours:
            day = day_data["day"]
            hours = day_data["hours"]
            start, end = hours.split(" to ")
            start_minutes = self.time_to_minutes(start)
            end_minutes = self.time_to_minutes(end)
            if start_minutes is not None and end_minutes is not None:
                formatted_hours[day] = [start_minutes, end_minutes]

        restaurant.opening_hours = formatted_hours
        restaurant.opening_hours_display = json.dumps(opening_hours)

    @staticmethod
    def time_to_minutes(time_str):
        pattern = r"^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)$"
        match = re.match(pattern, time_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2) or 0)
            period = match.group(3)

            if period == "PM" and hours != 12:
                hours += 12
            elif period == "AM" and hours == 12:
                hours = 0

            return hours * 60 + minutes
        else:
            print(f"Warning: Could not parse time string '{time_str}'")
            return None

import logging
import os
import time
import uuid
from django.utils.translation import gettext_lazy as _
from django.db import models
from model_utils import FieldTracker
from common.models.service import Service

from core.managers import ObjectsManager
from core.mixin.file_cleanup import FileCleanupMixin
from core.utils import versioned_upload

logger = logging.getLogger(__name__)
"""
🍽️ Cuisine Type Tags: These describe the origin or style of the food:
    -African
    Congolese
    Nigerian
    Ethiopian
    Moroccan
    Asian
    Indian
    Chinese
    Japanese
    Thai
    Italian
    French
    Mediterranean
    American
    Latin American
    Middle Eastern
    Caribbean
    Continental
    Fusion

🌱 Diet & Lifestyle Tags: These describe dietary categories or food philosophies:
    Vegetarian
    Vegan
    Halal
    Kosher
    Gluten-Free
    Dairy-Free
    Low-Carb
    Keto
    High-Protein
    Organic
    Sugar-Free
    Nut-Free

🥘 Meal Type Tags: These help customers find what kind of meals the supplier offers:
    Breakfast
    Brunch
    Lunch
    Dinner
    Late Night
    Light Meals
    Full Meals
    Family Meals
    Meal Prep / Packaged Meals

🍟 Food Category Tags: These describe the types of food sold:
    Grilled
    Fried
    Stews
    Soups
    Pasta
    Rice Dishes
    Burgers
    Sandwiches
    Shawarma
    Pizza
    Tacos / Wraps
    BBQ
    Roasted
    Seafood
    Chicken
    Goat / Beef
    Plant-Based
    Jollof / Pilau / Local Rice

🍰 Sweets & Beverage Tags: For businesses that offer desserts, snacks, and drinks:
    Smoothies
    Milkshakes
    Tea
    Coffee
    Fresh Juice
    Soft Drinks
    Ice Cream
    Pastries
    Cakes
    Snacks
    Chocolate
    Donuts
    Street Sweets

🚚 Service Tags: These highlight the style of service:
    Delivery Only
    Pickup Only
    Dine-in Available
    Express Delivery
    Pre-order Friendly
    Schedule Orders Accepted
    Family-Friendly
    Budget Friendly
    Premium Quality

🧑‍🍳 Experience & Brand Tags: These describe the experience or brand:
    Homemade
    Traditional
    Modern / Contemporary
    Healthy
    Fast Food
    Gourmet
    Local Favorite
    Hidden Gem
    Popular
"""

# Tag belong to services

class Tag(FileCleanupMixin, models.Model):
    def upload_image(instance, filename):
        return versioned_upload("branch/tags/", instance, filename)

    index = models.PositiveSmallIntegerField(default=0)
    type = models.ForeignKey(Service, on_delete=models.RESTRICT, null=True)
    name = models.CharField(max_length=25, unique=True)
    age_check = models.BooleanField(default=False)
    # Image must be a PNG file of size is to be 512x512
    image = models.ImageField(upload_to=upload_image)
    is_active = models.BooleanField(default=True, help_text="If enabled for filtering.")
    tracker = FieldTracker(fields=["image"])
    objects = ObjectsManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-is_active", "index", "name"]
        unique_together = [("type", "name")]

    def save(self, *args, **kwargs):
        self.cleanup_files
        super().save(*args, **kwargs)

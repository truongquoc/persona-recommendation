# authenbite/restaurants/api/filters.py

from django_filters import rest_framework as filters

from authenbite.restaurants.models import Restaurant


class RestaurantFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    is_favorite = filters.BooleanFilter(method="filter_is_favorite")
    min_rating = filters.NumberFilter(field_name="rating", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price_level", lookup_expr="lte")

    class Meta:
        model = Restaurant
        fields = ["name", "is_favorite", "price_level", "rating"]

    def filter_is_favorite(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(
                userrestaurantinteraction__user=user,
                userrestaurantinteraction__liked=True,
            )
        return queryset

    def filter_queryset(self, queryset):
        for name, value in self.form.cleaned_data.items():
            if value is not None:
                queryset = self.filters[name].filter(queryset, value)
        return queryset

    def get_schema_operation_parameters(self):
        return [
            {
                "name": "name",
                "required": False,
                "in": "query",
                "description": "Filter by restaurant name (case-insensitive)",
                "schema": {
                    "type": "string",
                },
            },
            {
                "name": "is_favorite",
                "required": False,
                "in": "query",
                "description": "Filter by favorite restaurants",
                "schema": {
                    "type": "boolean",
                },
            },
            {
                "name": "min_rating",
                "required": False,
                "in": "query",
                "description": "Filter by minimum rating",
                "schema": {
                    "type": "number",
                },
            },
            {
                "name": "max_price",
                "required": False,
                "in": "query",
                "description": "Filter by maximum price level",
                "schema": {
                    "type": "integer",
                },
            },
        ]

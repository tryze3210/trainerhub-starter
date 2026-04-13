from rest_framework.exceptions import NotFound
from apps.public_catalog import selectors


def build_catalog_response(query_params):
    params = {
        'q': query_params.get('q'),
        'entity_type': query_params.get('entity_type'),
        'category': query_params.get('category'),
        'difficulty': query_params.get('difficulty'),
        'trainer_slug': query_params.get('trainer_slug'),
        'featured': query_params.get('featured'),
        'sort': query_params.get('sort'),
    }
    items = selectors.list_catalog_items(params)
    return {'count': len(items), 'items': items, 'applied_filters': params}


def get_public_item_or_raise(entity_type: str, slug: str):
    item = selectors.get_catalog_item_by_slug(entity_type, slug)
    if not item:
        raise NotFound('Catalog item not found')
    return item

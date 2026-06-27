from rest_framework.exceptions import NotFound

from apps.public_catalog import selectors


PUBLIC_MARKETPLACE_SEO = {
    'title': 'TrainerHub marketplace',
    'description': 'Discover trainer-led courses, programs, videos and bundles with secure checkout and entitlement-based access.',
    'canonical_path': '/catalog',
}


def _price_label(item: dict) -> str:
    price = item.get('price') or '0'
    if price in {'0', '0.00'}:
        return 'Free'
    return f"{price} {item.get('currency') or 'RUB'}"


def _checkout_cta(item: dict) -> dict:
    return {
        'label': f"Buy for {_price_label(item)}",
        'href': f"/login?next=/checkout?item_type={item['entity_type']}&item_id={item['id']}",
        'requires_auth': True,
    }


def _item_seo(item: dict) -> dict:
    description = (item.get('description') or '').strip()
    if not description:
        description = f"{item['title']} by {item.get('trainer_name') or 'TrainerHub'}."
    return {
        'title': f"{item['title']} | TrainerHub",
        'description': description[:240],
        'canonical_path': f"/catalog/{item['entity_type']}s/{item['slug']}",
    }


def _pricing(item: dict) -> dict:
    return {
        'amount': item.get('price') or '0.00',
        'currency': item.get('currency') or 'RUB',
        'label': _price_label(item),
        'checkout_cta': _checkout_cta(item),
    }


def _reviews(item: dict) -> dict:
    return {
        'average_rating': item.get('rating') or 0,
        'reviews_count': item.get('reviews_count') or 0,
        'href': f"/catalog/{item['entity_type']}s/{item['slug']}#reviews",
    }


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


def build_marketplace_home(query_params) -> dict:
    catalog = build_catalog_response(query_params)
    featured = selectors.list_featured_items(limit=8)
    return {
        'seo': PUBLIC_MARKETPLACE_SEO,
        'hero': {
            'headline': 'TrainerHub marketplace',
            'subheadline': 'Courses, programs, videos and bundles from verified trainers.',
            'primary_cta': {'label': 'Browse catalog', 'href': '/catalog'},
            'secondary_cta': {'label': 'Browse trainers', 'href': '/trainers'},
        },
        'catalog': catalog,
        'featured': featured,
        'trust': {
            'checkout': 'Secure checkout creates orders, payments and entitlements.',
            'access': 'Purchased content is guarded by entitlement runtime checks.',
            'reviews': 'Published reviews and ratings are visible on product and trainer pages.',
        },
    }


def build_content_landing(entity_type: str, slug: str) -> dict:
    item = get_public_item_or_raise(entity_type, slug)
    return {
        'seo': _item_seo(item),
        'item': item,
        'pricing': _pricing(item),
        'reviews': _reviews(item),
        'trainer': {
            'slug': item.get('trainer_slug'),
            'display_name': item.get('trainer_name'),
            'href': f"/trainers/{item.get('trainer_slug')}",
        },
        'access': {
            'post_purchase': 'Access is granted after successful payment and checked through entitlements.',
            'refund_policy': 'Refunded purchases can revoke access through entitlement status.',
        },
    }


def build_trainer_landing(slug: str) -> dict:
    from apps.trainer_profiles.services import build_public_trainer_profile

    try:
        profile = build_public_trainer_profile(slug)
    except LookupError as exc:
        raise NotFound(str(exc))
    catalog_items = profile.get('catalog_items') or []
    featured = [item for item in catalog_items if item.get('is_featured')][:4]
    return {
        'seo': {
            'title': f"{profile['display_name']} | TrainerHub trainer",
            'description': (profile.get('headline') or profile.get('bio') or 'TrainerHub public trainer profile.')[:240],
            'canonical_path': f"/trainers/{profile['slug']}",
        },
        'profile': profile,
        'featured': featured,
        'catalog': {'count': len(catalog_items), 'items': catalog_items},
        'reviews': {
            'average_rating': profile.get('rating') or 0,
            'reviews_count': profile.get('reviews_count') or 0,
            'href': f"/trainers/{profile['slug']}#reviews",
        },
        'pricing': [
            _pricing(item) for item in catalog_items[:6]
        ],
        'checkout_ctas': [
            _checkout_cta(item) for item in catalog_items[:6]
        ],
    }

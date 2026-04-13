from apps.reviews import selectors


def build_target_reviews(target_type: str, target_id: str) -> dict:
    return {
        'summary': selectors.get_rating_summary(target_type, target_id),
        'items': selectors.list_published_reviews(target_type, target_id),
    }

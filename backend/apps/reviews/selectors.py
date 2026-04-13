REVIEWS = [
    {
        'id': 'rev-1',
        'target_type': 'trainer',
        'target_id': 'anna-fit',
        'author_name': 'Julia',
        'rating': 5,
        'title': 'Great short workouts',
        'body': 'Perfect format for a busy schedule. Clear guidance and high energy.',
        'status': 'published',
        'created_at': '2026-04-02T09:00:00Z',
    },
    {
        'id': 'rev-2',
        'target_type': 'program',
        'target_id': 'zumba-beginners-14-days',
        'author_name': 'Irina',
        'rating': 5,
        'title': 'Very engaging program',
        'body': 'Beginner-friendly, fun, and easy to follow day by day.',
        'status': 'published',
        'created_at': '2026-04-05T09:00:00Z',
    },
]


def list_published_reviews(target_type: str, target_id: str) -> list[dict]:
    return [
        review for review in REVIEWS
        if review['target_type'] == target_type and review['target_id'] == target_id and review['status'] == 'published'
    ]


def get_rating_summary(target_type: str, target_id: str) -> dict:
    reviews = list_published_reviews(target_type, target_id)
    count = len(reviews)
    average = round(sum(r['rating'] for r in reviews) / count, 2) if count else 0
    return {
        'target_type': target_type,
        'target_id': target_id,
        'reviews_count': count,
        'average_rating': average,
    }

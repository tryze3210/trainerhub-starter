def build_access_snapshot() -> dict:
    return {
        'role': 'trainer',
        'capabilities': [
            'cabinet.read',
            'trainer_cms.manage',
            'media.upload',
        ],
        'features': {
            'trainer_cms': True,
            'media_upload': True,
            'moderation_review': False,
        },
        'onboarding': {
            'is_completed': True,
            'missing_steps': [],
        },
    }

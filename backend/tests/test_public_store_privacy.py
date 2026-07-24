from apps.store.selectors import list_bundles, list_programs, list_videos


def test_legacy_store_payload_uses_public_trainer_identity():
    for item in [*list_videos(), *list_programs(), *list_bundles()]:
        assert 'trainer_id' not in item
        assert item['trainer_slug']
        assert item['trainer_name']

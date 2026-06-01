# TrainerHub v50.2 — referrals register contract patch-pack

Формат: обычный patch-pack без runtime-скриптов.

Фиксит падение:

```text
TypeError: register_user() got an unexpected keyword argument 'referral_invite_id'
```

## Что меняется

Файл:

```text
backend/apps/authn/services.py
```

Изменения:

- `register_user()` принимает referral-поля:
  - `referral_invite_id: str | None = None`
  - `referral_code: str = ''`
  - `click_session_key: str = ''`
- после создания пользователя, профиля и настроек вызывается:

```python
ReferralIntegrationService.bind_signup_from_request(
    referred_user=user,
    invite_id=referral_invite_id,
    referral_code=referral_code,
    click_session_key=click_session_key,
)
```

## Вариант 1 — применить как обычный changed-files patch-pack

Из корня репозитория:

```bash
cp -a trainerhub_v50_2_referrals_register_patch_pack/backend .
```

## Вариант 2 — применить через git apply

Из корня репозитория:

```bash
git apply trainerhub_v50_2_referrals_register_patch_pack/patches/v50_2_referrals_register_contract.patch
```

Если `git apply` конфликтует из-за локального форматирования файла, используй вариант 1 — он заменяет только один файл.

## Проверка

```bash
cd backend
python manage.py check
python manage.py shell -c "import inspect; from apps.authn.services import register_user; print(inspect.signature(register_user))"
pytest tests/test_referrals_v50_integration.py -q
pytest -q
```

Ожидаемая сигнатура должна содержать:

```text
referral_invite_id: str | None = None
```

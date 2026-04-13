# TrainerHub v49 patch — referrals engine

Этот patch добавляет отдельный bounded context `referrals` для growth / ambassador / promo attribution.

## Что внутри
- referral domain models
- application services
- DRF API
- Celery snippets
- frontend scaffolds
- install notes

## Основные сущности
- ReferralProgram
- ReferralCode
- ReferralInvite
- ReferralAttribution
- ReferralReward
- ReferralLedger

## Дальше по интеграции
Главные integration seams:
- signup / registration flow
- order paid / conversion flow
- analytics utm attribution bridge

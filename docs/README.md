# TrainerHub v28 — Affiliate / Referral Attribution + Commission Accrual

## Что входит

v28 добавляет production-oriented партнерский канал продаж:

- `AffiliatePartner` — партнер / инфлюенсер / реферальный источник с кодом и моделью комиссии;
- `AffiliateClick` — факт клика по партнерской ссылке;
- `AffiliateAttribution` — активная атрибуция клиента по `client_key` и/или user;
- `OrderAttribution` — immutable snapshot attribution на момент заказа;
- `AffiliateCommission` — обязательство платформы перед партнером;
- public tracking endpoint для клика;
- admin API для партнеров, комиссий и order attribution;
- partner dashboard page;
- billing integration stub для payable liability.

## Зачем этот шаг

На коммерческой платформе просто хранить `ref=blogger1` в query params недостаточно. Нужна нормальная модель, которая отвечает на вопросы:

- какой партнер привел заказ;
- по какой модели атрибуции это засчитано;
- какая комиссия начислена;
- как это сторнировать при refund / chargeback;
- как не потерять источник после логина, смены устройства, повторного визита.

Именно поэтому в v28 есть три уровня:

1. **click tracking**
2. **active attribution state**
3. **order snapshot + commission accrual**

---

## Основные инженерные решения

### 1. `OrderAttribution` отдельной сущностью, а не просто поля в `Order`

Так сохраняется immutable snapshot на момент покупки:

- какой partner был засчитан;
- какой click был источником;
- какие UTM были у заказа;
- какая commission base и commission amount были рассчитаны.

Это критично для аудита, споров и финансовых пересчетов.

### 2. `AffiliateCommission` отдельно от `OrderAttribution`

Attribution отвечает на вопрос **кому засчитан заказ**, а commission — **сколько и в каком статусе платим**.

Это позволяет делать:

- delayed approval после anti-fraud / refund window;
- payout batches;
- reversals;
- раздельную аналитику performance и payable liabilities.

### 3. `client_key` как обязательный канал склейки anonymous → authenticated

До логина пользователь часто анонимен. Поэтому нужен стабильный browser/client identifier (cookie/localStorage UUID), через который атрибуция живет до момента авторизации и checkout.

### 4. Snapshot UTM и click metadata

Даже если click/partner потом изменятся, заказ должен сохранить исторический snapshot. Это не обсуждается для production analytics.

---

## Структура

- `backend/apps/affiliates/...` — новый домен affiliates
- `backend/apps/orders/services/affiliate_attribution.py` — точка привязки к order finalization
- `backend/apps/billing/services/affiliate_accounting.py` — accrual / reversal stub под ledger
- `frontend/src/app/admin/affiliates/page.tsx` — admin page
- `frontend/src/app/partner/dashboard/page.tsx` — partner page

---

## Что нужно подключить вручную

### 1. Добавить app в `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    # ...
    "apps.affiliates",
]
```

### 2. Подключить URLs

В основной DRF router:

```python
from apps.affiliates.api.views import (
    AdminAffiliateCommissionViewSet,
    AdminAffiliatePartnerViewSet,
    AffiliateOrderAttributionViewSet,
    AffiliatePartnerDashboardViewSet,
    PublicAffiliateTrackingViewSet,
)

router.register(r"admin/affiliates/partners", AdminAffiliatePartnerViewSet, basename="admin-affiliate-partner")
router.register(r"admin/affiliates/commissions", AdminAffiliateCommissionViewSet, basename="admin-affiliate-commission")
router.register(r"admin/affiliates/order-attributions", AffiliateOrderAttributionViewSet, basename="admin-order-attribution")
router.register(r"partner/affiliates/commissions", AffiliatePartnerDashboardViewSet, basename="partner-affiliate-dashboard")
router.register(r"public/affiliate-tracking", PublicAffiliateTrackingViewSet, basename="public-affiliate-tracking")
```

### 3. На landing page / frontend захватывать клики

Когда пользователь открывает URL вида:

```
/trainers/ivan?ref=BLOGGER10&utm_source=instagram&utm_campaign=spring_sale
```

нужно: 

- достать `ref`;
- получить/создать `client_key`;
- отправить POST в tracking endpoint.

Пример payload:

```json
{
  "partner_code": "BLOGGER10",
  "client_key": "browser-uuid-123",
  "landing_path": "/trainers/ivan",
  "referrer_url": "https://instagram.com/...",
  "utm": {
    "utm_source": "instagram",
    "utm_medium": "influencer",
    "utm_campaign": "spring_sale"
  }
}
```

### 4. При финализации заказа вызвать attribution service

После успешного создания `Order`, но до payout finalization:

```python
from apps.orders.services.affiliate_attribution import attach_affiliate_attribution_to_order
from apps.billing.services.affiliate_accounting import record_affiliate_commission_liability

commission = attach_affiliate_attribution_to_order(
    order=order,
    user=request.user,
    client_key=request.headers.get("X-Client-Key"),
)

if commission:
    record_affiliate_commission_liability(commission=commission)
```

### 5. В refund / reversal flow сторнировать affiliate commission

Если заказ отменен или refund делает commission invalid, вызывай reversal для комиссии и зеркальную ledger-проводку.

---

## Финансовая модель

`commission_base_amount` здесь по умолчанию считается от `order.subtotal_amount`. Это правильная стартовая модель для marketplace.

Но в твоем проекте ты должен привести это к единому правилу с v21/v27:

- либо партнерская комиссия считается от gross subtotal;
- либо от paid amount after discounts;
- либо от trainer net basis.

Смешивать разные базы без явного policy нельзя.

Рекомендация для TrainerHub:

- **promo-funded-by-platform** не должен уменьшать affiliate base;
- **trainer-funded discount** должен уменьшать trainer basis, но не обязательно affiliate base — это уже policy продукта;
- решение должно быть единым и зафиксированным в billing docs.

---

## Минимальный сценарий тестирования

1. Создать `AffiliatePartner` с кодом `BLOGGER10` и комиссией `7%`.
2. Открыть landing page с `?ref=BLOGGER10&utm_source=instagram`.
3. Зафиксировать `AffiliateClick` и `AffiliateAttribution`.
4. Создать заказ на `1000.00`.
5. Вызвать `attach_affiliate_attribution_to_order`.
6. Проверить:
   - создан `OrderAttribution`;
   - `commission_base_amount = 1000.00`;
   - `commission_amount = 70.00`;
   - создан `AffiliateCommission(status=pending)`.
7. Сделать approve.
8. Сделать refund.
9. Проверить reversal.

---

## Следующий правильный шаг: v29

После v28 сильнее всего делать **analytics warehouse slice + KPI endpoints**:

- GMV / net revenue / MRR / churn / refund rate
- cohort analytics
- trainer funnel
- affiliate funnel
- promo performance
- admin dashboard tiles + charts

То есть v29 должен уже превращать все предыдущие финансовые и маркетинговые события в управленческую аналитику.

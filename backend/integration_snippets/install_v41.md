# v41 install

1. Copy `backend/apps/booking`
2. Add `apps.booking` to `INSTALLED_APPS`
3. Include `apps.booking.api.urls` under `/api/v1/booking/`
4. Generate and apply migrations:
   ```bash
   python manage.py makemigrations booking
   python manage.py migrate
   ```
5. Seed `BookingProfile` for approved trainers or let API autocreate on first access
6. Add periodic job for slot pre-generation if you want rolling availability windows

## Recommended next integration
- connect reservations to payments/orders for paid sessions
- emit notifications on reservation create/cancel
- add Google Calendar / ICS export adapters

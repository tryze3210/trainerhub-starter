from dataclasses import dataclass


@dataclass
class ProviderDispatchResult:
    ok: bool
    provider_message_id: str = ""
    response_code: str = ""
    response_payload: dict | None = None
    error_message: str = ""


class BaseNotificationProvider:
    provider_code = "base"

    def send(self, message):
        raise NotImplementedError


class ConsoleEmailProvider(BaseNotificationProvider):
    provider_code = "console_email"

    def send(self, message):
        return ProviderDispatchResult(
            ok=True,
            provider_message_id=f"email-{message.pk}",
            response_code="200",
            response_payload={"simulated": True},
        )


class ConsolePushProvider(BaseNotificationProvider):
    provider_code = "console_push"

    def send(self, message):
        return ProviderDispatchResult(
            ok=True,
            provider_message_id=f"push-{message.pk}",
            response_code="200",
            response_payload={"simulated": True},
        )


class ConsoleSMSProvider(BaseNotificationProvider):
    provider_code = "console_sms"

    def send(self, message):
        return ProviderDispatchResult(
            ok=True,
            provider_message_id=f"sms-{message.pk}",
            response_code="200",
            response_payload={"simulated": True},
        )

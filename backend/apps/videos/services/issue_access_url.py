from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from apps.access_control.permissions import ROLE_ADMIN, ROLE_TRAINER, user_role_set
from apps.entitlements.access_audit import AccessControlAuditService
from common.storage.client import storage_service
from apps.videos.models import Video, VideoAccessLog


DEFAULT_MEDIA_READ_TTL_SECONDS = 300
DEFAULT_MEDIA_READ_MAX_TTL_SECONDS = 900


def _client_ip(request) -> str | None:
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


def _host_from_url(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    without_scheme = text.split("://", 1)[-1]
    return without_scheme.split("/", 1)[0].lower()


def _allowed_hosts() -> set[str]:
    hosts = {str(item).lower() for item in getattr(settings, "ALLOWED_HOSTS", []) if item and item != "*"}
    frontend_origin = getattr(settings, "FRONTEND_URL", "") or getattr(settings, "PUBLIC_FRONTEND_URL", "")
    frontend_host = _host_from_url(frontend_origin)
    if frontend_host:
        hosts.add(frontend_host)
    extra = getattr(settings, "MEDIA_ALLOWED_REFERER_HOSTS", [])
    hosts.update(str(item).lower() for item in extra if item)
    return hosts


def _anti_leech_payload(request) -> dict[str, Any]:
    if request is None:
        return {"status": "unknown", "allowed": True, "reason": "no_request_context"}
    referer = request.META.get("HTTP_REFERER", "")
    origin = request.META.get("HTTP_ORIGIN", "")
    candidate = _host_from_url(origin) or _host_from_url(referer)
    allowed_hosts = _allowed_hosts()
    if not candidate:
        return {"status": "pass", "allowed": True, "reason": "no_referer_or_origin", "host": ""}
    if not allowed_hosts:
        return {"status": "pass", "allowed": True, "reason": "no_allowed_hosts_configured", "host": candidate}
    allowed = candidate in allowed_hosts
    return {
        "status": "pass" if allowed else "warning",
        "allowed": True,
        "reason": "referer_origin_allowed" if allowed else "referer_origin_unrecognized",
        "host": candidate,
        "allowed_hosts": sorted(allowed_hosts),
    }


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _sign_token(*, video_id: str, user_id: str, expires_at) -> str:
    secret = getattr(settings, "SECRET_KEY", "trainerhub")
    nonce = secrets.token_urlsafe(12)
    payload = f"{video_id}:{user_id}:{int(expires_at.timestamp())}:{nonce}"
    signature = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}:{signature}"


def _authenticated_roles(user) -> set[str]:
    if not getattr(user, "is_authenticated", False):
        return set()
    return user_role_set(user)


def _media_read_ttl_seconds() -> int:
    ttl_seconds = int(getattr(settings, "MEDIA_READ_TTL_SECONDS", DEFAULT_MEDIA_READ_TTL_SECONDS) or 0)
    max_ttl_seconds = int(getattr(settings, "MEDIA_READ_MAX_TTL_SECONDS", DEFAULT_MEDIA_READ_MAX_TTL_SECONDS) or 0)
    if ttl_seconds <= 0:
        ttl_seconds = DEFAULT_MEDIA_READ_TTL_SECONDS
    if max_ttl_seconds <= 0:
        max_ttl_seconds = DEFAULT_MEDIA_READ_MAX_TTL_SECONDS
    return min(ttl_seconds, max_ttl_seconds)


class IssueVideoAccessUrlService:
    def execute(self, *, user, video: Video, request=None) -> dict[str, Any]:
        ttl_seconds = _media_read_ttl_seconds()
        expires_at = timezone.now() + timezone.timedelta(seconds=ttl_seconds)
        anti_leech = _anti_leech_payload(request)
        entitlement_decision: dict[str, Any] = {}
        reason = VideoAccessLog.AccessReason.DENIED
        roles = _authenticated_roles(user)
        trainer_profile = getattr(user, "trainer_profile", None) if ROLE_TRAINER in roles else None

        if user.is_authenticated and (ROLE_ADMIN in roles or getattr(user, "is_staff", False)):
            reason = VideoAccessLog.AccessReason.ADMIN
        elif trainer_profile is not None and video.trainer_id == trainer_profile.id:
            reason = VideoAccessLog.AccessReason.TRAINER_OWNER
        elif video.is_free:
            reason = VideoAccessLog.AccessReason.FREE_VIDEO
        elif user.is_authenticated:
            entitlement_decision = AccessControlAuditService.check(
                user=user,
                target_type="video",
                target_id=str(video.id),
                include_admin_override=False,
            )
            if entitlement_decision.get("allowed"):
                reason = VideoAccessLog.AccessReason.ENTITLEMENT
            else:
                self._log(
                    user=user,
                    video=video,
                    request=request,
                    decision=VideoAccessLog.Decision.DENIED,
                    reason=VideoAccessLog.AccessReason.DENIED,
                    anti_leech=anti_leech,
                    entitlement_decision=entitlement_decision,
                )
                raise PermissionDenied(f"You do not have access to this video: {entitlement_decision.get('code')}")
        else:
            self._log(
                user=user if getattr(user, "is_authenticated", False) else None,
                video=video,
                request=request,
                decision=VideoAccessLog.Decision.DENIED,
                reason=VideoAccessLog.AccessReason.DENIED,
                anti_leech=anti_leech,
                entitlement_decision={"code": "authentication_required"},
            )
            raise PermissionDenied("Authentication is required to access this video.")

        access_token = _sign_token(
            video_id=str(video.id),
            user_id=str(getattr(user, "id", "") or "anonymous"),
            expires_at=expires_at,
        )
        playback_url = storage_service.create_presigned_read(
            video.media_asset.bucket_name,
            video.media_asset.object_key,
            ttl_seconds,
        )
        log = self._log(
            user=user if getattr(user, "is_authenticated", False) else None,
            video=video,
            request=request,
            decision=VideoAccessLog.Decision.GRANTED,
            reason=reason,
            anti_leech=anti_leech,
            entitlement_decision=entitlement_decision,
            access_token=access_token,
            expires_at=expires_at,
        )
        return {
            "playback_url": playback_url,
            "access_token": access_token,
            "expires_in": ttl_seconds,
            "expires_at": expires_at.isoformat(),
            "access_log_id": str(log.id),
            "delivery_policy": {
                "signed_url": True,
                "ttl_seconds": ttl_seconds,
                "anti_leech": anti_leech,
                "reason": reason,
            },
        }

    @staticmethod
    def _log(
        *,
        user,
        video: Video,
        request,
        decision: str,
        reason: str,
        anti_leech: dict[str, Any],
        entitlement_decision: dict[str, Any],
        access_token: str = "",
        expires_at=None,
    ) -> VideoAccessLog:
        return VideoAccessLog.objects.create(
            user=user,
            video=video,
            media_asset=video.media_asset,
            decision=decision,
            reason=reason,
            access_token_hash=_token_hash(access_token) if access_token else "",
            expires_at=expires_at,
            ip_address=_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "") if request is not None else "",
            referer=request.META.get("HTTP_REFERER", "") if request is not None else "",
            origin=request.META.get("HTTP_ORIGIN", "") if request is not None else "",
            anti_leech=anti_leech,
            entitlement_decision=entitlement_decision,
        )

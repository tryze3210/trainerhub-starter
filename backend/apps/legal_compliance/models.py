import uuid
from django.conf import settings
from django.db import models


class TrainerKYCProfile(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trainer_kyc_profile')
    full_name = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2, blank=True)
    tax_id = models.CharField(max_length=64, blank=True)
    legal_address = models.TextField(blank=True)
    payout_legal_entity_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_kyc_profiles')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LegalDocumentTemplate(models.Model):
    DOC_OFFER = 'offer'
    DOC_PRIVACY = 'privacy_policy'
    DOC_TERMS = 'terms_of_service'
    DOC_TRAINER_AGREEMENT = 'trainer_agreement'
    DOC_CHOICES = [
        (DOC_OFFER, 'Offer'),
        (DOC_PRIVACY, 'Privacy Policy'),
        (DOC_TERMS, 'Terms of Service'),
        (DOC_TRAINER_AGREEMENT, 'Trainer Agreement'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doc_type = models.CharField(max_length=64, choices=DOC_CHOICES)
    version = models.CharField(max_length=32)
    title = models.CharField(max_length=255)
    body_markdown = models.TextField()
    is_active = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('doc_type', 'version')]


class LegalAcceptanceSnapshot(models.Model):
    ACTOR_USER = 'user'
    ACTOR_TRAINER = 'trainer'
    ACTOR_CHOICES = [(ACTOR_USER, 'User'), (ACTOR_TRAINER, 'Trainer')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='legal_acceptances')
    actor_type = models.CharField(max_length=32, choices=ACTOR_CHOICES)
    document = models.ForeignKey(LegalDocumentTemplate, on_delete=models.PROTECT, related_name='acceptance_snapshots')
    accepted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    body_snapshot = models.TextField()
    title_snapshot = models.CharField(max_length=255)
    version_snapshot = models.CharField(max_length=32)


class TrainerContractArtifact(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_GENERATED = 'generated'
    STATUS_SIGNED = 'signed'
    STATUS_ARCHIVED = 'archived'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_GENERATED, 'Generated'),
        (STATUS_SIGNED, 'Signed'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contract_artifacts')
    document_template = models.ForeignKey(LegalDocumentTemplate, null=True, blank=True, on_delete=models.SET_NULL)
    artifact_path = models.CharField(max_length=1024, blank=True)
    version = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    generated_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PayoutEligibilitySnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payout_eligibility_snapshot')
    kyc_status = models.CharField(max_length=32, blank=True)
    has_active_agreement = models.BooleanField(default=False)
    has_verified_payout_profile = models.BooleanField(default=False)
    is_eligible = models.BooleanField(default=False)
    block_reason = models.TextField(blank=True)
    calculated_at = models.DateTimeField(auto_now=True)

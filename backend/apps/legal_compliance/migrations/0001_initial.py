import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalDocumentTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    'doc_type',
                    models.CharField(
                        choices=[
                            ('offer', 'Offer'),
                            ('privacy_policy', 'Privacy Policy'),
                            ('terms_of_service', 'Terms of Service'),
                            ('refund_policy', 'Refund Policy'),
                            ('trainer_agreement', 'Trainer Agreement'),
                        ],
                        max_length=64,
                    ),
                ),
                ('version', models.CharField(max_length=32)),
                ('title', models.CharField(max_length=255)),
                ('body_markdown', models.TextField()),
                ('is_active', models.BooleanField(default=False)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'unique_together': {('doc_type', 'version')}},
        ),
        migrations.CreateModel(
            name='TrainerKYCProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('full_name', models.CharField(blank=True, max_length=255)),
                ('country', models.CharField(blank=True, max_length=2)),
                ('tax_id', models.CharField(blank=True, max_length=64)),
                ('legal_address', models.TextField(blank=True)),
                ('payout_legal_entity_name', models.CharField(blank=True, max_length=255)),
                (
                    'status',
                    models.CharField(
                        choices=[('draft', 'Draft'), ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                        default='draft',
                        max_length=32,
                    ),
                ),
                ('rejection_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'reviewed_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='reviewed_kyc_profiles',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'trainer',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='trainer_kyc_profile',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='LegalAcceptanceSnapshot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('actor_type', models.CharField(choices=[('user', 'User'), ('trainer', 'Trainer')], max_length=32)),
                ('accepted_at', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('body_snapshot', models.TextField()),
                ('title_snapshot', models.CharField(max_length=255)),
                ('version_snapshot', models.CharField(max_length=32)),
                (
                    'document',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='acceptance_snapshots',
                        to='legal_compliance.legaldocumenttemplate',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='legal_acceptances',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='TrainerContractArtifact',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('artifact_path', models.CharField(blank=True, max_length=1024)),
                ('version', models.CharField(blank=True, max_length=32)),
                (
                    'status',
                    models.CharField(
                        choices=[('pending', 'Pending'), ('generated', 'Generated'), ('signed', 'Signed'), ('archived', 'Archived')],
                        default='pending',
                        max_length=32,
                    ),
                ),
                ('generated_at', models.DateTimeField(blank=True, null=True)),
                ('signed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'document_template',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to='legal_compliance.legaldocumenttemplate',
                    ),
                ),
                (
                    'trainer',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='contract_artifacts',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='PayoutEligibilitySnapshot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('kyc_status', models.CharField(blank=True, max_length=32)),
                ('has_active_agreement', models.BooleanField(default=False)),
                ('has_verified_payout_profile', models.BooleanField(default=False)),
                ('is_eligible', models.BooleanField(default=False)),
                ('block_reason', models.TextField(blank=True)),
                ('calculated_at', models.DateTimeField(auto_now=True)),
                (
                    'trainer',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='payout_eligibility_snapshot',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='ConsentLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    'consent_type',
                    models.CharField(
                        choices=[
                            ('terms_acceptance', 'Terms acceptance'),
                            ('privacy_acceptance', 'Privacy acceptance'),
                            ('refund_policy_acceptance', 'Refund policy acceptance'),
                            ('trainer_agreement_acceptance', 'Trainer agreement acceptance'),
                            ('marketing', 'Marketing consent'),
                        ],
                        max_length=64,
                    ),
                ),
                ('granted', models.BooleanField(default=True)),
                ('source', models.CharField(blank=True, max_length=64)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                (
                    'acceptance',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='consent_logs',
                        to='legal_compliance.legalacceptancesnapshot',
                    ),
                ),
                (
                    'document',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='consent_logs',
                        to='legal_compliance.legaldocumenttemplate',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='consent_logs',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]

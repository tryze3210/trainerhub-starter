from apps.payouts.models import PayoutRequest, TrainerBalance


def get_balance_for_trainer(trainer_id):
    return TrainerBalance.objects.filter(trainer_id=trainer_id).first()


def list_payout_requests_for_trainer(trainer_id):
    return PayoutRequest.objects.filter(trainer_id=trainer_id).order_by('-created_at')


def list_all_payout_requests():
    return PayoutRequest.objects.all().order_by('-created_at')

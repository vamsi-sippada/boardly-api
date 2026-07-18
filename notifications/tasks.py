from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_due_date_reminders(self):
    """
    Runs every morning at 8am.
    Finds all cards due within the next 24 hours that aren't done,
    and creates a notification for every assigned member.
    """
    try:
        from cards.models import Card, CardMember
        from notifications.models import Notification

        now        = timezone.now()
        in_24_hours = now + timezone.timedelta(hours=24)

        # Cards due in the next 24 hours that are not done
        upcoming_cards = Card.objects.filter(
            due_date__gte=now,
            due_date__lte=in_24_hours,
        ).exclude(
            status='done'
        ).prefetch_related('memberships__user', 'assignees')

        notifications = []
        for card in upcoming_cards:
            # Notify every user assigned to this card
            for card_member in card.memberships.all():
                notifications.append(
                    Notification(
                        recipient=card_member.user,
                        message=(
                            f'Reminder: card "{card.title}" is due '
                            f'on {card.due_date.strftime("%b %d at %I:%M %p")}'
                        )
                    )
                )

        if notifications:
            Notification.objects.bulk_create(notifications)

        return f'Sent {len(notifications)} due date reminders'

    except Exception as exc:
        # Retry the task if it fails, with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task
def send_overdue_notifications():
    """
    Runs every morning at 9am.
    Finds all cards that are past their due date and not done,
    notifies assigned members that their card is overdue.
    """
    from cards.models import Card
    from notifications.models import Notification

    now = timezone.now()

    overdue_cards = Card.objects.filter(
        due_date__lt=now,
    ).exclude(
        status='done'
    ).prefetch_related('memberships__user')

    notifications = []
    for card in overdue_cards:
        for card_member in card.memberships.all():
            notifications.append(
                Notification(
                    recipient=card_member.user,
                    message=f'Overdue: card "{card.title}" was due on {card.due_date.strftime("%b %d")}'
                )
            )

    if notifications:
        Notification.objects.bulk_create(notifications)

    return f'Sent {len(notifications)} overdue notifications'

@shared_task
def test_celery():
    """Simple task to verify Celery is working."""
    return 'Celery is working correctly!'
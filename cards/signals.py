from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Card, Comment, CardMember, ActivityLog
from notifications.models import Notification

User = get_user_model()


def create_activity(card, actor, verb):
    """
    Helper to create an ActivityLog entry.
    Centralised so the verb format is consistent everywhere.
    actor can be None (e.g. system-generated events).
    """
    ActivityLog.objects.create(
        card=card,
        actor=actor,
        verb=verb
    )


def notify_board_members(card, message, exclude_user=None):
    """
    Creates a Notification for every board member except the actor.
    exclude_user — the person who performed the action
                   (no point notifying yourself)
    """
    board = card.list.board
    memberships = board.memberships.select_related('user').all()

    notifications = []
    for membership in memberships:
        if exclude_user and membership.user == exclude_user:
            continue
        notifications.append(
            Notification(
                recipient=membership.user,
                message=message
            )
        )
    # bulk_create — one INSERT for all notifications, not one per member
    Notification.objects.bulk_create(notifications)


# ─── Card signals ─────────────────────────────────────────────────────────────

@receiver(post_save, sender=Card)
def card_post_save(sender, instance, created, **kwargs):
    """
    Fires every time a Card is saved.
    created=True  → new card
    created=False → card was updated
    """
    if created:
        # Who created the card? stored on instance.created_by
        actor = instance.created_by
        verb  = f'created card "{instance.title}"'
        create_activity(instance, actor, verb)

        notify_board_members(
            card=instance,
            message=f'{actor.username if actor else "Someone"} created card "{instance.title}"',
            exclude_user=actor
        )
    else:
        # Card was updated — log what changed
        # We check the status field specifically for meaningful logging
        actor = getattr(instance, '_updated_by', None)
        verb  = f'updated card "{instance.title}"'
        create_activity(instance, actor, verb)


@receiver(post_delete, sender=Card)
def card_post_delete(sender, instance, **kwargs):
    """
    Fires when a Card is deleted.
    Note: ActivityLog entries for this card are also deleted (CASCADE)
    so we log on the board level instead — but for simplicity
    we just note it here. In production you'd log to a board-level log.
    """
    pass  # ActivityLog cascades with card deletion


# ─── Comment signals ───────────────────────────────────────────────────────────

@receiver(post_save, sender=Comment)
def comment_post_save(sender, instance, created, **kwargs):
    """
    Fires when a Comment is created or updated.
    """
    if created:
        actor = instance.author
        verb  = f'commented on card "{instance.card.title}"'
        create_activity(instance.card, actor, verb)

        notify_board_members(
            card=instance.card,
            message=f'{actor.username if actor else "Someone"} commented: "{instance.body[:50]}"',
            exclude_user=actor
        )


# ─── CardMember signals ────────────────────────────────────────────────────────

@receiver(post_save, sender=CardMember)
def card_member_assigned(sender, instance, created, **kwargs):
    """
    Fires when a user is assigned to a card.
    instance.user  → the user being assigned
    instance.card  → the card they're assigned to
    """
    if created:
        verb = f'assigned {instance.user.username} to card "{instance.card.title}"'
        create_activity(instance.card, actor=None, verb=verb)

        # Notify the assigned user specifically
        Notification.objects.create(
            recipient=instance.user,
            message=f'You were assigned to card "{instance.card.title}"'
        )


@receiver(post_delete, sender=CardMember)
def card_member_unassigned(sender, instance, **kwargs):
    """
    Fires when a user is removed from a card.
    """
    verb = f'removed {instance.user.username} from card "{instance.card.title}"'
    create_activity(instance.card, actor=None, verb=verb)
from django.db.models.signals import post_save
from django.dispatch import receiver
from boards.models import BoardMember
from notifications.models import Notification


@receiver(post_save, sender=BoardMember)
def board_member_added(sender, instance, created, **kwargs):
    """
    Fires when someone is added to a board.
    Notifies the new member.
    """
    if created:
        Notification.objects.create(
            recipient=instance.user,
            message=f'You were added to board "{instance.board.title}" as {instance.role}'
        )
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Card, CardMember, Comment, ActivityLog

User = get_user_model()

class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'card', 'author', 'author_username', 'body', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'card', 'created_at', 'updated_at']

class ActivityLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'actor', 'actor_username', 'verb', 'created_at']
        read_only_fields = ['id', 'actor', 'verb', 'created_at']

class CardMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = CardMember
        fields = ['id', 'card', 'user', 'username', 'assigned_at']
        read_only_fields = ['id', 'assigned_at']

class CardSerializer(serializers.ModelSerializer):
    """Lightweight — used in list views."""
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Card
        fields = ['id', 'title', 'status', 'priority', 'due_date', 'position', 'is_overdue', 'list']
        read_only_fields = ['id', 'list']

    def get_is_overdue(self, obj):
        if not obj.due_date:
            return False
        return obj.due_date < timezone.now() and obj.status != Card.Status.DONE
    
class CardDetailSerializer(serializers.ModelSerializer):
    """Full detail — includes assignees, comments, activity log."""
    is_overdue = serializers.SerializerMethodField()
    memberships = CardMemberSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    activity_logs = ActivityLogSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Card
        fields = ['id', 'title', 'description', 'status', 'priority', 'due_date', 'position', 'is_overdue', 'list', 'created_by', 'created_by_username', 'memberships', 'comments', 'activity_logs', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_is_overdue(self, obj):
        if not obj.due_date:
            return False
        return obj.due_date < timezone.now() and obj.status != Card.Status.DONE
    
    def validate_due_date(self, value):
        if value and value < timezone.now():
            raise serializers.ValidationError("Due date cannot be in the past.")
        return value
    
class AssignMemberSerializer(serializers.Serializer):
    """Used for the assign-member action on a card."""
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
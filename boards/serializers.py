from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Board, BoardMember, BoardMembership, List

User = get_user_model()

class BoardMemberSerializer(serializers.ModelSerializer):
    """Represents one membership — used inside BoardDetailSerializer."""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = BoardMembership
        fields = ['id', 'user', 'username', 'email', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']

class AddMemberSerializer(serializers.ModelSerializer):
    """Used for the add-member action — validates incoming user_id and role."""
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.Objects.all())
    role = serializers.ChoiceField(choices=BoardMember.Role.choices, default=BoardMember.Role.MEMBER)

class ListSerializer(serializers.ModelSerializer):
    class Meta:
        model = List
        fields = ['id', 'name', 'position', 'board']
        read_only_fields = ['id', 'board']

class BoardSerializer(serializers.ModelSerializer):
    """Lightweight — used in list views."""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ['id', 'title', 'description','visibility' ,'owner', 'owner_username', 'member_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_member_count(self, obj):
        return obj.memberships.count()
    
class BoardDetailSerializer(serializers.ModelSerializer):
    """Full detail — used in retrieve view. Includes members and lists."""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    memberships = BoardMemberSerializer(many=True, read_only=True)
    lists = ListSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ['id', 'title', 'description', 'visibility', 'owner', 'owner_username', 'member_count', 'memberships', 'lists', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner' ,'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.memberships.count()
# Collaboration Views

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .collaboration_models import (
    ActivityLog,
    CollaborationSession,
    Comment,
    Notification,
    TeamMember,
)

# Get the custom user model
User = get_user_model()


class CollaborationViewSet(viewsets.ViewSet):
    """Real-time collaboration features."""
    
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def create_session(self, request):
        """Create a new collaboration session."""
        session_name = request.data.get('name', 'Collaboration Session')
        description = request.data.get('description', '')
        is_public = request.data.get('is_public', False)
        
        try:
            session = CollaborationSession.objects.create(
                name=session_name,
                description=description,
                is_public=is_public,
                owner=request.user if request.user.is_authenticated else None
            )
            
            # Add owner as team member
            if request.user.is_authenticated:
                TeamMember.objects.create(
                    session=session,
                    user=request.user,
                    role='owner',
                    status='online'
                )
            
            return Response({
                'session_id': str(session.id),
                'name': session.name,
                'description': session.description,
                'is_public': session.is_public,
                'created_at': session.created_at.isoformat()
            })
            
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def invite_member(self, request, pk=None):
        """Invite a team member to the session."""
        email = request.data.get('email')
        role = request.data.get('role', 'viewer')
        permissions = request.data.get('permissions', [])
        
        if not email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = CollaborationSession.objects.get(id=pk)
            
            # Check if user exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User with this email does not exist'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if already a member
            if TeamMember.objects.filter(session=session, user=user).exists():
                return Response(
                    {'error': 'User is already a member of this session'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create team member
            team_member = TeamMember.objects.create(
                session=session,
                user=user,
                role=role,
                permissions=permissions,
                invited_by=request.user if request.user.is_authenticated else None
            )
            
            # Log activity
            ActivityLog.objects.create(
                session=session,
                user=request.user if request.user.is_authenticated else user,
                action='member_invited',
                details={'invited_user': user.username, 'role': role}
            )
            
            return Response({
                'member_id': str(team_member.id),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'role': team_member.role,
                'permissions': team_member.permissions,
                'status': team_member.status,
                'joined_at': team_member.joined_at.isoformat()
            })
            
        except CollaborationSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def team_members(self, request, pk=None):
        """Get all team members for a session."""
        try:
            session = CollaborationSession.objects.get(id=pk)
            members = TeamMember.objects.filter(session=session).select_related('user')
            
            members_data = []
            for member in members:
                members_data.append({
                    'id': str(member.id),
                    'user': {
                        'id': member.user.id,
                        'username': member.user.username,
                        'email': member.user.email,
                        'first_name': member.user.first_name,
                        'last_name': member.user.last_name
                    },
                    'role': member.role,
                    'permissions': member.permissions,
                    'status': member.status,
                    'last_active': member.last_active.isoformat() if member.last_active else None,
                    'joined_at': member.joined_at.isoformat()
                })
            
            return Response({'members': members_data})
            
        except CollaborationSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add a comment to the session."""
        content = request.data.get('content')
        node_id = request.data.get('node_id')  # Optional: for node-specific comments
        
        if not content:
            return Response(
                {'error': 'Content is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = CollaborationSession.objects.get(id=pk)
            
            comment = Comment.objects.create(
                session=session,
                author=request.user if request.user.is_authenticated else None,
                content=content,
                node_id=node_id
            )
            
            # Log activity
            ActivityLog.objects.create(
                session=session,
                user=request.user if request.user.is_authenticated else None,
                action='comment_added',
                details={'comment_id': str(comment.id), 'node_id': node_id}
            )
            
            return Response({
                'comment_id': str(comment.id),
                'content': comment.content,
                'node_id': comment.node_id,
                'author': {
                    'id': comment.author.id if comment.author else None,
                    'username': comment.author.username if comment.author else 'Anonymous',
                },
                'created_at': comment.created_at.isoformat(),
                'resolved': comment.resolved
            })
            
        except CollaborationSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get all comments for a session."""
        node_id = request.query_params.get('node_id')
        
        try:
            session = CollaborationSession.objects.get(id=pk)
            
            comments = Comment.objects.filter(session=session).select_related('author')
            
            if node_id:
                comments = comments.filter(node_id=node_id)
            
            comments_data = []
            for comment in comments.order_by('created_at'):
                comments_data.append({
                    'id': str(comment.id),
                    'content': comment.content,
                    'node_id': comment.node_id,
                    'author': {
                        'id': comment.author.id if comment.author else None,
                        'username': comment.author.username if comment.author else 'Anonymous',
                        'first_name': comment.author.first_name if comment.author else '',
                        'last_name': comment.author.last_name if comment.author else ''
                    },
                    'created_at': comment.created_at.isoformat(),
                    'resolved': comment.resolved
                })
            
            return Response({'comments': comments_data})
            
        except CollaborationSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def activity(self, request, pk=None):
        """Get activity log for a session."""
        limit = int(request.query_params.get('limit', 50))
        
        try:
            session = CollaborationSession.objects.get(id=pk)
            
            activities = ActivityLog.objects.filter(session=session).select_related('user').order_by('-timestamp')[:limit]
            
            activities_data = []
            for activity in activities:
                activities_data.append({
                    'id': str(activity.id),
                    'action': activity.action,
                    'details': activity.details,
                    'user': {
                        'id': activity.user.id if activity.user else None,
                        'username': activity.user.username if activity.user else 'System',
                    },
                    'timestamp': activity.timestamp.isoformat()
                })
            
            return Response({'activities': activities_data})
            
        except CollaborationSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def update_presence(self, request, pk=None):
        """Update user presence in the session."""
        status = request.data.get('status', 'online')  # online, away, offline
        cursor_position = request.data.get('cursor_position')
        
        try:
            session = CollaborationSession.objects.get(id=pk)
            
            if request.user.is_authenticated:
                team_member = TeamMember.objects.filter(
                    session=session, 
                    user=request.user
                ).first()
                
                if team_member:
                    team_member.status = status
                    team_member.last_active = timezone.now()
                    team_member.cursor_position = cursor_position
                    team_member.save()
            
            return Response({'status': 'Presence updated'})
            
        except CollaborationSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationViewSet(viewsets.ViewSet):
    """Notification management for collaboration."""
    
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def list_notifications(self, request):
        """Get notifications for the current user."""
        if not request.user.is_authenticated:
            return Response({'notifications': []})
        
        notifications = Notification.objects.filter(
            recipient=request.user,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-created_at')[:50]
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': str(notification.id),
                'type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'read': notification.read,
                'data': notification.data,
                'created_at': notification.created_at.isoformat()
            })
        
        return Response({'notifications': notifications_data})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read."""
        try:
            notification = Notification.objects.get(
                id=pk, 
                recipient=request.user if request.user.is_authenticated else None
            )
            notification.read = True
            notification.save()
            
            return Response({'status': 'Notification marked as read'})
            
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
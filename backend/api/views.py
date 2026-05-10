from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from .models import Post, Comment
from .serializers import UserSerializer, RegisterSerializer, PostSerializer, CommentSerializer

User = get_user_model()

# ── Auth ──────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user, context={'request': request}).data}, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user, context={'request': request}).data})
    return Response({'error': 'Invalid credentials'}, status=400)

@api_view(['POST'])
def logout(request):
    request.user.auth_token.delete()
    return Response({'message': 'Logged out'})

# ── Users ─────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def me(request):
    serializer = UserSerializer(request.user, context={'request': request})
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
def update_profile(request):
    serializer = UserSerializer(request.user, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    serializer = UserSerializer(user, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def user_posts(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user)
    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def follow_user(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return Response({'error': 'Cannot follow yourself'}, status=400)
    if target.followers.filter(id=request.user.id).exists():
        target.followers.remove(request.user)
        return Response({'following': False, 'followers_count': target.followers.count()})
    else:
        target.followers.add(request.user)
        return Response({'following': True, 'followers_count': target.followers.count()})

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_users(request):
    q = request.query_params.get('q', '')
    users = User.objects.filter(username__icontains=q)[:10]
    serializer = UserSerializer(users, many=True, context={'request': request})
    return Response(serializer.data)

# ── Posts ─────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def feed(request):
    posts = Post.objects.all()
    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
def home_feed(request):
    following_ids = request.user.following.values_list('id', flat=True)
    posts = Post.objects.filter(author__id__in=list(following_ids) + [request.user.id])
    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def create_post(request):
    serializer = PostSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(author=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['GET', 'PUT', 'DELETE'])
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'GET':
        return Response(PostSerializer(post, context={'request': request}).data)
    if post.author != request.user:
        return Response({'error': 'Not allowed'}, status=403)
    if request.method == 'PUT':
        serializer = PostSerializer(post, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    post.delete()
    return Response(status=204)

@api_view(['POST'])
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        return Response({'liked': False, 'likes_count': post.likes.count()})
    post.likes.add(request.user)
    return Response({'liked': True, 'likes_count': post.likes.count()})

# ── Comments ──────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def post_comments(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'GET':
        serializer = CommentSerializer(post.comments.all(), many=True, context={'request': request})
        return Response(serializer.data)
    if not request.user.is_authenticated:
        return Response({'error': 'Login required'}, status=401)
    serializer = CommentSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(author=request.user, post=post)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['DELETE'])
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.author != request.user:
        return Response({'error': 'Not allowed'}, status=403)
    comment.delete()
    return Response(status=204)

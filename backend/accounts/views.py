from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from musics.serializers import PlaylistSerializer
from .algorithms.algorithm import recommend_ost, calculate_vector
from .serializers import *
from musics.models import Music
from accounts.models import MusicUserLike, User


from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

import numpy as np
from muvie.settings import SECRET_KEY
import jwt

class SignupAPIView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # jwt 토큰 접근
            token = TokenObtainPairSerializer.get_token(user)
            refresh_token = str(token)
            access_token = str(token.access_token)
            res = Response(
                {
                    "user": serializer.data,
                    "message": "register successs",
                    "token": {
                        "access": access_token,
                        "refresh": refresh_token,
                    },
                },
                status=status.HTTP_200_OK,
            )
            
            # jwt 토큰 => 쿠키에 저장
            res.set_cookie("access", access_token, httponly=True)
            res.set_cookie("refresh", refresh_token, httponly=True)
            
            return res
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AuthAPIView(APIView):
    # 유저 정보 확인
    def get(self, request):
        try:
            # access token을 decode 해서 유저 id 추출 => 유저 식별
            access = request.COOKIES['access']
            payload = jwt.decode(access, SECRET_KEY, algorithms=['HS256'])
            pk = payload.get('user_id')
            user = get_object_or_404(User, pk=pk)
            serializer = UserSerializer(instance=user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except(jwt.exceptions.ExpiredSignatureError):
            # 토큰 만료 시 토큰 갱신
            data = {'refresh': request.COOKIES.get('refresh', None)}
            serializer = TokenRefreshSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                access = serializer.data.get('access', None)
                refresh = serializer.data.get('refresh', None)
                payload = jwt.decode(access, SECRET_KEY, algorithms=['HS256'])
                pk = payload.get('user_id')
                user = get_object_or_404(User, pk=pk)
                serializer = UserSerializer(instance=user)
                res = Response(serializer.data, status=status.HTTP_200_OK)
                res.set_cookie('access', access)
                res.set_cookie('refresh', refresh)
                return res
            raise jwt.exceptions.InvalidTokenError

        except(jwt.exceptions.InvalidTokenError):
            # 사용 불가능한 토큰일 때
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
    	# 유저 인증
        email = request.data.get('email')
        password = request.data.get('password')
        print(check_password(password, encoded=User.objects.get(email=email).password))
        user = authenticate(email=email, password=password)
        print(user)
        # 이미 회원가입 된 유저일 때
        if user is not None:
            serializer = UserSerializer(user)
            # jwt 토큰 접근
            token = TokenObtainPairSerializer.get_token(user)
            refresh_token = str(token)
            access_token = str(token.access_token)
            res = Response(
                {
                    "user": serializer.data,
                    "message": "login success",
                    "token": {
                        "access": access_token,
                        "refresh": refresh_token,
                    },
                },
                status=status.HTTP_200_OK,
            )
            # jwt 토큰 => 쿠키에 저장
            res.set_cookie("access", access_token, httponly=True)
            res.set_cookie("refresh", refresh_token, httponly=True)
            return res
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


    # 로그아웃
    def delete(self, request):  
        # 쿠키에 저장된 토큰 삭제 => 로그아웃 처리
        response = Response({
            "message": "Logout success"
            }, status=status.HTTP_202_ACCEPTED)
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        return response

class FollowAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, user_pk):
        user = User.objects.get(pk=user_pk)
        serializer = FollowSerializer(user)
        return Response(serializer.data)

    def post(self, request, user_pk):
        user = request.user
        opponent = User.objects.get(pk=user_pk)
        if opponent in user.following.all():
            return Response({
                "message" : "already followed"
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.following.add(opponent)
            serializer = FollowSerializer(user)
            return Response(serializer.data)
    def delete(self, request, user_pk):
        user = request.user
        opponent = User.objects.get(pk=user_pk)
        if opponent not in user.following.all():
            return Response({
                "message" : "Not followed"
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = FollowSerializer(user)
            user.following.remove(opponent)
            return Response(serializer.data)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, user_pk):
        me = request.user
        if user_pk == me.pk:
            print(me)
            serializer = MyProfileSerializer(instance=me, user_pk=me.pk)
            user_serializer = SimpleUserSerializer(me)
            response = {
                "user_profile" : user_serializer.data,
                "detail" : serializer.data
            }
            return Response(response)
        else:
            user = User.objects.get(pk=user_pk)
            serializer = ProfileSerializer(instance=user, user_pk=me.pk)
            user_serializer = SimpleUserSerializer(user)
            print(123412412412342, user_serializer.data)
            response = {
                "user_profile" : user_serializer.data,
                "detail" : serializer.data
            }
        return Response(response)
        
class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request, user_pk):
        user = User.objects.get(pk=user_pk)
        new_password = request.data.get('new_password')
        new_password_confirm = request.data.get('new_password_confirm')
        if new_password == new_password_confirm:
            user.password = new_password
            return Response(SimpleUserSerializer(user).data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

class AccountsChangeView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request, user_pk):
        user = User.objects.get(pk=user_pk)
        if request.user != user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = UserChangeSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Change Success",
                             "changed_data" : UserChangeSerializer(User.objects.get(pk=user_pk)).data
                             })
        return Response(serializers.error, status=status.HTTP_400_BAD_REQUEST)

class LikeListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        like_list = user.like_music.all()
        serializer = PlaylistSerializer(like_list, many=True)
        return Response(serializer.data)

class PlaylistView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        playlist = user.playlist.all()
        serializer = PlaylistSerializer(playlist, many=True)
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommend_components(request):
    user = request.user
    component = user.music_components
    data = {
        'energy': component.energy,
        'instrumentalness': component.instrumentalness,
        'liveness': component.liveness,
        'acousticness': component.acousticness,
        'speechiness': component.speechiness,
        'valence': component.valence,
        'tempo': component.tempo,
        'mode': component.mode,
        'loudness': component.loudness,
        'danceability': component.danceability,
    }
    recommend_list = recommend_ost(data)
    response = {"data":[]}
    for recommend in recommend_list['tracks']:
        title = recommend['name']
        artist = recommend['artists'][0]['name']
        album = recommend['album']['name']
        uri = recommend['uri']
        poster = recommend['album']['images'][0]['url']
        if Music.objects.filter(title=title, artist=artist):
           response['data'].append({"title":title, "artist":artist, 'album':album, "uri":uri, 'poster':poster})
        else:
            new = Music.objects.create(
                title=title, artist=artist, uri=uri, album_cover = poster
            )
            new.save()
            response['data'].append({"title":title, "artist":artist, 'album':album, "uri":uri, 'poster':poster})
    return Response(response)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommend_user(request):
    user = request.user
    random_users = User.objects.order_by('?')[:10] # 대규모로 갈 경우 속도가 느려지기 때문에 후에 수정
    user_vector = calculate_vector(user)
    random_user_list = []

    for random_user in random_users:
        random_user_vector = calculate_vector(random_user)
        similarity = cosine_similarity(user_vector, random_user_vector)[0][0]
        random_user_list.append((similarity, random_user))
        
    random_user_list.sort(key=lambda x: x[0], reverse=True)
    topusers = [user[1] for user in random_user_list[:3]]
    user_serializer = SimpleUserSerializer(topusers, many=True)
    return Response({"recommend":user_serializer.data})
    
    # 가장 유사도가 높은 사용자 정보 반환

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommend_like(request):
    user = request.user
    recent_likes = MusicUserLike.objects.filter(user=user).order_by('-created_at')[:10]
    liked_songs = [like.music for like in recent_likes]

    all_users = User.objects.exclude(id=user.id)
    number_users = len(all_users)
    user_item_matrix = np.zeros((number_users, 10))

    for i, other_user in enumerate(all_users):
        other_likes = MusicUserLike.objects.filter(user=other_user).order_by('-created_at')[:10]
        for j, like in enumerate(other_likes):
            if like.music in liked_songs:
                user_item_matrix[i, j] = 1

    number_neighbor = 3
    if number_users >= number_neighbor:
        model = NearestNeighbors(n_neighbors=number_neighbor, metric='cosine')
        model.fit(user_item_matrix)
        print(all_users)
        user_index = list(all_users).index(user)
        user_vector = user_item_matrix[user_index].reshape(1, -1)
        distances, indices = model.kneighbors(user_vector)

        recommendations = []
        for i in range(number_neighbor):
            neighbor_index = indices[0][i]
            neighbor_user = all_users[neighbor_index]
            neighbor_likes = MusicUserLike.objects.filter(user=neighbor_user)
            for like in neighbor_likes:
                if like.music not in liked_songs:
                    recommendations.append(like.music)

        print(recommendations)
    else:
        print("Insufficient data for recommendation")
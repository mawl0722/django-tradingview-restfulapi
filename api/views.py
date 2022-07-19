import requests
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from extentions.addToWallet import WalletManagment

from pycoingecko import CoinGeckoAPI
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework import status


from .serializers import *

from rest_framework.views import APIView

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView, \
    RetrieveUpdateDestroyAPIView, RetrieveDestroyAPIView, CreateAPIView, ListAPIView, UpdateAPIView
from rest_framework import viewsets
from rest_framework import serializers
from rest_framework.response import Response

from .permissions import *

from .models import Position, Coin_list

User = get_user_model()


class UserList(ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsSuperUser,)


class UserDetail(RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsUser,)


class PositionList(ListAPIView):
    serializer_class = PositionSerializer
    permission_classes = (Is_Authenticated,IsUser)
    def get_queryset(self):
        user = self.request.user
        query = Position.objects.filter(paper_trading__user__id=user.id)
        return query

class PositionCloseUpdate(RetrieveUpdateDestroyAPIView):
    serializer_class = PositionCloseSerializer
    permission_classes = (Is_Authenticated,UserPosition,)

    def get_queryset(self):
        user = self.request.user
        query = Position.objects.filter(paper_trading__user__id=user.id)
        return query

    def delete(self, request, *args, **kwargs):
        user = self.request.user
        id = self.kwargs["pk"]
        position = Position.objects.get(id=id, paper_trading__user=user)
        if not position.status == "w":
            raise serializers.ValidationError("this position reached or closed ! you cant edit it")
        else:
            return self.destroy(request, *args, **kwargs)


class PositionCreate(CreateAPIView):
    serializer_class = PositionAddSerializer
    permission_classes = (Is_Authenticated,)

    def perform_create(self, serializer):
        user = self.request.user
        paper = user.paper_trading
        serializer.save(paper_trading=paper)


class PositionTotal(ListAPIView):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = (IsSuperUser,)


class PositionOptionCreate(ListCreateAPIView):
    serializer_class = PositionOptionCreateSerializer
    permission_classes = (Is_Authenticated,UserPositionOption,)

    def get_queryset(self):
        user = self.request.user
        id = self.kwargs['pk']
        query = Position_option.objects.filter(in_position=id, in_position__paper_trading__user=user)
        return query

    def perform_create(self, serializer):
        user = self.request.user
        id = self.kwargs['pk']
        position = Position.objects.get(id=id)
        option = Position_option.objects.filter(in_position=position, in_position__paper_trading__user=user)
        if not option:
            serializer.save(in_position=position)
        else:
            raise serializers.ValidationError("You already have a position option")


class PositionOptionUpdate(RetrieveUpdateDestroyAPIView):
    serializer_class = PositionOptionUpdateSerializer
    permission_classes = (Is_Authenticated,UserPositionOption,)
    lookup_field = "in_position"

    def get_queryset(self):
        user = self.request.user
        position_id = self.kwargs["in_position"]
        query = Position_option.objects.filter(in_position=position_id, in_position__paper_trading__user=user)
        return query
    def delete(self, request, *args, **kwargs):
        user = self.request.user
        position_id = self.kwargs["in_position"]
        position_option = Position_option.objects.get(in_position=position_id, in_position__paper_trading__user=user)
        if not position_option.status == "w" and not position_option.trade_type == "w" or not position_option.status == "p" and not position_option.status == "w":
            raise serializers.ValidationError("this position reached or closed ! you cant edit it")
        else:
            return self.destroy(request, *args, **kwargs)


class PositionOptionClose(RetrieveUpdateDestroyAPIView):
    serializer_class = PositionOptionCloseSerializer
    permission_classes = (Is_Authenticated,UserPositionOption,)
    lookup_field = "in_position"

    def get_queryset(self):
        user = self.request.user
        position_id = self.kwargs["in_position"]
        query = Position_option.objects.filter(in_position=position_id, in_position__paper_trading__user=user)
        return query


class PapertradingViewSet(viewsets.ModelViewSet):
    serializer_class = CreatePaperTradingSerializer
    permission_classes = (UserPapertrading,)

    def get_queryset(self):
        user = self.request.user
        query = Paper_trading.objects.filter(user=user)
        return query

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)


class PapertradingListView(ListCreateAPIView):
    serializer_class = CreatePaperTradingSerializer
    permission_classes = (Is_Authenticated,IsUser,)

    def get_queryset(self):
        user = self.request.user
        query = Paper_trading.objects.filter(user=user)
        return query

    def perform_create(self, serializer):
        user = self.request.user

        try:
            serializer.save(user=user)
            paper_trading = Paper_trading.objects.get(user=user)
            WalletManagment.check("usdt", paper_trading.balance, paper_trading)
        except IntegrityError:
            raise serializers.ValidationError("You already have a paper account")


class PapertradingDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = UpdatePaperTradingSerializer
    permission_classes = (Is_Authenticated,UserPapertrading,)

    def get_queryset(self):
        user = self.request.user
        query = Paper_trading.objects.filter(user=user)
        return query


class watchList_List(ListCreateAPIView):
    serializer_class = WatchListSerializer
    permission_classes = (Is_Authenticated,IsUser,)

    def get_queryset(self):
        user = self.request.user
        query = Watch_list.objects.filter(user=user)
        return query

    def perform_create(self, serializer):
        user = self.request.user
        try:
            serializer.save(user=user)
        except IntegrityError:
            raise serializers.ValidationError("You already have a paper account")


class watchList_Details(RetrieveDestroyAPIView):
    serializer_class = WatchListSerializer
    permission_classes = (Is_Authenticated,UserWatchList,)

    def get_queryset(self):
        user = self.request.user
        query = Watch_list.objects.filter(user=user)
        return query


class walletList(ListAPIView):
    serializer_class = WalletSerializer
    permission_classes = (Is_Authenticated,IsUser,)

    def get_queryset(self):
        user = self.request.user
        query = Wallet.objects.filter(paper_trading__user=user)
        return query


from extentions.watchList import WatchList_checker
from extentions.addToWallet import WalletManagment
from extentions.checkPositions import Position_checker
from extentions.checkPositionOption import Position_option_checker
from extentions.validateWallet import ValidateWalletCoin


def positions_checker(request):
    results = Position_checker.check()
    return HttpResponse(results)
def options_checker(request):
    results = Position_option_checker.check()
    return HttpResponse(results)





class coinListView(ListCreateAPIView):
    serializer_class = CoinSerializer
    permission_classes = (IsSuperUserOrReadOnly,)
    queryset = Coin_list.objects.all()


    def create(self, request, *args, **kwargs):
        # GET LAST COINS IN DB
        lastCoins = Coin_list.objects.values_list('coin')
        lastCoins = [coin[0] for coin in lastCoins]

        data = []
        get_coins = []
        url = 'https://min-api.cryptocompare.com/data/all/coinlist'
        res = requests.get(url)
        res = res.json()

        for coin in res['Data']:
            coinName = str(coin).lower()
            get_coins.append(coinName)

        # REMOVE DUPLICATED AND EXISTED COINS
        for elem in get_coins:
            if elem not in lastCoins and len(elem)<20:
                data.append({'coin':elem})

        # SEND DATA TO SERIALIZER
        serializer = self.get_serializer(data=data, many=True)

        # SERIALIZER VALIDATION
        serializer.is_valid(raise_exception=True)

        # CREATE AND SAVE NEW COINS TO DB
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

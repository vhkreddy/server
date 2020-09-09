import csv
import boto3
import os
import pandas as pd
import io
import json
import time
import pdb
import random
import zipfile
import string
import requests
import shutil
import datetime
from ftplib import FTP
from bs4 import BeautifulSoup
from io import StringIO
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import viewsets, filters, status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Count, Case, When, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from .aws_connect import AWSConnect
from .models import WordBank, WordReview, WordContest, Contest, ContestGroup

from .serializers import IssuesListSerializer, WordBankListSerializer, WordBankDownloadSerializer, ContestListSerializer, ContestGroupDetailSerializer, WordContestListSerializer, ContestWordListSerializer
# from authetication.models import User
# from authetication.serializers import UserSerializer
from authentication import serializers as auth_serializers
from authentication import models as auth_models
from .drf_utils.viewsets import GetSerializerClassMixin

class ViewsetBaseFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filter_dict = {key.strip(): value.strip()
                       for (key, value) in request.query_params.items()}
        
        if "word_bank__id__in" in filter_dict:
            filter_dict["word_bank__id__in"] = json.loads(filter_dict["word_bank__id__in"])
            
        if "ordering" in filter_dict:
            queryset = queryset.order_by(filter_dict["ordering"])
        else:
            try:
                queryset = queryset.order_by('-created_on')
            except:
                pass
            
        for entry in ("ordering", "page", "page_size", "format", "no_page"):
            if entry in filter_dict:
                del filter_dict[entry]
        return queryset.filter(**filter_dict)

class ModelViewSetPagination(PageNumberPagination):
    def paginate_queryset(self, queryset, request, view=None):
        if 'no_page' in request.query_params:
            self.page_size = len(queryset)
        elif 'page_size' in request.query_params: 
            self.page_size = request.query_params['page_size']
        return super().paginate_queryset(queryset, request, view)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def loadAndReviewWords(request):
    ftp_details = settings.NSF_FPT
    ftp = FTP()
    ftp.connect(ftp_details['server'], ftp_details['port'])
    ftp.login(ftp_details['username'], ftp_details['password'])
    
    alphabets = list(string.ascii_uppercase)
    word_types = {
        'file_name':'_word.m4a', 
        'file_name_origin':'_origin.m4a', 
        'file_name_sentence':'_sentence.m4a', 
        'file_name_complete':'_complete.m4a', 
        'file_name_definition':'_definition.m4a'
    }
    _errors = [
        'incomplete',
        'unavailable', 
        'low_voice', 
        'noise', 
        'not_clear', 
        'not_playing', 
        'repeating'
    ]
    for alphabet in alphabets:
        words = set() 
        words_dict = {}
        files = ftp.nlst(alphabet + '_Files/')
        
        for file in files:
            word = file.split('/')[1].lower()
            words_dict[word] = file
            words.add(word.split('_')[0])
            
        for word in words:
            word_instance, created = WordBank.objects.get_or_create(word=word)
            word_review_instance, created = WordReview.objects.get_or_create(word_bank=word_instance)
            word_review_instance.word = word
            word_instance.lexicographical = word[0]
            for field, extension in word_types.items():
                word_path = words_dict.get(word+extension)
                if word_path != None:
                    setattr(word_instance, field, word_path)
                    setattr(word_review_instance, field, 'available')
                else:
                    setattr(word_review_instance, field, 'unavailable')
                    setattr(word_review_instance, 'status', 'incomplete')
            review_word_values = (
                lambda word_review_instance,review_word_fields: [
                    getattr(word_review_instance,i,'') for i in review_word_fields
                ]
            )(word_review_instance, word_types.keys())
            
            if len(list(set(review_word_values) & set(_errors))) > 0:
                word_review_instance.status = 'incomplete'
            elif created:
                word_review_instance.status = 'open'
            word_instance.save()
            word_review_instance.save()
    ftp.quit()
    return JsonResponse({'type':'success', 'msg':'Loaded Successfully'} , safe=False)
    
class UserViewset(viewsets.ModelViewSet):
    queryset = auth_models.User.objects.all()
    serializer_class = auth_serializers.UserSerializer
    filter_backends = (ViewsetBaseFilter,)
    permission_classes = (AllowAny,)
    pagination_class = ModelViewSetPagination
    

class ContestViewset(viewsets.ModelViewSet):
    queryset = Contest.objects.all()
    serializer_class = ContestListSerializer
    filter_backends = (ViewsetBaseFilter,)
    permission_classes = (AllowAny,)
    pagination_class = ModelViewSetPagination

class ContestWordViewset(viewsets.ModelViewSet):
    queryset = WordContest.objects.all()
    serializer_class = ContestWordListSerializer
    filter_backends = (ViewsetBaseFilter,)
    permission_classes = (AllowAny,)
    pagination_class = ModelViewSetPagination

class ContestGroupViewset(viewsets.ModelViewSet):
    queryset = ContestGroup.objects.all()
    serializer_class = ContestGroupDetailSerializer
    filter_backends = (ViewsetBaseFilter,)
    permission_classes = (AllowAny,)
    pagination_class = ModelViewSetPagination

# class WordContestViewset(viewsets.ModelViewSet):
#     queryset = WordContest.objects.values('word_group').annotate(
#         JSB_PHASE1=Count('phase',filter=Q(spellbee_type='JSB', phase="Phase 1")),
#         JSB_PHASE2=Count('phase',filter=Q(spellbee_type='JSB', phase="Phase 2")), 
#         JSB_FINALS=Count('phase',filter=Q(spellbee_type='JSB', phase="Finals")),
#         SSB_PHASE1=Count('phase',filter=Q(spellbee_type='SSB', phase="Phase 1")),
#         SSB_PHASE2=Count('phase',filter=Q(spellbee_type='SSB', phase="Phase 2")), 
#         SSB_FINALS=Count('phase',filter=Q(spellbee_type='SSB', phase="Finals")) 
#     )
#     serializer_class = WordContestListSerializer
#     # filter_backends = (ViewsetBaseFilter,)
#     permission_classes = (AllowAny,)
#     pagination_class = ModelViewSetPagination

class IssuesViewset(GetSerializerClassMixin, viewsets.ModelViewSet):
    queryset = WordReview.objects.all()
    serializer_class = IssuesListSerializer
    # serializer_action_classes = {
    #     'list': IssuesListSerializer,
    # }
    filter_backends = (ViewsetBaseFilter,)
    permission_classes = (AllowAny,)
    pagination_class = ModelViewSetPagination
    
    @action(detail=False, schema=None, methods=['POST'], url_path='update_row')
    def update_row(self, request, *args, **kwargs):
        result = request.data
        wr = WordReview.objects.get(id=int(result['id']))
        # avl_excel_files = {'JSB':'JSB word list.csv', 'SSB':'SSB word list.csv'}
        # connect = AWSConnect()
        text_fields = {
            'word': 'Word', 
            'pronunciation': 'Pronunciation', 
            'pos': 'POS', 
            'land_of_origin': 'Origin', 
            'additional_info': 'Definitions', 
            'sentence': 'Sentence',
            'phase': 'Category',
            'difficulty_level': 'Difficulty Level',
            'spellbee_type': 'Spellbee Type'
        }
        audio_fields = [
            'file_name',
            'file_name_origin',
            'file_name_sentence',
            'file_name_complete',
            'file_name_definition'
        ]
        
        # excel_path = 'excel_files/' + avl_excel_files[wr.word_bank.spellbee_type]
        # file = connect.getKey(excel_path).get('Body')
        # df = pd.read_csv(io.StringIO(file.read().decode('utf-8')), delimiter=',')
        
        # selecting rows based on condition 
        # df_id =  df.index[df['Word'] == wr.word_bank.word].tolist()[0]
        
        #updating values as well as updating reviews
        for key, value in result.items():
            if key.startswith('word_bank__'):
                wb_column = key.replace('word_bank__', '')
                if wb_column in text_fields.keys():
                    setattr(wr.word_bank, wb_column, value)
                    # df.at[df_id,text_fields[wb_column]]= value
                    setattr(wr, wb_column, 'available')
                    if value == '':
                        setattr(wr, wb_column, 'unavailable')
            if key in audio_fields:
                setattr(wr, key, value)

        #uploading updated csv file
        # csv_buffer = StringIO()
        # df.to_csv(csv_buffer, index=False)               
        # connect.s3client.put_object(Bucket=connect.bucket,Key=excel_path, Body=csv_buffer.getvalue())
        
        #updating wordreview status
        # review_word_fields = audio_fields
        # if result['status'] != 'deleted' and result['status'] == wr.status:
        #     review_word_values = (lambda review_word,review_word_fields: [getattr(wr,i,'') for i in review_word_fields])(wr, review_word_fields)
        #     _errors = ['incomplete', 'unavailable', 'low_voice', 'noise', 'not_clear', 'not_playing', 'repeating']
        #     if len(list(set(review_word_values) & set(_errors))) > 0:
        #         wr.status = 'incomplete'
        #     else:
        #         wr.status = 'complete'
        # else:
        #     wr.status = result['status']
        # wr.modified_by = request.user.email
        # wr.modified_on = datetime.date.today
        wr.status = result['status']
        wr.comments = result['comments']
        wr.word_bank.save()
        wr.is_dirty = True
        wr.save()
        return Response({'message': 'successfully uploaded audio file'}, status=status.HTTP_200_OK)
    
    @action(detail=False, schema=None, methods=['POST'], url_path='delete_word')
    def delete_word(self, request, *args, **kwargs):
        audio_fields = [
            'file_name',
            'file_name_origin',
            'file_name_sentence',
            'file_name_complete',
            'file_name_definition'
        ]
        
        wr = WordReview.objects.get(id=int(request.data['id']))
        review_word_fields = audio_fields
        if wr.status == 'deleted':
            review_word_values = (lambda review_word,review_word_fields: [getattr(wr,i,'') for i in review_word_fields])(wr, review_word_fields)
            _errors = ['incomplete','unavailable', 'low_voice', 'noise', 'not_clear', 'not_playing', 'repeating']
            if len(list(set(review_word_values) & set(_errors))) > 0:
                wr.status = 'incomplete'
            else:
                wr.status = 'complete'
        else:
            wr.status = 'deleted'
        wr.is_dirty = True
        wr.save()
        return Response({'message': 'successfully uploaded audio file'}, status=status.HTTP_200_OK)
    
    @action(detail=False, schema=None, methods=['POST'], url_path='upload_audio')
    def upload(self, request, *args, **kwargs):
        ftp_details = settings.NSF_FPT
        wr = WordReview.objects.get(id=int(request.data['id']))
        column = request.data['column']
        audio_file = request.FILES['file']
        file_path = request.data['file_path']
        ftp = FTP()
        ftp.connect(ftp_details['server'], ftp_details['port'])
        ftp.login(ftp_details['username'], ftp_details['password'])
        up = ftp.storbinary('STOR '+file_path, audio_file)
        ftp.quit()
        if getattr(wr,column) == 'unavailable':
            setattr(wr,column, 'available')
        wr.is_dirty = True
        wr.save()
        return Response({'message': 'successfully uploaded audio file'}, status=status.HTTP_200_OK)

class ContestWordLoadViewset(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    def retrieve(self, request, pk=None):
        contest_word_instance = ContestGroup.objects.get(pk=pk)
        contest_word_serializer = ContestGroupDetailSerializer(contest_word_instance)
        for contest in contest_word_serializer.data['contests']:
            words = []
            word_contest_qset = WordContest.objects.filter(contest_id = contest['id'], status='new')
            for word_contest_instance in word_contest_qset:
                word_ids = json.loads(word_contest_instance.words)
                word_bank_qset = WordBank.objects.filter(id__in = word_ids)
                for word_bank_instance in word_bank_qset:
                    word_bank_serializer = WordBankListSerializer(word_bank_instance)
                    word_bank_serializer.data['spellbee_type'] = word_contest_instance.spellbee_type
                    word_bank_serializer.data['phase'] = word_contest_instance.phase
                    words.append(word_bank_serializer.data)
            contest['words'] = words
        result = {
            'ftp_details': json.loads(json.dumps(settings.NSF_FPT)),
            'contest_group':  contest_word_serializer.data
        }
        return Response(result)
    def partial_update(self, request, pk=None):
        WordContest.objects.filter(contest_id = pk).update(status = 'loaded')
        return JsonResponse({'type':'success', 'msg':'Loaded Successfully'} , safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def downloadWordS3Files(request):
    avl_excel_files = {'JSB':'JSB word list.csv', 'SSB':'SSB word list.csv'}
    frames = {}
    connect = AWSConnect()
    data = request.data
    spellbee_type = data.get('spellbee_type', None)
    phase = data.get('phase', None)
    current_excel_file=avl_excel_files[spellbee_type]
    excel_path = 'excel_files/' + current_excel_file 
    file = connect.getKey(excel_path).get('Body')
    df = pd.read_csv(io.StringIO(file.read().decode('utf-8')), delimiter=',')
    word_bank_qset = WordReview.objects.filter(
        word_bank__phase__istartswith = phase, 
        word_bank__spellbee_type = spellbee_type, 
        status = 'complete'
    )
    w_list = []
    for diff_level in ['Hard', 'Medium', 'Easy']:
        _w_list = [
            word for word in word_bank_qset.filter(
                word_bank__difficulty_level = diff_level
            ).values_list('word_bank__word', flat=True)
        ]
        random.shuffle(_w_list)
        _diff_count = data.get(diff_level.lower(), None)
        if _diff_count.isnumeric():
            _diff_count = int(_diff_count)
        else:
            _diff_count = len(_w_list)
        w_list += _w_list[:_diff_count]
    
    df = df[df['Word'].isin(w_list)]
    frames[spellbee_type] = df
    
    csv_buffer = io.BytesIO()
    with zipfile.ZipFile(csv_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as files_zip:
        files_zip.writestr(avl_excel_files[spellbee_type], frames[spellbee_type].to_csv(index=False) )

    response = HttpResponse(csv_buffer.getvalue(),content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=name.zip'

    return response
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def downloadWordFiles(request):
    data = request.data
    word_contest = WordContest.objects.get(id=data['id'])
    avl_excel_files = {'JSB':'JSB word list.csv', 'SSB':'SSB word list.csv'}
    destination_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/media/%s/' % word_contest.spellbee_type
    file_columns = (
        'file_name', 
        'file_name_origin', 
        'file_name_sentence',
        'file_name_complete',
        'file_name_definition'
    )
    word_is_list = []
    ftp_details = settings.NSF_FPT
    ftp = FTP()
    ftp.connect(ftp_details['server'], ftp_details['port'])
    ftp.login(ftp_details['username'], ftp_details['password'])
    word_is_list = word_is_list + json.loads(word_contest.words) 
    wordbank_qset = WordBank.objects.filter(id__in = word_is_list)
    serializer = WordBankDownloadSerializer(wordbank_qset, many=True)
    df = pd.DataFrame(serializer.data)
    df.columns = ['Word', 'POS', 'Pronunciation', 'Origin', 'Definitions', 'Sentence', 'Category', 'Difficulty Level']
    df.index.rename('S.No', inplace=True)
    
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as main_zip:
        main_zip.writestr('excel_files/'+avl_excel_files[word_contest.spellbee_type], df.to_csv() )
        for wb in wordbank_qset:
            for file_column in file_columns:
                file_buffer = io.BytesIO()
                file_path = getattr(wb,file_column,'')
                if file_path != '' and file_path != None:
                    first, second = file_path.split("/")[-1].split('_')
                    file_name = first.lower() + '_' + second.title() 
                    ftp.retrbinary('RETR %s' % file_path, file_buffer.write)
                    main_zip.writestr('audio_files/'+word_contest.spellbee_type+'/'+file_name, file_buffer.getvalue())
    response = HttpResponse(archive_buffer.getvalue(),content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=name.zip'
    return response
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def loadAndReviewWordsS3(request):
    connect = AWSConnect()
    avl_excel_files = {'JSB':'JSB word list.csv', 'SSB':'SSB word list.csv'}
    reload = request.data.get('reload', None)
    channel_layer = get_channel_layer()
    frames = []
    word_files = []
    message = {'status_msg': '', 'percentage': 0}
    
    def send_status(message):
        async_to_sync(channel_layer.group_send)(
            'event_notification',
            {
                'type': 'send_message_to_frontend',
                'message':json.dumps(message),
                'command': "load_review_status"
            }
        )
    if reload == False:
        message['status_msg'] = 'loaded and reviewed successfully'
        message['type'] = 'success'
        message['percentage'] = 100
        send_status(message)
        return JsonResponse({'type':'success', 'msg':'Loaded Successfully'} , safe=False)
    WordReview.objects.all().delete()
    WordBank.objects.all().delete()
    message['status_msg'] = 'getting files'
    send_status(message)
    for spellbee_type,current_excel_file in avl_excel_files.items():
        excel_path = 'excel_files/' + current_excel_file 
        file = connect.getKey(excel_path).get('Body')
        df = pd.read_csv(io.StringIO(file.read().decode('utf-8')), delimiter=',')
        df['Spellbee Type'] = spellbee_type
        frames.append(df)
        #loading all media keys
        source_path = 'audio_files/' + str(spellbee_type.lower()) + '/'
        # objs = list(connect.BUCKET.objects.filter(Prefix=source_path))
        for obj in list(connect.BUCKET.objects.filter(Prefix=source_path)):
            word_files.append(obj.key)
        message['percentage'] = 33.3/2
        send_status(message)
    df = pd.concat(frames, ignore_index=True)
    message['percentage'] = 33.3
    send_status(message)
    total_df_rows = len(df)
    #loading words
    for index, row in df.iterrows():
        message['status_msg'] = 'loading words {} of {}'.format(index, total_df_rows)
        message['percentage'] = 33.3 + ((index * 33.3)/total_df_rows)
        send_status(message)
        set_word = str(row['Word']).lower()
        if set_word == 'nan':
            continue
        word_path = 'audio_files/' + row['Spellbee Type'].lower() + '/'
        new_word = WordBank()
        new_word, created = WordBank.objects.get_or_create(
            spellbee_type=row['Spellbee Type'],
            word=row['Word'],
        )
        new_word.created_by = request.user.email
        new_word.year = '2020'
        new_word.pronunciation = row['Pronunciation']
        new_word.pos = row['POS']
        new_word.land_of_origin = row['Origin']
        new_word.additional_info = row['Definitions'] 
        new_word.sentence = row['Sentence']
        new_word.phase = row['Category']
        new_word.difficulty_level = row['Difficulty Level']
        new_word.file_name = word_path + set_word + '_Word.mp3'
        new_word.file_name_origin = word_path + set_word + '_Origin.mp3'
        new_word.file_name_sentence = word_path + set_word + '_Sentence.mp3'
        new_word.file_name_complete = word_path  + set_word + '_Complete.mp3'
        new_word.file_name_definition = word_path  + set_word + '_Definition.mp3'
        new_word.save()
        
    #reviewing words
    for index, row in df.iterrows():
        message['status_msg'] = 'reviewing words {} of {}'.format(index, total_df_rows)
        message['percentage'] = 66.6 + ((index * 33.3)/total_df_rows)
        send_status(message)
        set_word = str(row['Word']).lower()
        spellbee_type = row['Spellbee Type']
        audio_file_prefix = 'audio_files/' + str(spellbee_type.lower()) + '/' + set_word
        if set_word == 'nan':
            continue
        text_fields = [
            'word', 
            'pronunciation', 
            'pos', 
            'land_of_origin', 
            'additional_info', 
            'sentence',
            'spellbee_type',
            'phase',
            'year',
            'difficulty_level'
        ]
        audio_fields = {
            'file_name': '_Word.mp3',
            'file_name_origin': '_Origin.mp3',
            'file_name_sentence': '_Sentence.mp3',
            'file_name_complete': '_Complete.mp3',
            'file_name_definition': '_Definition.mp3'
        }
        word = WordBank.objects.get(
            spellbee_type=spellbee_type,
            word=row['Word'],
        )
        review_word, created = WordReview.objects.get_or_create(
            word_bank=word
        )
        review_word.created_by = request.user.email
        for text_field in text_fields:
            text_value = getattr(word,text_field,'')
            if text_value == '' or text_value == None:
                setattr(review_word, text_field, 'unavailable')
            else:
                setattr(review_word, text_field, 'available')
        
        for audio_field,audio_field_ext in audio_fields.items():
            audio_value = getattr(word,audio_field,'')
            audio_key = audio_file_prefix + audio_field_ext
            if audio_value == '' or audio_value == None or audio_key not in word_files:
                setattr(review_word, audio_field, 'unavailable')
            else:
                setattr(review_word, audio_field, 'available')
        review_word_fields = text_fields + list(audio_fields.keys())
        
        review_word_values = (
            lambda review_word,review_word_fields: [
                getattr(review_word,i,'') for i in review_word_fields
            ]
        )(review_word, review_word_fields)
        
        if 'unavailable' in review_word_values:
            review_word.status = 'incomplete'
        else:
             review_word.status = 'complete'
        review_word.save()
    message['status_msg'] = 'loaded and reviewed successfully'
    message['type'] = 'success'
    message['percentage'] = 100
    send_status(message)
    return JsonResponse({'type':'success', 'msg':'Loaded Successfully'} , safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getS3Volumes(request):
    keys = []
    result = AWSConnect().list_objects('/')
    for obj in result.get('CommonPrefixes'):
        keys.append(obj['Prefix'][:-1])
    
    return JsonResponse(keys , safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getVerifiedWords(request):
    words_qset = WordBank.objects.filter(word_bank__status='verified')
    serializer = WordBankListSerializer(words_qset, many=True)
    return JsonResponse(serializer.data , safe=False)

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def contestWords(request):
    def get_saved_ids(data):
        word_list = {
            'Hard': [],
            'Medium': [],
            'Easy': []
        }
        for difficulty_level in word_list.keys():
            word_contest_qset = WordContest.objects.filter(
                # word_group=data['word_group'],
                contest_id = data['contest'],
                spellbee_type=data['spellbee_type'], 
                phase=data['phase'],
                difficulty_level = difficulty_level
            )
            if word_contest_qset.count() > 0:
                word_list[difficulty_level] = json.loads(
                    word_contest_qset[0].words
                )
        return word_list
    
    if request.method == 'GET':
        word_list = []
        params = request.query_params
        word_contest_qset = WordContest.objects.filter(id = params['id'])
        if word_contest_qset.count() > 0:
            word_list = json.loads(word_contest_qset[0].words)
        return JsonResponse(word_list , safe=False)
    elif request.method == 'POST':
        data = request.data
        word_contest_instance = WordContest.objects.get(id = data['id'])
        word_contest_instance.words = json.dumps(data['words'])
        word_contest_instance.save()
        return JsonResponse(data['words'], safe=False)
    
    elif request.method == 'DELETE':
        WordContest.objects.all().delete()
        return JsonResponse({'type':'success', 'msg':'Deleted Successfully'} , safe=False)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def getWordGroups(request):
#     word_group = []
#     word_group_qset = WordContest.objects.filter(word_group__isnull=False).order_by('word_group').values_list('word_group', flat=True).distinct()
#     if word_group_qset.count() > 0:
#         word_group = list(word_group_qset)
#     return JsonResponse(word_group, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test(request):
    from django.db.models import Count, Case, When, Q
    # result = WordContest.objects.values('word_group').annotate(
    #     JSB=Count(Case(When(spellbee_type='JSB', then=1))), 
    #     SSB=Count(Case(When(spellbee_type='SSB', then=1))) 
    # )
    # result_new = WordContest.objects.values('word_group').annotate(
    #     JSB_PHASE1=Count('phase',filter=Q(spellbee_type='JSB', phase="Phase 1")),
    #     JSB_PHASE2=Count('phase',filter=Q(spellbee_type='JSB', phase="Phase 2")), 
    #     JSB_FINALS=Count('phase',filter=Q(spellbee_type='JSB', phase="FINALS")),
    #     SSB_PHASE1=Count('phase',filter=Q(spellbee_type='SSB', phase="Phase 1")),
    #     SSB_PHASE2=Count('phase',filter=Q(spellbee_type='SSB', phase="Phase 2")), 
    #     SSB_FINALS=Count('phase',filter=Q(spellbee_type='SSB', phase="FINALS")) 
    # )
    ContestGroup.objects.all().delete()
    Contest.objects.all().delete()
    WordContest.objects.all().delete()
    return JsonResponse({'type':'success', 'msg':[]} , safe=False)




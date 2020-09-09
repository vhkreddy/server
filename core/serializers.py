from rest_framework import serializers, fields
import pdb
from .models import WordBank, WordReview, ContestGroup, Contest, WordContest

class WordBankDownloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordBank
        fields = ['word','pos','pronunciation','land_of_origin','additional_info','sentence',
            'phase', 'difficulty_level'
        ]
        
class WordBankListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordBank
        fields = ['id', 'word','pronunciation','pos','land_of_origin','additional_info','sentence','spellbee_type',
            'phase','year','difficulty_level','file_name','file_name_origin','file_name_sentence','file_name_complete',
            'file_name_definition', 'lexicographical'
        ]

class WordReviewListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordReview
        fields = ['id', 'pronunciation', 'pos', 'land_of_origin' , 'sentence', 'spellbee_type', 'phase', 'year', 'difficulty_level', 
            'file_name', 'file_name_origin', 'file_name_sentence', 'file_name_complete', 'file_name_definition', 'status', 'word', 'additional_info',
            'file_name_remarks', 'file_name_origin_remarks', 'file_name_sentence_remarks', 'file_name_complete_remarks', 'file_name_definition_remarks',
            'comments', 'is_dirty', 'modified_on', 'modified_by'
        ]

class IssuesListSerializer(serializers.Serializer):
    def to_representation(self, instance):
        word_review_dict = WordReviewListSerializer(instance).data
        word_bank_dict = dict([('word_bank__' + k, v) for k, v in WordBankListSerializer(instance.word_bank).data.items()])
        word_review_dict.update(word_bank_dict)
        return word_review_dict
    class Meta:
        fields  = '__all__'
        
class ContestListSerializer(serializers.ModelSerializer):
    contest_group__name = serializers.CharField(read_only=True, source="contest_group.name")
    class Meta:
        model = Contest
        fields  = ['id', 'contest_name', 'contest_group_id','contest_group__name', 'contest_date']

class ContestGroupDetailSerializer(serializers.ModelSerializer):
    contests = serializers.SerializerMethodField(read_only=True)
    def get_contests(self, obj):
        if obj is not None:
            serializer = ContestListSerializer(obj.contest.all(), many=True)
            return serializer.data
        else:
            return None
    class Meta:
        model = ContestGroup
        fields = ['id', 'name', 'type', 'created_on', 'contests']
        depth = 1
        
class WordContestListSerializer(serializers.Serializer):
    JSB_PHASE1 = serializers.CharField(max_length=200)
    JSB_PHASE2 = serializers.CharField(max_length=200)
    JSB_FINALS = serializers.CharField(max_length=200)
    SSB_PHASE1 = serializers.CharField(max_length=200)
    SSB_PHASE2 = serializers.CharField(max_length=200)
    SSB_FINALS = serializers.CharField(max_length=200)
    
    class Meta:
        fields  = '__all__'


class ContestWordListSerializer(serializers.ModelSerializer):
    contest__contest_group__type = serializers.CharField(source="contest.contest_group.type")
    contest__contest_group__name = serializers.CharField(source="contest.contest_group.name", required=False)
    contest__contest_group__country = serializers.CharField(source="contest.contest_group.country")
    contest__contest_group_id = serializers.CharField(source="contest.contest_group_id", read_only=True)
    contest__contest_name = serializers.CharField(source="contest.contest_name")
    contest__contest_date = serializers.CharField(source="contest.contest_date")
    
    def validate_create_update(self, method, validated_data, instance=None):
        if validated_data['contest']['contest_group']['country'] == 'US':
            return
        wc_instance = WordContest.objects.filter(
            contest__contest_group__name = validated_data['contest']['contest_group']['name'],
            contest__contest_group__type = validated_data['contest']['contest_group']['type'],
            contest__contest_group__country = validated_data['contest']['contest_group']['country'],
            contest__contest_name = validated_data['contest']['contest_name'],
            spellbee_type = validated_data['spellbee_type'],
            phase = validated_data['phase']
        )
        # pdb.set_trace()
        if method == 'create' and wc_instance.count() > 0:
            raise serializers.ValidationError("contest already exists")
        elif method == 'update' and wc_instance.count() > 0 and  wc_instance[0].id != instance.id:
            raise serializers.ValidationError("contest already exists")
        
    def create(self, validated_data):
        self.validate_create_update('create', validated_data)
        contest = validated_data.pop('contest')
        contest_group = contest.pop('contest_group')
        contest_group_instance, contest_group_created = ContestGroup.objects.get_or_create(**contest_group)
        contest_instance, created = contest_group_instance.contest.get_or_create(**contest, contest_group_id = contest_group_instance.id)
        word_contest_instance, created = contest_instance.word_contest.get_or_create(**validated_data, contest_id = contest_instance.id)
        return word_contest_instance
    
    def update(self, instance, validated_data):
        # pdb.set_trace()
        self.validate_create_update('update', validated_data, instance)
        for word_item in validated_data.items():
            if word_item[0] == 'contest':
                contest_group = word_item[1].pop('contest_group')
                contest_group_instance, contest_group_created = ContestGroup.objects.get_or_create(**contest_group)
                contest_instance, contest_created = Contest.objects.get_or_create(**word_item[1], contest_group_id = contest_group_instance.id)
                # contest_instance.contest_group = contest_group_instance
                contest_instance.save()
                instance.contest = contest_instance
                instance.save()
            else:
                setattr(instance, word_item[0], word_item[1])
        instance.save()
        ContestGroup.objects.filter(contest__isnull=True).delete()
        Contest.objects.filter(word_contest__isnull=True).delete()
        return instance
    
    class Meta:
        model = WordContest
        fields = ['id', 'words', 'spellbee_type', 'phase', 'contest', 'contest__contest_name', 'contest__contest_date', 'contest__contest_group_id', 'contest__contest_group__country', 'contest__contest_group__name', 'contest__contest_group__type']
        read_only_fields = ('contest',)



        
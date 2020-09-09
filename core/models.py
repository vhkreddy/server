import uuid
from django.db import models
# from django.contrib.postgres.fields import ArrayField


class ContestGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CONTEST_TYPE = (
        ('Prelims', 'Prelims'),
        ('Finals', 'Finals')
    )
    COUNTRY_TYPE = (
        ('India', 'India'),
        ('US', 'US')
    )
    name = models.TextField(help_text='contest group name')
    type = models.CharField(help_text='contest type',
                            choices=CONTEST_TYPE, max_length=100)
    country = models.CharField(help_text='country type',
                            choices=COUNTRY_TYPE, max_length=100)
    # audit data
    created_by = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "contest_group"


class Contest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contest_name = models.CharField(max_length=100)
    contest_group = models.ForeignKey(ContestGroup, on_delete=models.CASCADE, null=True, blank=True, related_name='contest')
    contest_date = models.DateField(null=True,blank=True)
    
    # audit data
    created_by = models.CharField(max_length=100,blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "contest"

class WordBank(models.Model):
    SPELL_BEE_CHOICES = (
        ('JSB','JSB'),
        ('SSB','SSB')
        )
    PHASE_CHOICES = (
        ('Phase 1','Phase 1'),
        ('Phase 2','Phase 2')
        )
    DIFFICULTY_CHOICES = (
        ('Easy','Easy'),
        ('Medium','Medium'),
        ('Hard','Hard')
        )
   
    lexicographical = models.CharField(max_length=1,null=True,blank=True)
    
    # text info
    word = models.CharField(max_length=100)
    pronunciation = models.CharField(max_length=100)
    pos = models.CharField(max_length=100)
    land_of_origin = models.CharField(max_length=100)
    additional_info = models.CharField(max_length=3000)
    sentence = models.CharField(max_length=3000,null=True,blank=True)
    spellbee_type = models.CharField(max_length=100,choices=SPELL_BEE_CHOICES)
    phase = models.CharField(max_length=100,choices=PHASE_CHOICES)
    year = models.CharField(max_length=100)
    difficulty_level = models.CharField(max_length=100,choices=DIFFICULTY_CHOICES,default='Easy')
    
    # audio info
    file_name = models.CharField(max_length=100)
    file_name_origin = models.CharField(max_length=100,blank=True,null=True)
    file_name_sentence = models.CharField(max_length=100,blank=True,null=True)
    file_name_complete = models.CharField(max_length=100,blank=True,null=True)
    file_name_definition = models.CharField(max_length=100,blank=True,null=True)
    
    # audit data
    created_by = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'word_bank'

class WordReview(models.Model):
    TEXT_CHOICES = (
        ('available','available'),
        ('unavailable','unavailable')
        )
    AUDIO_CHOICES = (
        ('available','available'),
        ('unavailable','unavailable'),
        ('incomplete','incomplete'),
        ('low_voice','low_voice'),
        ('noise','noise'),
        ('not_clear','not_clear'),
        ('not_playing','not_playing'),
        ('repeating','repeating'),
        )
    STATUS_CHOICES = (
        ('deleted','deleted'),
        ('incomplete','incomplete'),
        ('verified','verified'),
        ('open','open')
        )
    word_bank = models.ForeignKey(WordBank, on_delete=models.CASCADE,null=True,blank=True , related_name='word_bank')

    # text info
    word = models.CharField(max_length=100, choices=TEXT_CHOICES, default='unavailable')
    pronunciation = models.CharField(max_length=100, choices=TEXT_CHOICES, default='unavailable')
    pos = models.CharField(max_length=100, choices=TEXT_CHOICES, default='unavailable')
    land_of_origin = models.CharField(max_length=100, choices=TEXT_CHOICES, default='unavailable')
    additional_info = models.CharField(max_length=100, choices=TEXT_CHOICES, default='unavailable')
    sentence = models.CharField(max_length=100, choices=TEXT_CHOICES, default='unavailable')
    spellbee_type = models.CharField(max_length=100, choices=TEXT_CHOICES, default='unavailable')
    phase = models.CharField(max_length=100, choices=TEXT_CHOICES, default='unavailable')
    year = models.CharField(max_length=100, choices=TEXT_CHOICES, default='unavailable')
    difficulty_level = models.CharField(max_length=100, choices=TEXT_CHOICES, default='unavailable')

    # audio info
    file_name = models.CharField(max_length=100, choices=AUDIO_CHOICES, default='unavailable')
    file_name_origin = models.CharField(max_length=100, choices=AUDIO_CHOICES, default='unavailable')
    file_name_sentence = models.CharField(max_length=100, choices=AUDIO_CHOICES, default='unavailable')
    file_name_complete = models.CharField(max_length=100, choices=AUDIO_CHOICES, default='unavailable')
    file_name_definition = models.CharField(max_length=100, choices=AUDIO_CHOICES, default='unavailable')
    
    # audio files remarks
    file_name_remarks = models.TextField(blank = True)
    file_name_origin_remarks = models.TextField(blank = True)
    file_name_sentence_remarks = models.TextField(blank = True)
    file_name_complete_remarks = models.TextField(blank = True)
    file_name_definition_remarks = models.TextField(blank = True)
    
    # word status info
    comments = models.TextField(blank = True)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='open')
    is_dirty = models.BooleanField(default=False)
    
    # audit data
    modified_by = models.CharField(max_length=100, default="")
    modified_on = models.DateField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'word_review'

class WordContest(models.Model):
    STATUS_TYPE = (
        ('new', 'new'),
        ('loaded', 'loaded')
    )
    SPELL_BEE_CHOICES = (
        ('JSB','JSB'),
        ('SSB','SSB')
        )
    PHASE_CHOICES = (
        ('Phase 1','Phase 1'),
        ('Phase 2','Phase 2'),
        ('Finals', 'Finals')
        )
    status = models.CharField(default='new', choices=STATUS_TYPE, max_length=100, help_text='contest status')
    words = models.TextField(default="[]")
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE,null=True,blank=True , related_name='word_contest')
    spellbee_type = models.CharField(max_length=100,choices=SPELL_BEE_CHOICES)
    phase = models.CharField(max_length=100,choices=PHASE_CHOICES)
    
     # audit data
    created_by = models.CharField(max_length=100,blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'word_contest'



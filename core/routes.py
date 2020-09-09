from django.urls import path, include
from django.conf.urls import url
from rest_framework.routers import DefaultRouter


from .viewsets import  getS3Volumes, loadAndReviewWords, IssuesViewset, UserViewset, downloadWordFiles, getVerifiedWords, contestWords, ContestViewset, ContestGroupViewset, ContestWordViewset, ContestWordLoadViewset, test #, WordContestViewset, getWordGroups

router = DefaultRouter()
router.register(r'issues', IssuesViewset)
router.register(r'users', UserViewset)
router.register(r'contests', ContestViewset)
router.register(r'contest_groups', ContestGroupViewset)
router.register(r'contest_group_words', ContestWordViewset)
router.register(r'contest_word_load', ContestWordLoadViewset, basename='contest_word_load')
# router.register(r'word_contests', WordContestViewset)

urlpatterns = [
    path('', include(router.urls)),
    url(r'^volumes/', getS3Volumes, name="Volumes"),
    url(r'^download_word_files/', downloadWordFiles, name="download_word_files"),
    url(r'^load_and_review_words/',loadAndReviewWords, name="LoadAndReviewWords"),
    url(r'^get_verified_words/',getVerifiedWords, name="getVerifiedWords"),
    url(r'^contest_words/',contestWords, name="contestWords"),
    # url(r'^get_word_groups/',getWordGroups, name="get_word_groups"),
    url(r'^test/',test, name="test"),
]

from django import newforms as forms
from django.contrib.auth.models import User
from django.newforms import ValidationError
import defaults
from models import *

class NewTopic(forms.Form):
    "Create a new topic."
    topic_name = forms.CharField(max_length = 100)
    topic_fullname = forms.CharField(max_length = 100)
    
    about = forms.CharField(widget = forms.Textarea)
    
    def __init__(self, user, topic_name=None, *args, **kwargs):
        super(NewTopic, self).__init__(*args, **kwargs)
        self.user = user
        if topic_name:
            self.fields['topic_name'].initial = topic_name
    
    def clean_topic_name(self):
        try:
            name = self.cleaned_data['topic_name']
            Topic.objects.get(name = name)
        except Topic.DoesNotExist, e:
            return name
        raise ValidationError('The name %s is already taken. Try something else?' % name)
    
    def clean(self):
        if self.user.get_profile().karma < defaults.KARMA_COST_NEW_TOPIC:
            raise ValidationError('You do not have enogh karma')
        return self.cleaned_data
    
    def save(self):
        return Topic.objects.create_new_topic(user = self.user, full_name=self.cleaned_data['topic_fullname'], topic_name=self.cleaned_data['topic_name'], about = self.cleaned_data['about'])
    
class NewLink(forms.Form):
    url = forms.URLField()
    text = forms.CharField(widget = forms.Textarea)
    
    def __init__(self, topic, user, *args, **kwargs):
        super(NewLink, self).__init__(*args, **kwargs)
        self.user = user
        self.topic = topic
        
    def clean_url(self):
        try:
            Link.objects.get(topic = self.topic, url = self.cleaned_data['url'])
        except Link.DoesNotExist, e:
            return self.cleaned_data['url']
        raise ValidationError('This link has already been submitted.')
    
    def clean(self):
        if self.user.get_profile().karma < defaults.KARMA_COST_NEW_LINK:
            raise ValidationError('You do not have enogh karma')
        return self.cleaned_data
    
    def save(self):
        return Link.objects.create_link(url = self.cleaned_data['url'], text = self.cleaned_data['text'], user = self.user, topic = self.topic)
    
class DoComment(forms.Form):
    text = forms.CharField(widget = forms.Textarea)
    
    def __init__(self, user, link, *args, **kwargs):
        super(DoComment, self).__init__(*args, **kwargs)
        self.user = user
        self.link = link
        
    def save(self):
        return Comment.objects.create_comment(link = self.link, user = self.user, comment_text = self.cleaned_data['text'])
    
class DoThreadedComment(forms.Form):
    text = forms.CharField(widget = forms.Textarea)
    parent_id = forms.CharField(widget = forms.HiddenInput)
    
    def __init__(self, user, link, parent, *args, **kwargs):
        super(DoThreadedComment, self).__init__( *args, **kwargs)
        self.user = user
        self.link = link
        self.parent = parent
        self.fields['parent_id'].initial = parent.id
    
    def save(self):
        return Comment.objects.create_comment(link = self.link, user = self.user, comment_text = self.cleaned_data['text'], parent = self.parent)
    
class AddTag(forms.Form):
    tag = forms.CharField(max_length = 100)
    
    def __init__(self, user, link, *args, **kwargs):
        super(AddTag, self).__init__(*args, **kwargs)
        self.user = user
        self.link = link
        
    def save(self):
        return LinkTagUser.objects.tag_link(tag_text = self.cleaned_data['tag'], link = self.link, user=self.user)


from django.newforms import widgets
from django.contrib.auth.models import User    
class LoginForm(forms.Form):
    """Login form for users."""
    username = forms.RegexField(r'^[a-zA-Z0-9_]{1,30}$',
                                max_length = 30,
                                min_length = 1,
                                widget = widgets.TextInput(attrs={'class':'input'}),
                                error_message = 'Must be 1-30 alphanumeric characters or underscores.')
    password = forms.CharField(min_length = 1, 
                               max_length = 128, 
                               widget = widgets.PasswordInput(attrs={'class':'input'}),
                               label = 'Password')
    remember_user = forms.BooleanField(required = False, 
                                       label = 'Remember Me')
    
    def clean(self):
        try:
            user = User.objects.get(username__iexact = self.cleaned_data['username'])
        except User.DoesNotExist, KeyError:
            raise forms.ValidationError('Invalid username, please try again.')
        
        if not user.check_password(self.cleaned_data['password']):
            raise forms.ValidationError('Invalid password, please try again.')
        
        return self.cleaned_data
                
    
        
        
        
        
        
        
        
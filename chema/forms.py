from django import forms
from .models import *
import os
from django.contrib.auth.models import User
from PIL import Image
from django.conf import settings
from user.models import Profile


class AddMemberForm(forms.Form):
    member = forms.ModelChoiceField(queryset=Profile.objects.all(), label='Select New Member')


class GroupJoinForm(forms.Form):
    group = forms.ModelChoiceField(queryset=Group.objects.all(),label='Select Group', empty_label='Select a Member')
    

class GroupCreationForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'cover_image', 'is_active']
        # You can customize widgets or add any additional fields as needed
       
        widgets={
            'description': forms.Textarea(attrs={
                'class': 'form-control ',
                'rows': 4,
            }),
            'cover_image': forms.HiddenInput()
        }
        
    def __init__(self, *args, **kwargs):
        super(GroupCreationForm, self).__init__(*args, **kwargs)
        # You can customize form fields or add validation as needed.
    
    
class PostCreationForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']
        widgets={
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                 'rows': 5,
            }),
        }
        
        

class EditPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
            }),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets={
            'content': forms.Textarea(attrs={
                'class': 'form-control form-control-md',
                'rows': 4,
            }),
        } 

class CommentEditForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets={
            'content': forms.Textarea(attrs={
                'class': 'form-control form-control-md',
                'rows': 4,
            }),
        } 
        


class DependentForm(forms.ModelForm):
    class Meta:
        model = Dependent
        fields = ['name', 'date_of_birth', 'relationship'] 
        widgets={
             'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control form-control-md',
                 'style': ' width: 160px;',
                 'type': 'date',
              }),
        }
       
       
class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['content']
        widgets={
            'content': forms.Textarea(attrs={
                'class': 'form-control form-control-md',
               'rows': 4,
            }),
        }
        
        
class EditReplyForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']
        widgets={
            'content': forms.Textarea(attrs={
                'class': 'form-control form-control-md',
                'rows': 4,
            }),
        }


class SearchForm(forms.Form):
    query = forms.CharField(max_length=100, required=True)

    widgets={
            'query': forms.Textarea(attrs={
                'class': 'form-control form-control-md',
                'placeholder':'search',
                
            }),
        }  



class AddAdminForm(forms.Form):
    member = forms.ModelChoiceField(queryset=Profile.objects.filter(groups__is_active=True), label='Select New Member')


    # def __init__(self, *args, **kwargs):
    #     group_id = kwargs.pop('group_id')
    #     super().__init__(*args, **kwargs)
    #     group = Group.objects.get(id=group_id)
    #     self.fields['member'].queryset = group.members.all()

 

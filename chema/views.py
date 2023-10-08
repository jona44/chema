from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import *
from django.urls import reverse 
from django.forms import inlineformset_factory
from django.contrib import messages
import os
from user.models import Profile
import random
from .forms import *



@login_required
def home(request):
    profile = Profile.objects.get(user=request.user)  # Retrieve the profile associated with the user
    groups = Group.objects.filter(members=profile)
    search_form = SearchForm()
    grouped_data = []
    active_group = Group.objects.filter(is_active=True).first()
    
    if active_group is None:
    # Handle the case where there are no active groups
<<<<<<< Updated upstream
        return render(request, 'chema/home.html')
=======
        return render(request, 'chema/create_group.html')
>>>>>>> Stashed changes
    
    # Fetch only the posts of the active group
    active_group_posts = Post.objects.filter(group=active_group).order_by('-created_at')

    # Fetch comments for the posts in the active group
    active_group_comments = Comment.objects.filter(post__in=active_group_posts).order_by('-created_at')

    group_data = {
        'group': active_group,
        'minimized': not (active_group_posts.exists() or active_group_comments.exists()),
        'posts': active_group_posts[:5],  # Limit the number of posts to display initially
        'comments': active_group_comments,  # Comments for the active group's posts
    }

    if active_group.admins_as_members.exists():
        group_data['admins_as_members'] = active_group.admins_as_members.all()
    else:
        group_data['admins_as_members'] = []

    for comment in group_data['comments']:
        comment.replies.set(Reply.objects.filter(comment=comment).order_by('-created_at')[:3])

    return render(request, 'chema/home.html', {
        'grouped_data': [group_data],  # Only the active group data
        'groups': groups,
        'search_form': search_form,
        'active_group': active_group,
        'active_group_posts': active_group_posts,
        'active_group_comments': active_group_comments
    })


@login_required
def choice(request):
    pass
    return render(request, 'chema/choice.html')


@login_required
def join_existing_group(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = GroupJoinForm(request.POST)
        if form.is_valid():
            group_id = form.cleaned_data['group'].id
            group = get_object_or_404(Group, id=group_id)
            group.members.add(request.user.profile)
            return redirect('group_detail_view', group_id=group.id)
    else:
        form = GroupJoinForm()

    return render(request, 'chema/join_existing_group.html', {'form': form})

@login_required

@login_required
def create_group(request):
    if request.method == 'POST':
        form = CreateGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.admin = Admin.objects.create(profile=request.user.profile)
            group.save()
            group.admins_as_members.add(request.user.profile)
            return redirect('group_detail_view', group_id=group.id)
    else:
        form = CreateGroupForm()

    context = {
        'form': form,
    }

    return render(request, 'chema/create_group.html', {'form': form})


@login_required
def createPost(request, group_id):
      # Retrieve the active group based on the group_id
    try:
        group = Group.objects.get(id=group_id, is_active=True)
    except Group.DoesNotExist:
        messages.error(request, "The group does not exist or is not active.")
        return redirect('your_redirect_url') 
    
    # Check if the user is a member of the group
    if request.user.profile not in group.members.all():
        messages.error(request, "You are not a member of this group.")
        return redirect('home') 

    if request.method == 'POST':
        # Process the form submission
        form = PostCreationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a new post
            post = form.save(commit=False)
            post.author = request.user.profile
            post.group = group
            post.save()
            messages.success(request, "Post created successfully!")
            return redirect('home') 
        else:
            messages.error(request, "Error creating the post. Please check your input.")
    else:
        # Display a blank form for creating a post
        form = PostCreationForm()

    return render(request, 'chema/createPost.html', {'form': form, 'group': group})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = EditPostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('home')  # Redirect to the home page after editing the post
    else:
        form = EditPostForm(instance=post)

    return render(request, 'chema/edit_post.html', {'form': form, 'post': post})




@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user.profile:
        # If the current user is not the author of the post, they are not allowed to delete it
        return redirect('home')

    if request.method == 'POST':
        post.delete()
        return redirect('home')  # Redirect to home page or any other appropriate page after post deletion

    return render(request, 'chema/delete_post.html', {'post': post})


@login_required
def create_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user.profile
            comment.post = post
            comment.save()
            return redirect('home')
    else:
        form = CommentForm()

    return render(request, 'chema/create_comment.html', {'form': form, 'post': post})


@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user.profile:
        # If the current user is not the author of the comment, they are not allowed to edit it
        return redirect('home')

    if request.method == 'POST':
        form = CommentEditForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = CommentEditForm(instance=comment)

    return render(request, 'chema/edit_comment.html', {'form': form, 'comment': comment})



@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user.profile:
        # If the current user is not the author of the comment, they are not allowed to delete it
        return redirect('post_detail', post_id=comment.post.id)

    if request.method == 'POST':
        comment.delete()
        return redirect('post_detail', post_id=comment.post.id)

    return render(request, 'chema/delete_comment.html', {'comment': comment})


@login_required
def add_member(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    # Get the logged-in user

    if request.method == 'POST':
        form = AddMemberForm(request.POST)
        if form.is_valid():
            member_profile = form.cleaned_data['member']
            # Check if the new_member is the logged-in user and not already a member
            if member_profile not in group.members.all():
                group.members.add(member_profile)
                return redirect('home')
    else:
        form = AddMemberForm()

    return render(request, 'chema/add_member.html', {'form': form, 'group': group})


@login_required
def approve_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Check if the user is the group admin
    if request.user == post.group.admin:
        post.approved = True
        post.save()
    
    return redirect('home')


@login_required
def add_dependents(request):
    DependentFormSet = inlineformset_factory(Profile, Dependent, form=DependentForm, extra=2,can_delete = False) # Set the number of empty forms

    user = request.user.profile
    formset = DependentFormSet(instance=user)

    if request.method == 'POST':
        formset = DependentFormSet(request.POST, instance=user)
        if formset.is_valid():
            # Iterate over the forms and set can_delete to False
            
            formset.save()
            
             # Getting the names of the added dependents
            added_dependents_names = ', '.join([form.cleaned_data.get('name') for form in formset.forms if form.cleaned_data.get('name')])

            # Adding a success message with the names of the added dependents
            success_message = f"Successfully added dependents: {added_dependents_names}"
            messages.success(request, success_message)
            return redirect('home')  # Redirect to the user's home page

    return render(request, 'chema/add_dependents.html', {'formset': formset})



@login_required
def user_groups(request):
    profile = Profile.objects.get(user=request.user)
    groups = Group.objects.filter(members=profile)
    return render(request, 'chema/user_groups.html', {'groups': groups})


@login_required
def add_reply(request, comment_id):
    comment= get_object_or_404(Comment, id=comment_id)

    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            new_reply = form.save(commit=False)
            new_reply.author = request.user.profile
            new_reply.comment = comment
            new_reply.save()
            return redirect('home')
    else:
        form = ReplyForm()

    return render(request, 'chema/add_reply.html', {'form': form, 'comment': comment})


@login_required
def remove_reply(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)
    comment = reply.comment
    if request.user.profile == reply.author:
        reply.delete()
    return redirect('groupDetail', group_id=comment.post.group.id)


@login_required
def edit_reply(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)

    if request.method == 'POST':
        form = EditReplyForm(request.POST, instance=reply)
        if form.is_valid():
            form.save()
            return redirect('groupDetail', group_id=reply.comment.post.group.id)
    else:
        form = EditReplyForm(instance=reply)

    return render(request, 'chema/edit_reply.html', {'form': form, 'reply': reply})



@login_required
def member_detail(request, pk):
    # Get the user object or raise a 404 error
    user = get_object_or_404(User, pk=pk)
    
    # Get the user's profile
    profile = Profile.objects.get(user=user)
    
    # Get the groups that the user belongs to
    groups = Group.objects.filter(members=profile)
    
    # Get the dependents of the user
    dependents = Dependent.objects.filter(guardian=profile)
    
    # Render the template with the context data
    return render(request, 'chema/member_detail.html', {
        'member': user,
        'profile': profile,
        'groups': groups,
        'dependents': dependents,
    })


from django.db.models import Q

def search_view(request):
    query = request.GET.get('q', '')
    # Perform a search for both groups and members using Q objects
    results = (
        list(Group.objects.filter(Q(name__icontains=query) | Q(members__user__username__icontains=query)).values()) +
        list(Profile.objects.filter(user__username__icontains=query).values())
    )
    return JsonResponse({'results': results})


def join_group(request, group_id):
    # Get the group object
    group = get_object_or_404(Group, id=group_id)
    # Add the current user to the group's members
    if request.user not in group.members.all():
        group.members.add(request.user.profile)
    # Redirect to the group's detail page or any other appropriate page
    return redirect('group_detail_view', group_id)


def group_detail_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    members_count = group.members.count()
    admins_count = group.admins_as_members.count()
    
    return render(request, 'chema/group_detail_view.html', {'group': group,'members_count':members_count,'admins_count':admins_count})



@login_required
def add_admin(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        form = AddAdminForm(request.POST, group_id=group.id)
        if form.is_valid():
            user = form.cleaned_data['member']
            if request.user.profile in group.admins_as_members.all() and user in group.members.all():
                group.admins_as_members.add(user)
                return redirect('group_detail_view', group_id=group.id)
            else:
                # handle error case here
                pass
    else:
        form = AddAdminForm(group_id=group.id)
    return render(request, 'chema/add_admin.html', {'form': form})




def toggle_group(request, group_id):
    # Get the group being toggled
    group_to_toggle = get_object_or_404(Group, id=group_id)
    
    # Toggle the group by setting it to active
    group_to_toggle.is_active = True
    group_to_toggle.save()

    # Deactivate all other groups
    Group.objects.exclude(id=group_id).update(is_active=False)

    return redirect('home')

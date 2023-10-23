from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse,HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from .models import *
from django.urls import reverse 
from django.forms import inlineformset_factory
from django.contrib import messages
import os
from user.models import Profile
import random
from .forms import *
from django.core.exceptions import PermissionDenied



@login_required
def home(request):
    user = request.user.profile
    groups = Group.objects.filter(members=request.user.profile)
    search_form = SearchForm()
   

    grouped_data = []

    # Get the active group, if it exists
    active_group = Group.objects.filter(is_active=True).first()

    if active_group is None:
        # Handle the case where there are no active groups
        return render(request, 'chema/home.html')

    # Fetch only the posts of the active group
    active_group_posts = Post.objects.filter(group=active_group).order_by('-created_at')

    # Fetch comments for the posts in the active group
    active_group_comments = Comment.objects.filter(post__in=active_group_posts).order_by('-created_at')

    group_data = {
        
        'group': active_group,
        'minimized': not (active_group_posts.exists() or active_group_comments.exists()),
        'posts': active_group_posts[:5],  # Limit the number of posts to display initially
        'comments': active_group_comments,  # Comments for active group's posts
        'admins_as_members': active_group.get_admins(),  # Use the new method to get admins
    }

    for comment in group_data['comments']:
        comment.replies.set(Reply.objects.filter(comment=comment).order_by('-created_at')[:3])

    return render(request, 'chema/home.html', {
        'grouped_data': [group_data],  # Only the active group data
        'groups': groups,
        'search_form': search_form,
        'active_group': active_group,
        'active_group_posts': active_group_posts,
        'active_group_comments': active_group_comments,
        
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

            if group.members.filter(id=profile.id).exists():
                # Handle this case as needed
                pass
            else:
                group.members.add(profile)
                return redirect('group_detail_view', group_id=group.id)

    else:
        form = GroupJoinForm()

    return render(request, 'chema/join_existing_group.html', {'form': form})


def join_active_group(request):
    # Assuming there is only one active group, retrieve it
    active_group = Group.objects.filter(is_active=True).first()

    if active_group:
        # Check if the user is already a member of the group
        is_member = GroupMembership.objects.filter(member=request.user.profile, group=active_group).exists()

        if not is_member:
            # If the user is not already a member, create a new GroupMembership
            membership = GroupMembership(member=request.user.profile, group=active_group)
            membership.save()
            messages.success(request, f"You have joined the '{active_group.name}' group.")
        else:
            messages.warning(request, f"You are already a member of the '{active_group.name}' group.")
    else:
        messages.error(request, "No active group found to join.")

    return redirect('group_detail_view', group_id=active_group.id)
 # Redirect to the group detail page or an appropriate URL


@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupCreationForm(request.POST)
        if form.is_valid():
            # Create the group detail using the form data
            group = form.save(commit=False)

            # Assuming the group is active upon creation
            group.is_active = True

            # Set the admin of the group to the current user's profile
            group.admin = request.user.profile
            group.save()

            # Create a GroupMembership instance for the current user
            member_instance = GroupMembership(member=request.user.profile, group=group, is_admin=True)
            member_instance.save()

            # Redirect to the group detail view or any other page
            return redirect('group_detail_view', group_id=group.id)
    else:
        form = GroupCreationForm()

    context = {
        'form': form,
    }

    return render(request, 'chema/create_group.html', context)


@login_required
def create_post(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # Check if the user is a member of the group
    if not group.members.filter(id=request.user.profile.id).exists():
        messages.error(request, "You are not a member of this group.")
        return redirect('home')

    if request.method == 'POST':
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
        form = PostCreationForm()

    context = {
        'group': group,
        'form': form,
    }

    return render(request, 'chema/create_post.html', context)


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
    print( post_id)
    # Retrieve the post based on the post_id
    post = get_object_or_404(Post, id=post_id, approved=True)

    if request.method == 'POST':
        # Process the form submission
        form = CommentForm(request.POST)
        if form.is_valid():
            # Create a new comment
            comment = form.save(commit=False)
            comment.author = request.user.profile
            comment.post = post
            comment.save()
            messages.success(request, "Comment created successfully!")
            return redirect('home')
        else:
            messages.error(request, "Error creating the comment. Please check your input.")
    else:
        # Display a blank form for creating a comment
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
    # Get the group
    group = get_object_or_404(Group, id=group_id)

    # Check if the current user is a member of the group
    if request.user.profile not in group.members.all():
        raise Http404("You are not a member of this group.")

    if request.method == 'POST':
        form = AddMemberForm(request.POST)
        if form.is_valid():
            member_profile = form.cleaned_data['member']
            # Check if the new member is not already a member of the group
            if member_profile not in group.members.all():
                GroupMembership.objects.create(member=member_profile, group=group)
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



def group_detail_view(request, group_id):
    group = get_object_or_404(Group, pk=group_id)

    # Use the reverse relationship to get the admin members
    group_admins = group.members.filter(groupmembership__is_admin=True)

    context = {
        'group': group,
        'group_admins': group_admins,
        'members': group.members.all(),  # All members of the group
        'count_members': group.members.count(),
        'count_admins': group_admins.count(),
    }

    return render(request, 'chema/group_detail_view.html', context)


from django.db.models import Q

def search_view(request):
    query = request.GET.get('q', '')
    
    # Perform a search for both groups and members using Q objects
    results = (
        list(Group.objects.filter(Q(name__icontains=query) | Q(members__user__username__icontains=query)).values()) +
        list(Profile.objects.filter(user__username__icontains=query).values())
    )
    
    return JsonResponse({'results': results})


# def member_detail(request, group_id, member_id):  
#     group = get_object_or_404(Group, id=group_id)
#     member = get_object_or_404(Profile, id=member_id)
#     groups = member.groups.all()
#     bio = member.bio
#     phone = member.phone
#     dependents = member.dependent_set.all()

#     # Fetch the group details for each group the member belongs to
#     group_details = []
#     for group in groups:
#         group_details.append({
#             'name': group.name,
#             # 'dependent': profile.dependent,
#             # 'deceased': group.deceased,
#             'is_active': group.is_active,
#             'description': group.description,
#             'date': group.date,
#         })

#     context = {
#         'object': member,
#         'groups': groups,
#         'bio': bio,
#         'phone': phone,
#         'dependents': dependents,
#         'group': group,
#         'member': member,
#     }

#     return render(request, 'chema/member_detail.html', context)




def member_detail(request, group_id, member_id):
    group = get_object_or_404(Group, id=group_id)
    member = get_object_or_404(Profile, id=member_id)
    groups = member.groups.all()
    bio = member.bio
    phone = member.phone
    dependents = member.dependent_set.all()
   

    # Fetch the group details for each group the member belongs to
    group_details = []
    for group in groups:
        group_details.append({
            'name': group.name,
            'is_active': group.is_active,
            'description': group.description,
            'date': group.date,
        })

    context = {
        'object': member,
        'groups': groups,
        'bio': bio,
        'phone': phone,
        'dependents': dependents,
        'group': group,
        'member': member,
         
    }

    # Check if the current user is a group admin for the specific group
    try:
        group_membership = GroupMembership.objects.get(group=group, member=request.user.profile)
        if not group_membership.is_admin:
            raise Http404("You are not a group admin.")
    except GroupMembership.DoesNotExist:
        raise Http404("You are not a group member.")

    if request.method == 'POST' and 'mark_member_as_deceased' in request.POST:
        # Handle marking the member as deceased here
        member.deceased = True  # Assuming you have a 'deceased' field in your Profile model
        member.save()

        # You can add a success message or redirect as needed
        return HttpResponse(request, 'chema/member_detail.html')

    return render(request, 'chema/member_detail.html', context)





@login_required
def add_admin(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    
    # Check if the user is an admin of the group
    if not group.admin == request.user.profile:
        return render(request, 'error.html')  # Handle the case where the user is not an admin

    if request.method == 'POST':
        form = AddAdminForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['member']

            # Check if the selected user is a member of the group
            if user in group.members.all():
                # Check if the user is already an admin
                if not group.groupmembership_set.filter(member=user, is_admin=True).exists():
                    # If not an admin, make the user an admin
                    group_membership = group.groupmembership_set.get(member=user)
                    group_membership.is_admin = True
                    group_membership.save()
                
                return redirect('group_detail_view', group_id=group.id)
            else:
                # Handle the case where the selected user is not a member of the group
                pass
    else:
        form = AddAdminForm(group_id=group_id)

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



# def mark_member_as_deceased(request, group_id, member_id):
#     group = get_object_or_404(Group, id=group_id, is_active=True)
#     member = get_object_or_404(Profile, id=member_id, groups=group)
#     admin = group.get_admins()

#     if request.user not in admin:
#         raise PermissionDenied("You are not authorized to perform this action.")

#     if request.method == 'POST':
#         member.deceased = True
#         member.save()
#         messages.success(request, f'{member} has been marked as deceased.')
#         return redirect('member_detail', group_id=group_id, member_id=member_id)



    


       
   
    
    
    
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Project

def invite_collaborator(request, project_id):
    # Grab the specific project we are inviting someone to
    project = get_object_or_404(Project, id=project_id)
    
    # Optional Security: Ensure only the creator can invite people
    if request.user.id != project.owner_id:
        messages.error(request, "Only the project owner can invite collaborators.")
        return redirect('project_detail', project_id=project.id) # Change to your actual URL name

    if request.method == 'POST':
        # Grab the email the user typed into the form
        email = request.POST.get('email')
        
        try:
            # 1. Search the database for a user with this exact email
            user_to_invite = User.objects.get(email=email)
            
            # 2. Add them to the ManyToMany 'collaborators' list we made earlier
            project.collaborators.add(user_to_invite)
            
            # 3. Send a success message to the UI
            messages.success(request, f"Successfully added {user_to_invite.username} to the project!")
            
        except User.DoesNotExist:
            # If the database can't find the email, catch the crash and show an error
            messages.error(request, "No user found with that email address.")
            
    # Bounce them right back to the project page 
    # (Make sure 'project_detail' matches the name= you gave your project URL!)
    return redirect('project_detail', project_id=project.id)
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from .forms import LoginForm, RegisterForm

def sign_in(request):

    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('posts')
        
        form = LoginForm()
        return render(request,'users/login.html', {'form': form})
    
    elif request.method == 'POST':
        form = LoginForm(request.POST)
        
        if form.is_valid():
            username = form.cleaned_data['username']
            password=form.cleaned_data['password']
            user = authenticate(request,username=username,password=password)
            if user:
                login(request, user)
                messages.success(request,f'Hi {username.title()}, welcome back!')
                return redirect('posts')
        
        # either form not valid or user is not authenticated
        messages.error(request,f'Invalid username or password')
        return render(request,'users/login.html',{'form': form})

    
        
def sign_out(request):
    logout(request)
    messages.success(request,f'You have been logged out.')
    return redirect('login')        



def sign_up(request):
    if request.method == 'GET':
        form = RegisterForm()
        return render(request, 'users/register.html', { 'form': form})

    elif request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            try:
                form.save()
                messages.success(request,f'Registration successful. Please log in.')
                return redirect('login')
            except Exception as e:
                messages.error(request,f'An error occurred during registration. Please try again.')
                return render(request, 'users/register.html', { 'form': form})

        messages.error(request,f'Please correct the errors below.')
        return render(request, 'users/register.html', { 'form': form})

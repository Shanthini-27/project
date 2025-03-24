from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm
from .models import CustomUser
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import timezone
import uuid

def index(request):
    return render(request, 'user/index.html', {'title': 'index'})

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.confirmation_token = str(uuid.uuid4())
            user.confirmation_token_expires = timezone.now() + timezone.timedelta(hours=1)
            user.save()
            email = form.cleaned_data.get('email')
            try:
                htmly = get_template('user/Email.html')
                d = {'username': user.username, 'token': user.confirmation_token}
                subject, from_email, to = 'welcome', 'your_email@gmail.com', email
                html_content = htmly.render(d)
                msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                messages.success(request, f'Account created for {user.username}. Please check your email for confirmation.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'Error sending email: {e}')
        else:
            messages.error(request, 'Error registering user')
    else:
        form = UserRegisterForm()
    return render(request, 'user/register.html', {'form': form, 'title': 'register'})

def confirm_email(request, token):
    try:
        user = CustomUser.objects.get(confirmation_token=token)
        if user.confirmation_token_expires < timezone.now():
            messages.error(request, 'Confirmation token has expired. Please register again.')
            return redirect('register')
        user.is_active = True
        user.save()
        messages.success(request, 'Email confirmed successfully. You can now login.')
        return redirect('login')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid confirmation token.')
        return redirect('register')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('index')
            else:
                messages.error(request, 'Your account is not active. Please check your email for confirmation.')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'user/login.html', {'title': 'login'})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


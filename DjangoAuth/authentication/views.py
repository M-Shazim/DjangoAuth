from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from DjangoAuth import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .tokens import generate_token
from django.core.mail import send_mail, EmailMessage
# Create your views here.

def home(request):
    return render(request, "authentication/index.html")

def signup(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        pass1 = request.POST["pass1"]
        pass2 = request.POST["pass2"]

        if User.objects.filter(username=username):
            messages.error(request, "Username already exists! please try changing your username. ")
            return redirect("home")

        if User.objects.filter(email=email):
            messages.error(request, "Email already registered! please try changing your email. ")
            return redirect("home")

        if len(username)>10:
            messages.error(request, "Username must be under 10 characters! please try changing your username. ")
            return redirect("home")
        
        if pass1!=pass2:
            messages.error(request, "passwords didn't match! ")
            return redirect("home")
        


        myuser = User.objects.create_user(username, email, pass1)
        myuser.is_active = False
        myuser.save()

        messages.success(request, "Successfully created user. We have sent you a joining email, go check it out!!!")


        #Welcome Email
        subject = "Welcome to DjnagoAuth."
        message = "Hello " + myuser.username + "! \n " + "From activating your account, Kindly "
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject,message, from_email, to_list, fail_silently=True)

        #Email Address Confirmation Email
        current_site = get_current_site(request)
        email_subject = "Confirm your email @ DjangoAuth"
        message2 = render_to_string("email_confirmation.html",{
            "name" : myuser.username,
            "domain" : current_site.domain,
            "uid" : urlsafe_base64_encode(force_bytes(myuser.pk)),
            "token" : generate_token.make_token(myuser)

        })
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )

        email.fail_silently = True
        email.send()

        return redirect("signin")
    
    return render(request, "authentication/signup.html")

def signin(request):

    if request.method == "POST":
        username = request.POST["username"]
        pass1 = request.POST["pass1"]

        user =  authenticate(username=username, password=pass1)

        if user is not None:
            login(request,user)
            messages.success(request, "Successfully LoggedIn. ")

            return render(request, "authentication/index.html", {
                "username" : username,
            })

        else:
            messages.error(request, "Bad Credentials")
            return redirect("home")

    return render(request, "authentication/signin.html")

def signout(request):
    logout(request)
    messages.success(request, "Logged out successfully! ")
    return redirect("home")


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        myuser.save()
        login(request, myuser)
        return redirect("home")

    else:
        return render(request, "activation_failed.html")

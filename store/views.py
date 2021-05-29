from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import datetime
from django.conf import settings
from django.core.mail import send_mail
from .models import *
from .models import *
from .forms import *
from .utils import cookieCart, cartData, guestOrder
from django.http import HttpResponse
from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from .forms import CreateUserForm
from django.contrib.auth import authenticate, login, logout
from verify_email.email_handler import send_verification_email
import subprocess, os, platform
from subprocess import call

from django.contrib import messages

from django.contrib.auth.decorators import login_required


def registerPage(request):
    if request.user.is_authenticated:
        return redirect('store')
    else:
        form = CreateUserForm()
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                user=form.save()
                #send_mail(subject,message,from_email,to_list,fail_silently=True)
                subject = 'thankyou for registering'
                message = 'welcome to fashion store'
                from_mail = settings.EMAIL_HOST_USER
                to_list = [user.email, settings.EMAIL_HOST_USER]
                send_mail(subject,message,from_mail,to_list,fail_silently=True)
                username = form.cleaned_data.get('username')
                messages.success(request, 'Account was created for ' + username)
                Customer.objects.create(
                    user=user,
                    email=user.email,
                )
                return redirect('login')

        context = {'form': form}
        return render(request, 'store/register.html', context)


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('store')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('store')
            else:
                messages.info(request, 'Username OR password is incorrect')

        context = {}
        return render(request, 'store/login.html', context)


# @login_required(login_url='login')
def logoutUser(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def image_upload_view(request):
    """Process images uploaded by users"""
    customer = request.user.customer
    form = AccountSettings(instance=customer)

    if request.method == 'POST':
        form = AccountSettings(request.POST, request.FILES,instance=customer)
        if form.is_valid():
            form.save()

    groups = customer.group.all()
    context = {'form':form, 'groups':groups}
    return render(request, 'store/upload.html', context)

def store(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    products = Product.objects.all()
    context = {'products': products, 'cartItems': cartItems}
    return render(request, 'store/store.html', context)


def cart(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)

def productDetail(request, id):
    product = Product.objects.get(id=id)
    return render(request, 'store/product_detail.html', {"product": product})

def virtualTryOn(request, id):
    product = Product.objects.get(id=id)
    f = open(r"C:\Users\Shreya Yadav\Desktop\VTO\newVTO\Down-to-the-Last-Detail-Virtual-Try-on-with-Detail-Carving\demo\demo.txt","w")
    f.write(request.user.customer.image.url[19:len(request.user.customer.image.url)].split('.')[0].split('_')[0]+".jpg ")
    f.write(request.user.customer.image.url[19:len(request.user.customer.image.url)].split('.')[0].split('_')[0]+"_keypoints.json ")
    f.write(product.image.url[8:len(product.image.url)].split('.')[0].split('_')[0]+".jpg ")
    f.write("test")
    f.close()
    os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
    if platform.system() == 'Windows':
        programfiles = ('PROGRAMW6432' if platform.architecture()[0] == '32bit'
                    else 'PROGRAMFILES')
    bash_exe = os.getenv(programfiles) + r'\Git\bin\bash'
    subprocess.call([bash_exe, '-c', 'C:/Users/Shreya\ Yadav/Desktop/VTO/newVTO/Down-to-the-Last-Detail-Virtual-Try-on-with-Detail-Carving/demo.sh'])
    form = Viton()
    return redirect('/images/Viton/0.jpg')

def checkout(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action:', action)
    print('Product:', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(
        customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(
        order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(
            customer=customer, complete=False)
    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment submitted..', safe=False)

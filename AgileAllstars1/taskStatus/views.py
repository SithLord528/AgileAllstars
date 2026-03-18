from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse('<h1>Task Status Page</h1>')

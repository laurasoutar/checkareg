from django.shortcuts import render

# Create your views here.
def get_reg(request):
    return render(request, 'checkareg/get_reg.html', {})
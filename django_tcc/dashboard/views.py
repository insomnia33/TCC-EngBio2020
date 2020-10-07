from django.shortcuts import render
from dashboard.main import main

path = "D:\\TCC\\input\\"

# Create your views here.

def home(request):   
    if request.method == 'POST':
        fileName = request.FILES['myFile'].name
        dictList = [main(path, fileName)]
        context = {'data' : dictList}
        
        return render(request, 'dashboard/dash.html', context)
    return render(request, 'dashboard/home.html')



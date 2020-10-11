from django.shortcuts import render
from dashboard.main import main, execute
import json

path = "D:\\TCC\\input\\"

# Create your views here.

def home(request):   
    if request.method == 'POST':
        if 'execute' in request.POST:
            
            with open('data.json') as f:
                dictList = json.load(f)

            context = {'data' : [execute(dictList[0], path)]}
            return render(request, 'dashboard/dash.html', context)

        else:
            fileName = request.FILES['myFile'].name
            dictList = [main(path, fileName)]
            context = {'data' : dictList}
            with open('data.json', 'w') as f:
                json.dump(dictList, f)
            return render(request, 'dashboard/dash.html', context)

    else:    
        return render(request, 'dashboard/home.html')


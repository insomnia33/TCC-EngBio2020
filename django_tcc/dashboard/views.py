from django.shortcuts import render
from dashboard.main import main, execute
from django.core.files.storage import FileSystemStorage
import json


# Create your views here.

def home(request):   
    if request.method == 'POST':
        if 'execute' in request.POST:
            
            with open('data.json') as f:
                dictList = json.load(f)

            context = {'data' : [execute(dictList[0])]}
            return render(request, 'dashboard/dash.html', context)

        else:
            uploadedFile = request.FILES['myFile']
            fs = FileSystemStorage()
            fs.save(uploadedFile.name, uploadedFile)
            print('media/'+uploadedFile.name)
            dictList = [main(uploadedFile.name)]
            context = {'data' : dictList}
            with open('data.json', 'w') as f:
                json.dump(dictList, f)
            return render(request, 'dashboard/dash.html', context)
            return render(request, 'dashboard/dash.html')
    else:    
        return render(request, 'dashboard/home.html')


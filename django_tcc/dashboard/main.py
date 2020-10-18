import SimpleITK as sitk
import numpy as np
import imageio
import vtk
import os

path = 'dashboard/media/'

def volume(image, label=1):
    # check if is a file or a path, if is a path then load the image
    if(isinstance(image, str)):
        image = sitk.ReadImage(image, sitk.sitkInt16)
           
    maskArray = sitk.GetArrayFromImage(image) # get the calcification mask pixel array
    pxX, pxY, pxZ = image.GetSpacing() # get the x, y and z spacing (mm³) from metadata

    count, _, _ = np.where(maskArray == label) # count the number of voxels
    volume = len(count)*pxX*pxY*pxZ # multiply number of voxels with voxel spacing (x,y,z) getting the result in mm³
    
    return int(volume)

def volumeProportion(refMask, segMask): # refference mask and segmentation mask
    # check if is a file or a path, if is a path then load the image
    if(isinstance(refMask, str)):
        refMask = sitk.ReadImage(refMask, sitk.sitkInt16)
        
    if(isinstance(segMask, str)):
        segMask = sitk.ReadImage(segMask, sitk.sitkInt16)
    
    refVol = volume(refMask) # get volume from reference mask
    segVol = volume(segMask) # get volume from segmentation mask
    
    proportion = (segVol/refVol)*100 # calculate proportion in %

    return proportion

def stlConverter(image):
    stlWriter = vtk.vtkSTLWriter()
    stlWriter.SetFileName('test.stl')
    stlWriter.SetInputConnection(dmc1.GetOutputPort())
    stlWriter.SetInputConnection(dmc2.GetOutputPort())
    stlWriter.SetInputConnection(dmc.GetOutputPort())
    stlWriter.Write()

def sliceSaver(image):
    
    axialSlice = np.rot90(sitk.GetArrayFromImage(image)[72,:,:], 2)
    coronalSlice = np.rot90(sitk.GetArrayFromImage(image)[:,72,:], 2)
    sagitalSlice = np.rot90(sitk.GetArrayFromImage(image)[:,:,72], 2)

    imageio.imwrite('dashboard/static/axialSlice.png', axialSlice)
    imageio.imwrite('dashboard/static/coronalSlice.png', coronalSlice)
    imageio.imwrite('dashboard/static/sagitalSlice.png', sagitalSlice)


def execute(volumes):
    #predict here

    image = sitk.ReadImage(path+volumes['FileName'])

    imageEdema = sitk.BinaryThreshold(image, 0.5, 0.9, insideValue=2)
    imageCore = sitk.BinaryThreshold(image, 0.9, insideValue=3)
    imageWT = sitk.BinaryThreshold(image, 0.5, insideValue=1)

    sitk.WriteImage(imageEdema, path+'edema.nii.gz')
    sitk.WriteImage(imageCore, path+'core.nii.gz')
    sitk.WriteImage(imageWT, path+'wholetumor.nii.gz')

    #volumes['Necrosis'] = volume(mask, 1)/1000
    #volumes['EnhancingTumor'] = volume(mask, 4)/1000
    #volumes['PropEnhancingTumor'] = (volumes['EnhancingTumor']/volumes['WholeTumor'])*100
    #volumes['PropNecrosis'] = (volumes['Necrosis']/volumes['WholeTumor'])*100

    volumes['Edema'] = volume(imageEdema, 2)/1000
    volumes['TumorCore']  = volume(imageCore, 3)/1000
    volumes['WholeTumor'] = volume(imageWT, 1)/1000
    volumes['PropTumorCore'] = (volumes['TumorCore']/volumes['WholeTumor'])*100
    volumes['PropEdema'] = (volumes['Edema']/volumes['WholeTumor'])*100
    volumes['PropTumor'] = (volumes['WholeTumor']/volumes["Volume"])*100

    print(volumes)

    return volumes

def main(fileName):
    image = sitk.ReadImage(path+fileName)
    sliceSaver(image)
    imageVolume = volume(sitk.BinaryThreshold(image, -0.8))/1000

    volumes = {}
    volumes['FileName'] = fileName
    volumes["Volume"] = imageVolume
    volumes['Nome'] = 'Paciente 92'
    volumes['Idade'] = '24 anos'
    volumes['Sexo'] = 'Masculino'
    volumes['Regiao'] = 'Cabeça'
    volumes['Modalidade'] = 'Ressonância Magnética'
    volumes['Aquisicao'] = '16/03/2020'
    volumes['Shape'] = image.GetSize()
    volumes['Spacing'] = image.GetSpacing()



    return(volumes)
    
    
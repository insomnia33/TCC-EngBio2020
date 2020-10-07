import SimpleITK as sitk
import numpy as np
import vtk
import os

def volume(image, label=1):
    # check if is a file or a path, if is a path then load the image
    if(isinstance(image, str)):
        image = sitk.ReadImage(image, sitk.sitkInt16)
           
    maskArray = sitk.GetArrayFromImage(image) # get the calcification mask pixel array
    pxX, pxY, pxZ = image.GetSpacing() # get the x, y and z spacing (mm³) from metadata

    count, _, _ = np.where(maskArray == label) # count the number of voxels
    volume = len(count)*pxX*pxY*pxZ # multiply number of voxels with voxel spacing (x,y,z) getting the result in mm³
    print(volume)
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

    

def main(path, file):
    image = sitk.ReadImage(path+file)
    mask = sitk.ReadImage(path+'truth.nii.gz')
    imageVolume = volume(sitk.BinaryThreshold(image, 1))/1000
    
    volumes = {}
    volumes['Nome'] = 'Paciente 33'
    volumes['Idade'] = '33 anos'
    volumes['Sexo'] = 'Masculino'
    volumes['Regiao'] = 'Cabeça'
    volumes['Modalidade'] = 'Ressonância Magnética'
    volumes['Aquisicao'] = '16/03/2020'
    volumes['Shape'] = image.GetSize()
    volumes['Spacing'] = image.GetSpacing()
    volumes['Path'] = path+file
    volumes['Necrosis'] = volume(mask, 1)/1000
    volumes['EnhancingTumor'] = volume(mask, 4)/1000
    volumes['Edema'] = volume(mask, 2)/1000
    volumes['TumorCore']  = volumes['Necrosis']+volumes['EnhancingTumor']
    volumes['WholeTumor'] = volumes['TumorCore']+volumes['Edema']
    volumes['PropEnhancingTumor'] = (volumes['EnhancingTumor']/volumes['WholeTumor'])*100
    volumes['PropNecrosis'] = (volumes['Necrosis']/volumes['WholeTumor'])*100
    volumes['PropEdema'] = (volumes['Edema']/volumes['WholeTumor'])*100
    volumes['PropTumor'] = (volumes['WholeTumor']/imageVolume)*100

    return(volumes)
    
    
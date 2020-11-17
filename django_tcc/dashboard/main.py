import SimpleITK as sitk
from tensorflow.keras.models import load_model
from segmentation_models.losses import *
from segmentation_models.metrics import *
import numpy as np
import imageio
import vtk
import os
import pandas as pd
from zipfile import ZipFile
from glob import glob

'''Function list:
    volume(binary mask, label) -> Calculo de volume em mL -> [int] mL
    volumeProportion() -> Calculo da proporção para o encéfalo em % -> [float] %
    stlConverter() -> Conversão de .nii para .stl -> [arquivo] .stl
    sliceSaver() -> Salvar a fatia do meio de cada eixo para visualização -> [arquivos] .png
    downsample() -> Reduz a forma da matriz cúbica do exame -> [objeto sitk]
    prediction() -> Carrega o modelo e executa a predição -> [mapa probabilistico] .nii
    execute() -> Ativado ao clicar no botão Executar
    main() -> Ativado ao clicar em Selecionar Arquivo
'''
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true' # Enable this if GPU run out memory

path = 'dashboard/media/' # media folder of server
models = 'dashboard/static/models/' # 3D model folder

def volume(image, label=1):
    # check if is a file or a path, if is a path then load the image
    if(isinstance(image, str)):
        image = sitk.ReadImage(image, sitk.sitkInt16) # Read image file
           
    maskArray = sitk.GetArrayFromImage(image) # get the calcification mask pixel array
    pxX, pxY, pxZ = image.GetSpacing() # get the x, y and z spacing (mm³) from metadata

    count, _, _ = np.where(maskArray == label) # count the number of voxels
    volume = len(count)*pxX*pxY*pxZ # multiply number of voxels with voxel spacing (x,y,z) getting the result in mm³
    
    return int(volume)/1000 # return the volume in cm³ or mL

def volumeProportion(refMask, segMask): # refference mask and segmentation mask
    # check if is a file or a path, if is a path then load the image
    if(isinstance(refMask, str)):
        refMask = sitk.ReadImage(refMask, sitk.sitkInt16) # Read image file
        
    if(isinstance(segMask, str)):
        segMask = sitk.ReadImage(segMask, sitk.sitkInt16) # Read image file
    
    refVol = volume(refMask) # get volume from reference mask
    segVol = volume(segMask) # get volume from segmentation mask
    
    proportion = (segVol/refVol)*100 # calculate proportion in %

    return proportion

def stlConverter(filePath):
    # Receive NIFTI path to convert to STL
    reader = vtk.vtkNIFTIImageReader() # Instance the VTK reader
    reader.SetFileName(filePath) # Insert the filepath
    reader.Update() # Read the file

    contour = vtk.vtkMarchingCubes()  # Instance cube objects to create contours with voxels
    contour.SetInputData(reader.GetOutput()) # Pass the NIFTI 3D array to contour object
    contour.ComputeNormalsOn()
    contour.ComputeGradientsOn()
    contour.SetValue(0,1)
    contour.Update() # Create contour object

    stlWriter = vtk.vtkSTLWriter() # Instance the STL writer
    stlWriter.SetFileName(models+'brain.stl') # Set filepath
    stlWriter.SetInputConnection(contour.GetOutputPort())
    stlWriter.SetFileTypeToASCII() # STL ASCII file type
    stlWriter.Write() # Write STL file

def sliceSaver(image):
    # Receive SimpleITK object image file
    middle = int(image.GetSize()[2]/2) # Get middle slice
    axialSlice = np.rot90(sitk.GetArrayFromImage(image)[middle,:,:], 2) # Get array from SimpleITK Object in Axial Plane
    coronalSlice = np.rot90(sitk.GetArrayFromImage(image)[:,middle,:], 2) # Get array from SimpleITK Object in Coronal Plane
    sagitalSlice = np.rot90(sitk.GetArrayFromImage(image)[:,:,middle], 2) # Get array from SimpleITK Object in Sagital Plane
    # Write 8bit single slice files with IMAGEIO
    imageio.imwrite('dashboard/static/axialSlice.png', axialSlice)
    imageio.imwrite('dashboard/static/coronalSlice.png', coronalSlice)
    imageio.imwrite('dashboard/static/sagitalSlice.png', sagitalSlice)

def downsample(image):
    # Input SimpleITK object
    new_size = [64, 64, 64] # output size

    xyfactor = image.GetSize()[0]/64 # Pixel spacing increase factor
    zfactor = image.GetSize()[2]/64 # Slice thickness increase factor

    resample = sitk.ResampleImageFilter() # Instance resample object
    resample.SetInterpolator(sitk.sitkLinear) # Set the interpolator for resample
    resample.SetOutputDirection(image.GetDirection()) # Get direction from original file
    resample.SetOutputOrigin(image.GetOrigin()) # Get origin from original file
    # New spacing is defined by previous one by scaling factor
    new_spacing = (image.GetSpacing()[0]*xyfactor, image.GetSpacing()[1]*xyfactor, image.GetSpacing()[2]*zfactor) 
    resample.SetOutputSpacing(new_spacing)# Set new spacing

    orig_size = np.array(image.GetSize(), dtype=np.int) # Original Size
    orig_spacing = [spacing for spacing in image.GetSpacing()] # Original Spacing
    new_size = np.ceil(new_size).astype(np.int) #  image dimensions are in integers
    new_size = [int(s) for s in new_size] # new image size
    resample.SetSize(new_size) # Set new size

    return resample.Execute(image) # Apply Resample transformation and return the output

def postProcess(mask, flair_norm):

    binMask = sitk.BinaryThreshold(mask, 0.1, int(np.max(sitk.GetArrayFromImage(mask))))
    top = float(np.max(sitk.GetArrayFromImage(flair_norm)))
    binMaskCC = sitk.ConnectedComponent(binMask)
    binMaskCC = sitk.RelabelComponent(binMaskCC)
    labels = sitk.LabelShapeStatisticsImageFilter() # instance label shape statistic filter
    labels.Execute(binMaskCC)

    center = mask.TransformPhysicalPointToIndex(labels.GetCentroid(1))
    whole_tumor = sitk.ConnectedThreshold(flair_norm, [center], 2.8, top)

    return whole_tumor

def prediction(image):
    # SimpleITK image as input
    # Read .h5 model
    model = load_model(path+"flair_64_model.h5", custom_objects={'Dice Coefficient' : FScore(), 'Dice Loss' : DiceLoss()}, compile=False)
    
    imageArr = sitk.GetArrayFromImage(image) # Get 3D array from SimpleITK image object

    array = np.array([imageArr])
    array = array[None, ...] # Define dimension for the CNN array: (None, 1, 64, 64, 64)
    #print(f'INPUT SHAPE: {array.shape}')

    output = model.predict(array) # Apply prediction
    output = np.squeeze(output) # Remove "None" dimension, reduce to arrays
    output.shape
    #print(f'OUTPUT SHAPE: {output.shape}')

    mask = sitk.GetImageFromArray(output[0]) # Get the first label
    mask.CopyInformation(image) # Copy image coordinates information
    return mask # Return prediction TPM mask

def execute(volumes):
    # After clicking on EXECUTE button
    image = sitk.ReadImage(path+volumes['FileName']) # Read the file
    imageDown = downsample(sitk.Normalize(image)) # Downsample the file for prediction
    sitk.WriteImage(imageDown, path+'flair_downsampled.nii.gz') # Save downsampled file

    tpm = prediction(imageDown) # Pass the file on U-NET and get the Probabilistic Tissue Map
    top = float(np.max(sitk.GetArrayFromImage(tpm)))

    ### POST PROCESSING AREA ###
    # Splitting the TPM on desired ROI tissues, this could be improved with other technics and better thresholds.
    
    tcMask = sitk.BinaryThreshold(tpm, lowerThreshold=2400, upperThreshold=top,  insideValue=1)
    wtMask = postProcess(tpm, imageDown)
    edMask = wtMask - tcMask
    edMask = sitk.BinaryThreshold(edMask, 1, 1, insideValue=2, outsideValue=0)
    tcMask = sitk.BinaryThreshold(tcMask, lowerThreshold=1, upperThreshold=1,  insideValue=3, outsideValue=0)

    bot = float(np.min(sitk.GetArrayFromImage(imageDown))) # Get lower pixel intensity
    top = float(np.max(sitk.GetArrayFromImage(imageDown))) # Get higher pixel intensity
    image255 = sitk.IntensityWindowing(imageDown, bot, top) # Convert to 8 Bit image
    # Create the overlay on original image
    overlay = sitk.LabelOverlay(image=sitk.Cast(image255, sitk.sitkUInt8), labelImage=sitk.Cast(wtMask, sitk.sitkUInt8), opacity=0.7,colormap=[255, 0, 0])

    sliceSaver(overlay) # Save overlay slices
    stlConverter(path+'flair_downsampled.nii.gz') # Save downsampled STL version

    # Save all masks files on media folder
    sitk.WriteImage(wtMask, path+'flair_wt.nii.gz')
    sitk.WriteImage(edMask, path+'flair_ed.nii.gz')
    sitk.WriteImage(tcMask, path+'flair_tc.nii.gz')
    sitk.WriteImage(tpm, path+'flair_tpm.nii.gz')

    # Calculate FULL brain volume
    brainMask = sitk.BinaryThreshold(imageDown, 1, top)
    imageVolume = volume(brainMask)

    #volumes['Necrosis'] = volume(mask, 1)
    #volumes['EnhancingTumor'] = volume(mask, 4)
    #volumes['PropEnhancingTumor'] = (volumes['EnhancingTumor']/volumes['WholeTumor'])*100
    #volumes['PropNecrosis'] = (volumes['Necrosis']/volumes['WholeTumor'])*100
    volumes["Volume"] = imageVolume
    volumes['TumorCore']  = volume(tcMask, 3) # Tumor Core volume calculation
    volumes['WholeTumor'] = volume(wtMask, 1) # Whole tumor volume
    volumes['Edema'] = volume(edMask, 2)
    volumes['PropTumorCore'] = (volumes['TumorCore']/volumes['WholeTumor'])*100
    volumes['PropEdema'] = (volumes['Edema']/volumes['WholeTumor'])*100
    volumes['PropTumor'] = (volumes['WholeTumor']/volumes["Volume"])*100
    volumes['Shape'] = imageDown.GetSize()
    volumes['Spacing'] = imageDown.GetSpacing()

    #print(volumes)
    df = pd.DataFrame.from_dict(volumes)
    df.to_csv(path+'data.csv', index=False) # Save information on a CSV sheet

    fileList = glob(path+'*.nii.gz')
    zipObj = ZipFile(path+'nifti.zip', 'w')
    for file in fileList:
        zipObj.write(file)
    zipObj.close()
    return volumes # Return volumes to fill dashboard

def main(fileName):
    # After uplading file to media/ django pass filepath to main()
    image = sitk.ReadImage(path+fileName) # read file
    sliceSaver(image) # Save slices from file to visualization
    stlConverter(path+fileName) # Save main file as .STL

    volumes = {} # Create the dictionary to be used on API
    volumes['FileName'] = fileName # Set filename
    # Nome, Idade, Sexo, Regiao, Modalidade, Aquisicao are artificially inserted because NIFTI files dont have it, but DICOM has on metadata
    volumes['Nome'] = 'Paciente 33'
    volumes['Idade'] = '24 anos'
    volumes['Sexo'] = 'Masculino'
    volumes['Regiao'] = 'Cabeça'
    volumes['Modalidade'] = 'Ressonância Magnética'
    volumes['Aquisicao'] = '16/03/2020'
    volumes['Shape'] = image.GetSize() # Get image shape
    volumes['Spacing'] = image.GetSpacing() # Get image voxel spacing

 
    return(volumes) # Return information
    
    
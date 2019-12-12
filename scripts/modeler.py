import numpy as np, pandas as pd, math

#If the user checked the appropriate flag, they may be importing MIC vs disk data or MIC vs MIC, and the function below
#will try to determine which.
def determine_data_type(current_model):
  try:
    x = np.asarray([float(z) for z in current_model.current_dataset['disks'].values])
  except:
    return 'disk', 'Could not process the data! Column 2 contains non-numeric values. Please reload and try again.'
  if np.min(x) < 0:
    return 'disk', 'Could not process the data! Column 2 contains negative values. Please reload and try again.'
  if np.min(x) < 0.12 or np.max(x) > 60:
    return 'mic', '0'
  #MICs are nearly ALWAYS assigned to one of the values below based on microbiological standard practice.
  #So if all or nearly all of the values in column 2 fall into one of these, then we're almost certainly dealing
  #with MIC data. Disk values, by contrast, will generally be integers in [5,50]. 
  xbins = {0.016,0.03,0.06,0.12,0.125,0.25,0.5,1,2,4,8,16,32,64,128,256}
  likely_mic_values = 0
  for xval in x:
    if xval in xbins:
      likely_mic_values += 1
  #90% is a little arbitrary but this seems to work quite well in our experience so far...
  if likely_mic_values >= 0.9 * x.shape[0]:
    return 'mic', '0'
  return 'disk', '0'

def process_traindata(raw, miccutoffR, miccutoffS):
  #2 is susceptible, 1 is intermediate, 0 is resistant.
        x, y = [], []
        for i in range(raw.shape[0]):
                yreal = float(raw['mics'].values[i])
    #We have to be careful about use of the >= and <= here. Microbiologists always specify for their cutoffs
    #whether they are using >= or > and MICs are discrete value data not continuous.
                if yreal >= miccutoffR:
                  y.append(0)
                elif yreal <= miccutoffS:
                  y.append(2)
                else:
                  y.append(1)
  #The x-values -- the disk values -- are relatively straightforward since we do not have to assign categories
  #for these.
        x = np.asarray(raw['disks'].values)
        return x, np.asarray(y)

def fit_data(current_model, data_type='disk'):
  if data_type == 'mic':
    return 'The MIC vs MIC data type is not currently supported, this feature is being added. Please check back later.'
  try:
    #Check to make sure the user entered valid cutoffs. If not, give 'em an error.
    miccutoffR = float(current_model.miccutoffR)
    miccutoffS = float(current_model.miccutoffS)
  except:
    return "The MIC cutoffs you have entered are not valid numeric characters. Try again."

  try:
    #Process current dataset. We're going to fit a classifier to separate susceptible from non-susceptible
    #(aka ysuscep) and resistant from nonresistant (aka yresist). x is the disk values.
    x, y = process_traindata(current_model.current_dataset, miccutoffR, miccutoffS)
  except:
    #If we couldn't do that, they PROBABLY entered numeric characters. Give 'em an error.
    return "The data could not be processed. Typically this error results when it contains non-numeric characters (e.g. <=). Try again."

  #Check to make sure their dataset really does contain both flavors. If not, give 'em an error.
  if np.max(y) < 2 or np.min(y) > 0:
    return ("You are trying to fit data that either does not contain any resistant strains or does not contain any susceptible strains "
        "(i.e. there are only resistant + intermediate or resistant + susceptible in this dataset). Autofitting will "
            "not work. You could use manual cutoff selection for this dataset. Check the manual override button to proceed.")
  #try:
    #Currently we only have one modeling approach incorporated although we can add another 
      
  window_widths = current_model.model_engine.fit_disk_data(x,y)
  current_model.diskcutoffR = current_model.model_engine.cutoff_R
  current_model.diskcutoffS = current_model.model_engine.cutoff_S
  if data_type == 'mic':
    xbins = np.asarray([0.016,0.03,0.06,0.12,0.125,0.25,0.5,1,2,4,8,16,32,64,128,256])
    for i in range(1, len(xbins)):
      if current_model.diskcutoffR > xbins[i-1] and current_model.diskcutoffR <= xbins[i]:
        current_model.diskcutoffR = xbins[i]
      if current_model.diskcutoffS >= xbins[i-1] and current_model.diskcutoffS < xbins[i]:
        current_model.diskcutoffS = xbins[i-1]
  current_model.diskcutoffS = float(current_model.diskcutoffS)
  current_model.diskcutoffR = float(current_model.diskcutoffR)
  if len(window_widths) > 0:
    return ', '.join(['!'] + window_widths)
  else:
    return '0'
  #except:
    #If we have serious unexplained errors in fitting, give 'em a catchall error message.
  #  return "There was an error during fitting. The fit has not been used."

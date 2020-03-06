import numpy as np
from copy import copy


def process_traindata(raw, miccutoffR, miccutoffS):
  #2 is susceptible, 1 is intermediate, 0 is resistant.
  x, y = [], []
  for i in range(len(raw['mics'])):
    yreal = raw['mics'][i]
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
  x = np.asarray(raw['disks'])
  return x, np.asarray(y)

def fit_data(current_model):
  try:
    #Check to make sure the user entered valid cutoffs. If not, give 'em an error so we don't even
    #try to plot the data or do anything else.
    miccutoffR = float(current_model.ycutoffR)
    miccutoffS = float(current_model.ycutoffS)
  except:
    return "The MIC cutoffs you have entered are not valid numeric characters. Try again."

  #If they haven't loaded any data yet, throw an error.
  if current_model.current_dataset['disks'] is None:
      return ("You want to fit the data, but you haven't loaded any? "
                          "Try loading some first. Now there's an idea!")
  #If the user is choosing their own cutoffs, we don't NEED to fit their
  #data, so we can just return without doing anything. Although DO check
  #first to make sure they haven't entered non-numeric cutoffs.
  #Also, none of this applies if it is MIC vs MIC data.
  if current_model.use_user_defined_disk_cutoffs == True and current_model.mic_vs_mic==False:
    try:
      _ = float(current_model.xcutoffR)
      _ = float(current_model.xcutoffS)
    except:
      return ("You've chosen to enter user-specified disk cutoffs BUT have entered non-numeric "
              "values. Please revise.")
    return '0'

  #If the user is in MIC vs MIC mode, we can just set the xcutoffs to equal the ycutoffs and return.
  #We don't need to do any more "fitting" than that, because for e-test and other similar MIC vs MIC
  #applications, FDA requires them to use same cutoff for e-test MIC and broth MIC.
  #We just make sure to use copy so we don't have multiple bindings to same object.
  if current_model.mic_vs_mic == True:
    current_model.xcutoffR = copy(float(current_model.ycutoffR))
    current_model.xcutoffS = copy(float(current_model.ycutoffS))
    return '0'

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
  current_model.xcutoffR = float(current_model.model_engine.cutoff_R)
  current_model.xcutoffS = float(current_model.model_engine.cutoff_S)
  if len(window_widths) > 0:
    return ', '.join(['!'] + window_widths)
  else:
    return '0'

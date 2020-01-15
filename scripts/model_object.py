import pandas as pd, model_core

#Class model_parameter_set is the object that stores all associated model parameters.
#Each instance of disk_fitter has an object of class model_parameter_set stored
#as its "current model", and any time fitting occurs, it updates the object
#attributes, all of which are listed below.
#The model_parameter_set object in turn contains an object of class mgm (described
#in model_core.py) as one of ITS attributes, and this mgm object and its
#routines will do the actual fitting.
#THe functions that update the error tables, however, belong to class model_parameter_set.
class model_parameter_set():

  def __init__(self):
    self.current_dataset = pd.DataFrame()
    self.model_type = 'mgm'
    self.miccutoffS = 4.0
    self.miccutoffR = 16.0
    self.diskcutoffS = 32.0
    self.diskcutoffR = 12.0
    self.model_engine = model_core.mgm()
    self.strain_name = 'Acinteobacter baumannii'
    self.use_user_defined_disk_cutoffs = False
    self.determine_if_mic_vs_mic = False
    self.is_mic_vs_mic = False
    #The error counts in the final export table distinguish between what FDA considers 'very major' and 'major errors'.
    self.error_counts = {'num_strains':0,'very major errors':0,
                         'major errors':0, 'minor errors':0}

    #FDA also distinguishes between error types that occur in certain bands. Hence the following dictionaries.
    self.i_plus2_error = {'num_strains':0,'very major errors':0,
                          'major errors':0, 'minor errors':0}
    self.i_plus1_minus1_error = {'num_strains':0,'very major errors':0,
                                 'major errors':0, 'minor errors':0}
    self.i_minus2_error = {'num_strains':0,'very major errors':0,
                           'major errors':0, 'minor errors':0}

    self.colormap_type = 'christmas_colors'


  def update_error_tables(self,data_type='disk'):
    try:
      self.miccutoffR = float(self.miccutoffR)
      self.miccutoffS = float(self.miccutoffS)
      self.diskcutoffR = float(self.diskcutoffR)
      self.diskcutoffS = float(self.diskcutoffS)
    except:
      return 'Non-numeric cutoff entered!'
    self.error_counts = {'num_strains':self.current_dataset.shape[0],
                         'very major errors':0, 'major errors':0, 'minor errors':0}
    self.i_plus2_error = {'num_strains':0,'very major errors':0, 'major errors':0, 'minor errors':0}
    self.i_plus1_minus1_error = {'num_strains':0,'very major errors':0, 'major errors':0, 'minor errors':0}
    self.i_minus2_error = {'num_strains':0,'very major errors':0, 'major errors':0, 'minor errors':0}
                           
    
    if data_type != 'mic':
      self.update_error_for_disk_data()
    else:
      self.update_error_for_mic_vs_mic_data()
    return '0'

  def update_error_for_disk_data(self):
    diskvalue = list(self.current_dataset['disks'].values)
    micvalue = list(self.current_dataset['mics'].values)
    for i in range(0, self.current_dataset.shape[0]):
      #Assign predictions and actual values to categories
      if micvalue[i] <= self.miccutoffS:
        actual_category = 0
      elif micvalue[i] < self.miccutoffR:
        actual_category = 1
      else:
        actual_category = 2

      if diskvalue[i] >= self.diskcutoffS:
        predicted_category = 0
      elif diskvalue[i] > self.diskcutoffR:
        predicted_category = 1
      else:
        predicted_category = 2

      if micvalue[i] > (self.miccutoffR):
        self.i_plus2_error['num_strains'] += 1
        error_code = self.check_is_error(predicted_category, actual_category)
        if error_code != 'no error':
          self.i_plus2_error[error_code] += 1
      elif micvalue[i] <= self.miccutoffR and micvalue[i] >= self.miccutoffS:
        self.i_plus1_minus1_error['num_strains'] += 1
        error_code = self.check_is_error(predicted_category, actual_category)
        if error_code != 'no error':
          self.i_plus1_minus1_error[error_code] += 1
      else:
        self.i_minus2_error['num_strains'] += 1
        error_code = self.check_is_error(predicted_category, actual_category)
        if error_code != 'no error':
          self.i_minus2_error[error_code] += 1
    #Here we have to be careful. FDA has specific definitions for 'very major error' and 'major error'.
    #That's what we're using here.
      error_code = self.check_is_error(predicted_category, actual_category)
      if error_code != 'no error':
        self.error_counts[error_code] += 1

  def update_error_for_mic_vs_mic_data(self):
    #If the user imported MIC vs MIC data, the procedure is the same but the direction of the inequality
    #for x values (what we're calling 'diskvalue' here for the sake of consistency) is reversed.
    diskvalue = list(self.current_dataset['disks'].values)
    micvalue = list(self.current_dataset['mics'].values)
    for i in range(0, self.current_dataset.shape[0]):
      if micvalue[i] <= self.miccutoffS:
        actual_category = 0
      elif micvalue[i] < self.miccutoffR:
        actual_category = 1
      else:
        actual_category = 2

      if diskvalue[i] >= self.diskcutoffR:
        predicted_category = 2
      elif diskvalue[i] > self.diskcutoffS:
        predicted_category = 1
      else:
        predicted_category = 0
      error_code = self.check_is_error(predicted_category, actual_category)
      if error_code != 'no error':
        self.error_counts[error_code] += 1

          
  def check_is_error(self, predicted_category, actual_category):
    if predicted_category != actual_category:
        if actual_category == 1 or predicted_category == 1:
          return 'minor errors'
        elif actual_category == 2 and predicted_category == 0:
          return 'very major errors'
        elif actual_category == 0 and predicted_category == 2:
          return 'major errors'
    else:
      return 'no error'

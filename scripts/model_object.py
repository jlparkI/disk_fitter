import model_core

#Class model_parameter_set is the object that stores all associated model parameters.
#Each instance of disk_fitter has an object of class model_parameter_set stored
#as its "current model", and any time fitting occurs, it updates the object
#attributes, all of which are listed below.
#The model_parameter_set object in turn contains an object of class mgm (described
#in model_core.py) as one of ITS attributes, and this mgm object and its
#routines will do the actual fitting.
#The reason for this design is so that if we ever add other fitting algorithms, we can
#trade out different "model_engines" to handle each type of fitting algorithm.
#THe functions that update the error tables belong to class model_parameter_set.
class model_parameter_set():

  def __init__(self):
    self.current_dataset = {'mics':None, 'disks':None}
    self.model_type = 'mgm'
    #These cutoffs are either specified by the user (if they so indicate by checking the appropriate boxes)
    #OR determined by model fitting, which is done by the model_engine object below.
    self.ycutoffS = 4.0
    self.ycutoffR = 16.0
    self.xcutoffS = 32.0
    self.xcutoffR = 12.0
    self.model_engine = model_core.mgm()
    self.strain_name = 'Acinteobacter baumannii'
    #If this is checked, use the user's defined cutoffs.
    self.use_user_defined_disk_cutoffs = False
    #This one is extremely important -- if it's true, we don't need
    #to fit a model, because the ycutoffs and xcutoffs are defined to be the same
    #by microbiologists for MIC data, so the data handling will be very different.
    self.mic_vs_mic = False
    #The error counts in the final export table distinguish between what FDA considers 'very major' and 'major errors'.
    self.error_counts = {'num_strains':0,'very major errors':0,
                         'major errors':0, 'minor errors':0}

    #Microbiologists also distinguish between error types that occur in certain bands.
    #Hence the following dictionaries. The precise definition of these bands is a little complicated
    #and will be discussed further under the comments in the error update functions below.
    self.i_plus2_error = {'num_strains':0,'very major errors':0,
                          'major errors':0, 'minor errors':0}
    self.i_plus1_minus1_error = {'num_strains':0,'very major errors':0,
                                 'major errors':0, 'minor errors':0}
    self.i_minus2_error = {'num_strains':0,'very major errors':0,
                           'major errors':0, 'minor errors':0}

    #Microbiologists define essential and categorical agreement for MIC vs MIC data only, so
    #IF we are dealing with MIC vs MIC data, we'll update these object attributes.
    self.essential_agreement = 0
    self.categorical_agreement = 0

    #color scheme for the plot.
    self.colormap_type = 'christmas_colors'

  #loads the user's specified csv file and does some basic error handling.
  #I didn't use Pandas because when freezing a python app to an exe, pandas
  #just adds a chunk to the memory footprint, and we don't really need to do
  #anything fancy that might require pandas here.
  def load_dataset(self, filename):
    error = False
    self.current_dataset = {'mics':[], 'disks':[]}
    with open(filename) as input_filehandle:
      for line in input_filehandle:
        try:
          current_values = line.strip().split(',')
          self.current_dataset['mics'].append(float(current_values[0]))
          self.current_dataset['disks'].append(float(current_values[1]))
        except:
          error = True
        if len(current_values) > 2:
          error = True
    if error == True or len(self.current_dataset['mics']) != len(self.current_dataset['disks']):
      #Make sure if there was an error loading the file to zero out self.current_dataset. That way,
      #other modules will be able to determine that no data has been loaded and do error handling
      #accordingly.
      self.current_dataset = {'mics':None, 'disks':None}
      return ('There was an error opening the selected file! Clearly you have made a mistake. '
          'One reason why this may have occurred '
          'is if you selected a non-csv file or a file with more than two columns. '
          'Remember your instructions!')
    else:
      return '0'



  #This function updates the model_parameter_set error dictionaries by first zeroing them out,
  #then calling either update_error_for_disk_data or update_error_for_mic_vs_mic_data,
  #depending on which option the user checked.
  def update_error_tables(self, is_mic_vs_mic=False):
    try:
      self.ycutoffR = float(self.ycutoffR)
      self.ycutoffS = float(self.ycutoffS)
      self.xcutoffR = float(self.xcutoffR)
      self.xcutoffS = float(self.xcutoffS)
    except:
      return 'Non-numeric cutoff entered!'
    self.error_counts = {'num_strains':len(self.current_dataset['mics']),
                         'very major errors':0, 'major errors':0, 'minor errors':0}
    self.i_plus2_error = {'num_strains':0,'very major errors':0, 'major errors':0, 'minor errors':0}
    self.i_plus1_minus1_error = {'num_strains':0,'very major errors':0, 'major errors':0, 'minor errors':0}
    self.i_minus2_error = {'num_strains':0,'very major errors':0, 'major errors':0, 'minor errors':0}
                           
    
    if is_mic_vs_mic == False:
      self.update_error_for_disk_data()
    else:
      self.update_error_for_mic_vs_mic_data()
    return '0'



  def update_error_for_disk_data(self):
    diskvalue = self.current_dataset['disks']
    micvalue = self.current_dataset['mics']
    for i in range(len(self.current_dataset['mics'])):
      #Assign predictions and actual values to categories
      if micvalue[i] <= self.ycutoffS:
        actual_category = 0
      elif micvalue[i] < self.ycutoffR:
        actual_category = 1
      else:
        actual_category = 2

      if diskvalue[i] >= self.xcutoffS:
        predicted_category = 0
      elif diskvalue[i] > self.xcutoffR:
        predicted_category = 1
      else:
        predicted_category = 2

    #This next part is a little subtle. Microbiologists when reviewing disk vs mic data like
    #to see how many of the errors (where predicted != actual) fall into ">=I+2", "I+1 to I-1"
    #and "<=I-2". I+x in this case is defined as +x bins. So for example if the cutoff is 16
    #then I is MIC < 16, I+1 is MIC <= 16 and I+2 is MIC <=32. I had to double-check with our
    #microbio team the first time I implemented this because the way they were using these
    #"I+2", "I+1 to I-1" etc. categories was initially unclear to me. At any rate, the next set of
    #if-else statements implements their logic to determine errors in the corresponding categories.
      if micvalue[i] > (self.ycutoffR):
        self.i_plus2_error['num_strains'] += 1
        error_code = self.check_is_error(predicted_category, actual_category)
        if error_code != 'no error':
          self.i_plus2_error[error_code] += 1
      elif micvalue[i] <= self.ycutoffR and micvalue[i] >= self.ycutoffS:
        self.i_plus1_minus1_error['num_strains'] += 1
        error_code = self.check_is_error(predicted_category, actual_category)
        if error_code != 'no error':
          self.i_plus1_minus1_error[error_code] += 1
      else:
        self.i_minus2_error['num_strains'] += 1
        error_code = self.check_is_error(predicted_category, actual_category)
        if error_code != 'no error':
          self.i_minus2_error[error_code] += 1
    #We now update the overall whole-dataset error counts. An error is any situation where
    #predicted != actual. Microbiologists define "very major", "major" and "minor" errors
    #depending on how predicted compares to actual (implemented in check_is_error below).
      error_code = self.check_is_error(predicted_category, actual_category)
      if error_code != 'no error':
        self.error_counts[error_code] += 1




  def update_error_for_mic_vs_mic_data(self):
    self.essential_agreement = 0
    self.categorical_agreement = 0
    num_wrong_predictions = 0
    num_predictions_within_twofold = 0
    #If the user imported MIC vs MIC data, the procedure is the same but the direction of the inequality
    #for x values (what we're calling 'diskvalue' here for the sake of consistency) is reversed.
    xvalue = self.current_dataset['disks']
    micvalue = self.current_dataset['mics']
    for i in range(len(self.current_dataset['mics'])):
      if micvalue[i] <= self.ycutoffS:
        actual_category = 0
      elif micvalue[i] < self.ycutoffR:
        actual_category = 1
      else:
        actual_category = 2

      if xvalue[i] >= self.xcutoffR:
        predicted_category = 2
      elif xvalue[i] > self.xcutoffS:
        predicted_category = 1
      else:
        predicted_category = 0


    #Same applies as for the analogous section under update_error_for_disk_data above
    #(see the long comment under that function to explain what we're doing in this next
    #group of if-else statements).
      if micvalue[i] > (self.ycutoffR):
        self.i_plus2_error['num_strains'] += 1
        error_code = self.check_is_error(predicted_category, actual_category)
        if error_code != 'no error':
          self.i_plus2_error[error_code] += 1
      elif micvalue[i] <= self.ycutoffR and micvalue[i] >= self.ycutoffS:
        self.i_plus1_minus1_error['num_strains'] += 1
        error_code = self.check_is_error(predicted_category, actual_category)
        if error_code != 'no error':
          self.i_plus1_minus1_error[error_code] += 1
      else:
        self.i_minus2_error['num_strains'] += 1
        error_code = self.check_is_error(predicted_category, actual_category)
        if error_code != 'no error':
          self.i_minus2_error[error_code] += 1


    #We now update the overall whole-dataset error counts. An error is any situation where
    #predicted != actual. Microbiologists define "very major", "major" and "minor" errors
    #depending on how predicted compares to actual (implemented in check_is_error below).
      error_code = self.check_is_error(predicted_category, actual_category)
      if error_code != 'no error':
        num_wrong_predictions += 1
        self.error_counts[error_code] += 1
      #We also check whether the e-test MIC was at least within twofold of the broth MIC. If so,
      #microbiologists consider it to be within "essential agreement" even if predicted
      #category is wrong. So they track both # errors and "essential agreement". (Yes, I know,
      #twofold is a huge error bar in most fields. It's what microbiologists use -- MIC assays
      #are not very precise.)
      if xvalue[i] <= micvalue[i]*2.0:
        if xvalue[i] >= micvalue[i]*0.5:
          num_predictions_within_twofold += 1
                                          
    #For MIC vs MIC data only, update the essential and categorical agreement attributes.
    self.essential_agreement = 100.0 * num_predictions_within_twofold / self.error_counts['num_strains']
    self.categorical_agreement = 100.0 - 100.0*num_wrong_predictions / self.error_counts['num_strains']
        



  #Very major error means predicted susceptible but actually resistant.
  #Major error means predicted resistant but actually susceptible.
  #Minor error means one of {predicted, actual} is intermediate
  #and the other is something else. This distinction comes down to the impact
  #a missed prediction would have on patient treatment. If you predict susceptible
  #but bug is resistant, for example, this is the worst thing that can happen, because
  #patient is being treated with a drug that won't help, so the infection will continue
  #to grow. Predicting resistant when actually susceptible is bad but not quite as bad --
  #just means the doctor will pass on what could actually have been a useful drug for that patient.
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

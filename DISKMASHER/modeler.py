import numpy as np, sklearn, pandas as pd, matplotlib.pyplot as plt, traceback
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix

def determine_data_type(qtapp):
	try:
		x = np.asarray([float(z) for z in qtapp.current_dataset['disks'].values])
	except:
		return 'disk', 'Could not process the data! Column 2 contains non-numeric values. Please reload and try again.'
	if np.min(x) < 0:
		return 'disk', 'Could not process the data! Column 2 contains negative values. Please reload and try again.'
	if np.min(x) < 1 or np.max(x) > 60:
		return 'mic', '0'
	xbins = {0.016,0.03,0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,256}
	likely_mic_values = 0
	for xval in x:
		if xval in xbins:
			likely_mic_values += 1
	if likely_mic_values > 0.9 * x.shape[0]:
		return 'mic', '0'
	return 'disk', '0'

def process_traindata(raw, miccutoffR, miccutoffS):
        x, ysuscep, yresist = [], [], []
        for i in range(raw.shape[0]):
                yreal = float(raw['mics'].values[i])
                if yreal >= miccutoffS and yreal < miccutoffR:
                        ysuscep.append(0)
                        yresist.append(0)
                elif yreal < miccutoffS:
                        ysuscep.append(1)
                        yresist.append(0)
                elif yreal >= miccutoffR:
                        ysuscep.append(0)
                        yresist.append(1)
        x = np.asarray(raw['disks'].values)
        ysuscep = np.asarray(ysuscep)
        xresist = np.asarray(yresist)
        return x, ysuscep, yresist

def fit_data(qtapp, data_type='disk'):
	try:
		#Check to make sure the user entered valid cutoffs. If not, give 'em an error.
		miccutoffR = float(qtapp.miccutoffR)
		miccutoffS = float(qtapp.miccutoffS)
	except:
		traceback.print_exc()
		return "The MIC cutoffs you have entered are not valid numeric characters. Try again."

	try:
		#Process current dataset. We're going to fit a classifier to separate susceptible from non-susceptible
		#(aka ysuscep) and resistant from nonresistant (aka yresist). x is the disk values.
		x, ysuscep, yresist = process_traindata(qtapp.current_dataset, miccutoffR, miccutoffS)
	except:
		#If we couldn't do that, they PROBABLY entered numeric characters. Give 'em an error.
		traceback.print_exc()
		return "The data could not be processed. Typically this error results when it contains non-numeric characters (e.g. <=). Try again."

	#Check to make sure their dataset really does contain both flavors. If not, give 'em error message 6.
	if np.unique(ysuscep).shape[0] == 1 or np.unique(yresist).shape[0] == 1:
		return ("You are trying to fit data that either does not contain any resistant strains or does not contain any susceptible strains "
				"(i.e. there are only resistant + intermediate or resistant + susceptible in this dataset). The data will be plotted and "
				"error rates calculated but auto-fitting (i.e. determination of disk cutoffs) cannot be conducted. You could try using "
				"manual cutoff selection for this dataset.")
	try:
		if qtapp.use_logistic_regression == True:
			suscep_vs_all = LogisticRegression(C=100, max_iter=10000)
			resist_vs_all = LogisticRegression(C=100, max_iter=10000)
			if data_type == 'mic':
				x = np.log(x)
			suscep_vs_all.fit(x.reshape(-1,1), ysuscep)
			resist_vs_all.fit(x.reshape(-1,1), yresist)
			if data_type != 'mic':
				qtapp.diskcutoffR = np.abs(resist_vs_all.intercept_[0] / resist_vs_all.coef_[0][0])
				qtapp.diskcutoffS= np.abs(suscep_vs_all.intercept_[0] / suscep_vs_all.coef_[0][0])
			else:
				qtapp.diskcutoffR = np.exp(np.abs(resist_vs_all.intercept_[0] / resist_vs_all.coef_[0][0]))
				qtapp.diskcutoffS= np.exp(np.abs(suscep_vs_all.intercept_[0] / suscep_vs_all.coef_[0][0]))
			return '0'
		else:
			#This isn't really a 'decision tree' because we only let it grow to depth 1 BUT the nature of the
			#algorithm makes it much more resistant to outliers than logistic regression. This is a nice alternative
			#for datasets with weird outliers.
			suscep_vs_all = DecisionTreeClassifier(max_depth=1)
			resist_vs_all = DecisionTreeClassifier(max_depth=1)
			suscep_vs_all.fit(x.reshape(-1,1), ysuscep)
			resist_vs_all.fit(x.reshape(-1,1), yresist)
			if data_type != 'mic':
				qtapp.diskcutoffR = resist_vs_all.tree_.threshold[0]
				qtapp.diskcutoffS= suscep_vs_all.tree_.threshold[0]
			else:
				qtapp.diskcutoffR = resist_vs_all.tree_.threshold[0]
				qtapp.diskcutoffS= suscep_vs_all.tree_.threshold[0]
			return '0'
	except:
		#If we have serious unexplained errors in fitting, give 'em a catchall error message.
		traceback.print_exc()
		return "There was an error during fitting. The fit has not been used."


def update_error_tables(qtapp, data_type='disk'):
	#We don't have to check the cutoffs to make sure they're allowed here because we already checked under
	#the fitting procedure.
	miccutoffR = float(qtapp.miccutoffR)
	miccutoffS = float(qtapp.miccutoffS)
	diskcutoffR = float(qtapp.diskcutoffR)
	diskcutoffS = float(qtapp.diskcutoffS)

	qtapp.error_counts = {'very major errors':0, 'major errors':0, 'minor errors':0}
	qtapp.confusion_matrix = np.zeros((3,3))
	diskvalue = list(qtapp.current_dataset['disks'].values)
	micvalue = list(qtapp.current_dataset['mics'].values)
	if data_type != 'mic':
		for i in range(0, qtapp.current_dataset.shape[0]):
			if micvalue[i] < miccutoffS:
				actual_category = 0
			elif micvalue[i] < miccutoffR:
				actual_category = 1
			else:
				actual_category = 2

			if diskvalue[i] > diskcutoffS:
				predicted_category = 0
			elif diskvalue[i] >= diskcutoffR:
				predicted_category = 1
			else:
				predicted_category = 2
			qtapp.confusion_matrix[actual_category, predicted_category] += 1
			if predicted_category != actual_category:
				if actual_category == 1 or predicted_category == 1:
					qtapp.error_counts['minor errors'] += 1
				elif actual_category == 2 and predicted_category == 0:
					qtapp.error_counts['very major errors'] += 1
				elif actual_category == 0 and predicted_category == 2:
					qtapp.error_counts['major errors'] += 1

	elif data_type == 'mic':
		for i in range(0, qtapp.current_dataset.shape[0]):
			if micvalue[i] < miccutoffS:
				actual_category = 0
			elif micvalue[i] < miccutoffR:
				actual_category = 1
			else:
				actual_category = 2

			if diskvalue[i] >= diskcutoffR:
				predicted_category = 2
			elif diskvalue[i] >= diskcutoffS:
				predicted_category = 1
			else:
				predicted_category = 0
			qtapp.confusion_matrix[actual_category, predicted_category] += 1
			if predicted_category != actual_category:
				if actual_category == 1 or predicted_category == 1:
					qtapp.error_counts['minor errors'] += 1
				elif actual_category == 2 and predicted_category == 0:
					qtapp.error_counts['very major errors'] += 1
				elif actual_category == 0 and predicted_category == 2:
					qtapp.error_counts['major errors'] += 1
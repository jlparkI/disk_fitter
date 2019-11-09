import pandas as pd, numpy as np, math

#Our microbiology team requested a specific format for export data...as shown below.
def export_results(qtapp, filename):
	try:
		output_data = open(filename, 'w+')
		output_data.write('Proposed breakpoints,# Strains,Very Major Errors,Major Errors, Minor Errors\n')
		xbins = np.asarray([0.016,0.03,0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,256])
		diskcutoffS = float(qtapp.diskcutoffS)
		diskcutoffR = float(qtapp.diskcutoffR)
		cutoffs_and_breakpoints = [float(current_value) for current_value in [qtapp.diskcutoffS, qtapp.diskcutoffR]]
		if qtapp.is_mic_vs_mic:
			for i in range(1, len(xbins)):
				#It is VERY important that the disk cutoffs from the fitting procedure are rounded to the
				#nearest integer in an appropriate way (i.e. with >= or > chosen appropriately). See
				#also line 21-27. THe logistic regression and decision tree methods obviously return
				#real numbers so in this function we ensure we are exporting a useful cutoff instead.
				if cutoffs_and_breakpoints[0] > xbins[i-1] and cutoffs_and_breakpoints[0] < xbins[i]:
					diskcutoffS = xbins[i]
				if cutoffs_and_breakpoints[1] > xbins[i-1] and cutoffs_and_breakpoints[1] < xbins[i]:
					diskcutoffR = xbins[i-1]
		bkpt1_sign = '<'
		bkpt2_sign = '>'
		if qtapp.is_mic_vs_mic == False:
			if math.ceil(diskcutoffS) == round(diskcutoffS) and diskcutoffS != round(diskcutoffS):
				bkpt2_sign = '>='
			if math.floor(diskcutoffR) == round(diskcutoffR) and diskcutoffR != round(diskcutoffR):
				bkpt1_sign = '<='
			diskcutoffS = round(diskcutoffS)
			diskcutoffR = round(diskcutoffR)
		output_data.write('Resistant: zone %s%s    Susceptible: zone %s%s,'%(bkpt1_sign, str(diskcutoffR),
										bkpt2_sign, str(diskcutoffS) ) )
		output_data.write('%s,%s,%s,%s\n'%(str(qtapp.current_dataset.shape[0]), str(qtapp.error_counts['very major errors']),
					str(qtapp.error_counts['major errors']), str(qtapp.error_counts['minor errors'])) )

		#Our microbiology team wanted to have a text-based histogram. The code below writes a text-based
		#histogram into the csv file.
		output_data.write('\n\n\nThe chart below plots disk zone (on x) vs mic (on y)\n')
		disk_values = [z for z in np.unique(qtapp.current_dataset['disks'].values)]
		mics = [z for z in np.unique(qtapp.current_dataset['mics'].values)]
		disk_zone_tracker = np.zeros((len(mics), len(disk_values)))
		export_data = qtapp.current_dataset.values
		export_data[:,0] = np.clip(export_data[:,0], a_min = 0.016, a_max = 256)
		for i in range(0, export_data.shape[0]):
			disk_zone_tracker[mics.index(export_data[i,0]), disk_values.index(export_data[i,1])] += 1
		for i in range(0, disk_zone_tracker.shape[0]):
			output_line = [str(mics[i])]
			for j in range(0, len(disk_zone_tracker[i,:])):
				if disk_zone_tracker[i,j] > 0:
					output_line.append(str(disk_zone_tracker[i,j]))
				else:
					output_line.append('')
			output_data.write(','.join(output_line))
			output_data.write('\n')
		output_data.write(',' + ','.join([str(z) for z in disk_values]))
		output_data.close()
	except:
		return ("The data could not be exported. The program is trying to write to a file called '%s'. Make sure that you don't "
			"have a file by this name already open."%filename)
	return '0'
		

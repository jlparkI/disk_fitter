import pandas as pd, numpy as np, math


def export_results(qtapp, filename):
	try:
		output_data = open(filename, 'w+')
		output_data.write('Proposed breakpoints,# Strains,Very Major Errors,Major Errors, Minor Errors\n')
		diskcutoffS = float(qtapp.diskcutoffS)
		diskcutoffR = float(qtapp.diskcutoffR)
		bkpt1_sign = '<'
		bkpt2_sign = '>'
		if math.ceil(diskcutoffS) == round(diskcutoffS):
			bkpt2_sign = '>='
		if math.floor(diskcutoffR) == round(diskcutoffR):
			bkpt1_sign = '<='
		output_data.write('Resistant: zone %s%s    Susceptible: zone %s%s,'%(bkpt1_sign, str(round(diskcutoffR)),
										bkpt2_sign, str(round(diskcutoffS)) ) )
		output_data.write('%s,%s,%s,%s\n'%(str(qtapp.current_dataset.shape[0]), str(qtapp.error_counts['very major errors']),
					str(qtapp.error_counts['major errors']), str(qtapp.error_counts['minor errors'])) )

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
		
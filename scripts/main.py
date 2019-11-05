from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QVBoxLayout, QMainWindow, QMessageBox, QFileDialog, QLineEdit, QHBoxLayout, QCheckBox, QComboBox
from PyQt5.QtGui import QPixmap
import pandas as pd, numpy as np, plotting, modeler, data_export, os
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class disk_masher(QMainWindow):

	def __init__(self):
		super().__init__()
		self.current_dataset = pd.DataFrame()
		self.use_logistic_regression = True
		self.miccutoffS = 4
		self.miccutoffR = 16
		self.diskcutoffS = 32
		self.diskcutoffR = 12
		self.use_user_defined_disk_cutoffs = False
		self.determine_if_mic_vs_mic = False
		self.is_mic_vs_mic = False
		self.confusion_matrix = np.zeros((3,3))
		self.error_counts = {'very major errors':0, 'major errors':0, 'minor errors':0}

		self.colormap_type = 'continuous_blue'
		self.central_plot = Figure(figsize=(12,5))
		self.canvas = FigureCanvas(self.central_plot)
		self.toolbar = NavigationToolbar(self.canvas, self)
		
		self.setWindowTitle('Disk Masher 1.0')
		self.central_widget = QWidget()
		self.setCentralWidget(self.central_widget)
		mainlayout = QVBoxLayout(self.central_widget)
		horiz_layout_1 = QHBoxLayout()
		horiz_layout_2 = QHBoxLayout()
		horiz_layout_3 = QHBoxLayout()
		horiz_layout_4 = QHBoxLayout()
		horiz_layout_5 = QHBoxLayout()
		horiz_layout_6 = QHBoxLayout()

		mainlayout.addWidget(self.toolbar)
		mainlayout.addWidget(self.canvas)

		###Three main buttons, one to import data, one to fit and one to export results.

		import_button = QPushButton('Import data')
		mainlayout.addWidget(import_button)
		import_button.clicked.connect(self.load_file)

		fit_button = QPushButton('Fit/Plot data')
		fit_button.resize(100, fit_button.height())
		mainlayout.addWidget(fit_button)
		fit_button.clicked.connect(self.fit_data)

		export_button = QPushButton('Export results')
		mainlayout.addWidget(export_button)
		export_button.clicked.connect(self.export_results)

		###Now add text boxes user can add to modify the breakpoints. These are stacked next to each other

		self.susceptibility_label = QLabel('Susceptibility breakpoint (<, mg/L)')
		horiz_layout_1.addWidget(self.susceptibility_label)
		self.resistance_label = QLabel('Resistance breakpoint (>=, mg/L)')
		horiz_layout_1.addWidget(self.resistance_label)

		self.susceptibility_breakpoint = QLineEdit()
		self.susceptibility_breakpoint.setText('4')
		self.susceptibility_breakpoint.textChanged.connect(self.update_s_cutoff)
		horiz_layout_2.addWidget(self.susceptibility_breakpoint)

		self.resistance_breakpoint = QLineEdit()
		self.resistance_breakpoint.setText('16')
		self.resistance_breakpoint.textChanged.connect(self.update_r_cutoff)
		horiz_layout_2.addWidget(self.resistance_breakpoint)
		
		self.regression_type = QComboBox()
		self.regression_type.addItem("Logistic Regression")
		self.regression_type.addItem("Decision Tree Classifier")
		self.regression_type.activated[str].connect(self.change_regression_type)
		horiz_layout_3.addWidget(self.regression_type)

		self.color_palette = QComboBox()
		self.color_palette.addItem("Continuous Blue Palette")
		self.color_palette.addItem("Discrete Blue Palette")
		self.color_palette.addItem("Continuous Green Palette")
		self.color_palette.activated[str].connect(self.change_color_palette)
		horiz_layout_3.addWidget(self.color_palette)


		##Now add text boxes user can add to modify the disk cutoffs if desired, after a checkbox to indicate whether or not manual cutoffs should override.
		self.manual_override = QCheckBox('Use user-specified cutoffs and override fitting procedure', self)
		self.manual_override.stateChanged.connect(self.manual_fit_button)
		horiz_layout_4.addWidget(self.manual_override)

		self.mic_vs_mic_checkbox = QCheckBox('Recognize MIC vs MIC data and handle differently from MIC vs disk data', self)
		self.mic_vs_mic_checkbox.stateChanged.connect(self.mic_vs_mic_handling)
		horiz_layout_4.addWidget(self.mic_vs_mic_checkbox)

		self.diskS_label = QLabel('Susceptibility disk cutoff(>, mm)')
		horiz_layout_5.addWidget(self.diskS_label)
		self.diskR_label = QLabel('Resistance disk cutoff (<, mm)')
		horiz_layout_5.addWidget(self.diskR_label)

		self.diskS_breakpoint = QLineEdit()
		self.diskS_breakpoint.setText('12')
		self.diskS_breakpoint.textChanged.connect(self.diskS_manual_cutoff)
		horiz_layout_6.addWidget(self.diskS_breakpoint)

		self.diskR_breakpoint = QLineEdit()
		self.diskR_breakpoint.setText('32')
		self.diskR_breakpoint.textChanged.connect(self.diskR_manual_cutoff)
		horiz_layout_6.addWidget(self.diskR_breakpoint)
		

		mainlayout.addLayout(horiz_layout_1)
		mainlayout.addLayout(horiz_layout_2)
		mainlayout.addLayout(horiz_layout_3)
		mainlayout.addLayout(horiz_layout_4)
		mainlayout.addLayout(horiz_layout_5)
		mainlayout.addLayout(horiz_layout_6)
		self.show()

	def change_regression_type(self, text):
		if text == 'Logistic Regression':
			self.use_logistic_regression = True
		elif text == 'Decision Tree Classifier':
			self.use_logistic_regression = False

	def change_color_palette(self, text):
		if text == 'Continuous Blue Palette':
			self.colormap_type = 'continuous_blue'
		elif text == 'Discrete Blue Palette':
			self.colormap_type = 'discrete_blue'
		elif text == 'Continuous Green Palette':
			self.colormap_type = 'continuous_green'

	def load_file(self):
		options = QFileDialog.Options()
		filename, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()",
						"","CSV Files (*.csv);;", options=options)
		if filename:
			try:
				self.current_dataset = pd.read_csv(filename, header=None)
				self.current_dataset.columns = ['mics', 'disks']
			except:
				self.sudden_death('There was an error opening the selected file! Clearly you have made a mistake. '
					'One reason why this may have occurred '
					'is if you selected a non-csv file or a file with more than two columns. '
					'Remember your instructions!')
			if len(self.current_dataset.columns) > 2:
				self.sudden_death('There was an error opening the selected file! Clearly you have made a mistake. '
					'One reason why this may have occurred '
					'is if you selected a non-csv file or a file with more than two columns. '
					'Remember your instructions!')

	def fit_data(self):
		if len(self.current_dataset.columns) < 2:
			self.sudden_death("You want to fit the data, but you haven't loaded any? Try loading some first. Now there's an idea!")
			return
		data_type = 'disk'
		if self.determine_if_mic_vs_mic:
			data_type, error_code = modeler.determine_data_type(self)
			if error_code != '0':
				self.sudden_death(error_code)
				return
			if data_type == 'mic':
				self.is_mic_vs_mic = True
				self.diskS_label.setText('Susceptibility cutoff (<, mg/L)')
				self.diskR_label.setText('Resistance cutoff (>, mg/L)')
			else:
				self.is_mic_vs_mic = False
				self.diskS_label.setText('Susceptibility disk cutoff(>, mm)')
				self.diskR_label.setText('Resistance disk cutoff (<, mm)')
		if self.use_user_defined_disk_cutoffs == False:
			output_code = modeler.fit_data(self, data_type)
			if output_code != '0':
				self.sudden_death(output_code)
				return
		output_code = plotting.gen_plot(self, data_type)
		if output_code != '0':
			self.sudden_death(output_code)
			return
		self.diskS_breakpoint.setText(str(self.diskcutoffS))
		self.diskR_breakpoint.setText(str(self.diskcutoffR))

	def update_s_cutoff(self, text):
		self.miccutoffS = text

	def update_r_cutoff(self, text):
		self.miccutoffR = text

	def diskS_manual_cutoff(self, text):
		self.diskcutoffS = text

	def diskR_manual_cutoff(self, text):
		self.diskcutoffR = text

	def manual_fit_button(self, state):
		if state == QtCore.Qt.Checked:
			alert = QMessageBox()
			alert.setText("You have selected use of manual cutoffs! This will override the fitting procedure and use the cutoffs you have specified whether "
					"they are reasonable or not. 'Just because you can, doesn't mean you should.'")
			alert.setIconPixmap(QPixmap(os.path.join('img','picture_of_a_microbiologist.jpg')))
			alert.setWindowTitle('Warning!')
			alert.exec_()
			self.use_user_defined_disk_cutoffs = True
		else:
			self.use_user_defined_disk_cutoffs = False

	def mic_vs_mic_handling(self, state):
		if state == QtCore.Qt.Checked:
			alert = QMessageBox()
			alert.setText("The program will now try to recognize MIC vs MIC data based on the distribution of the data and will fit and plot it differently than "
					"it would MIC vs disk data. You may now load files with MIC in column 1 and MIC in column 2.")
			alert.setIconPixmap(QPixmap(os.path.join('img', 'picture_of_a_microbiologist.jpg')))
			alert.setWindowTitle('Warning!')
			alert.exec_()
			self.determine_if_mic_vs_mic = True
		else:
			self.determine_if_mic_vs_mic = False
			self.is_mic_vs_mic = False
			self.diskS_label.setText('Susceptibility disk cutoff(>, mm)')
			self.diskR_label.setText('Resistance disk cutoff (<, mm)')

	def export_results(self):
		if len(self.current_dataset.columns) < 2 or np.sum(self.confusion_matrix) == 0:
			self.sudden_death("You want to export the data, but you haven't loaded any? Try loading some first. Now there's an idea!")
			return
		options = QFileDialog.Options()
		filename, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()",
						"","CSV Files (*.csv);;", options=options)
		if filename:
			error_code = data_export.export_results(self, filename)
			if error_code != '0':
				self.sudden_death(error_code)
				return
			alert = QMessageBox()
			alert.setText('Your results have been exported to a csv file entitled "%s" . Happy disking!'%filename)
			alert.setIconPixmap(QPixmap(os.path.join('img', 'picture_of_a_microbiologist.jpg')))
			alert.setWindowTitle('Success!')
			alert.exec_()

		

	def sudden_death(self, error_message):
		alert = QMessageBox()
		alert.setText(error_message)
		alert.setIconPixmap(QPixmap(os.path.join('img', 'picture_of_a_zombie.jpg')))
		alert.setWindowTitle('Sudden Death')
		alert.exec_()
	

if __name__ == '__main__':
	app = QApplication([])
	alert = QMessageBox()
	alert.setText('Welcome to Disk Masher! Disk Masher accepts data imports in the form of .csv files. The first column '
			'should contain the mic values, the second column should contain the disk zones in mm. Enjoy mashing your disks!')
	alert.setIconPixmap(QPixmap(os.path.join('img', 'picture_of_a_microbiologist.jpg')))
	alert.setWindowTitle('Disk Masher 1.0')
	alert.exec_()
	current_app = disk_masher()
	app.exec_()
	exit()

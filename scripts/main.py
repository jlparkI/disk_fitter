from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QVBoxLayout, QMainWindow, QMessageBox, QFileDialog, QLineEdit, QHBoxLayout, QCheckBox, QComboBox
from PyQt5.QtGui import QPixmap
import pandas as pd, plotting, modeler, data_export, os, model_object
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

#Each instance of the application is an object of class disk_fitter, with all of the user-defined parameters,
#the input data, the current model (object of class model_parameter_set) and the results for export stored as class attributes.
#This is an extremely simple approach adopted because the application is relatively simple and only needs to
#perform a single task. If this were to be expanded to perform additional tasks, adding new classes for
#each model and each input dataset would be helpful.
class disk_fitter(QMainWindow):

  def __init__(self):
    super().__init__()
    self.curr_model = model_object.model_parameter_set()

    self.central_plot = Figure()
    self.canvas = FigureCanvas(self.central_plot)
    self.toolbar = NavigationToolbar(self.canvas, self)
    
    #This next part is fairly straightforward -- we're just building the interface by adding box layouts
    #and adding widgets to each to get the overall layout we want.
    self.setWindowTitle('Disk Fitter 1.0')
    self.central_widget = QWidget()
    self.setCentralWidget(self.central_widget)
    self.resize(950,600)
    mainlayout = QVBoxLayout(self.central_widget)
    main_controls = QHBoxLayout()
    horiz_layouts = [QHBoxLayout() for i in range(0,7)]

    mainlayout.addWidget(self.toolbar)
    mainlayout.addWidget(self.canvas)

    ###Three main buttons, one to import data, one to fit and one to export results.

    import_button = QPushButton('Import data')
    main_controls.addWidget(import_button)
    import_button.clicked.connect(self.load_file)

    fit_button = QPushButton('Fit/Plot data')
    fit_button.setDefault(True)
    fit_button.setAutoDefault(True)
    main_controls.addWidget(fit_button)
    fit_button.clicked.connect(self.fit_data)

    export_button = QPushButton('Export results')
    main_controls.addWidget(export_button)
    export_button.clicked.connect(self.export_results)

    ###Now add text boxes user can add to modify the MIC breakpoints. These are stacked next to each other

    self.susceptibility_label = QLabel('Susceptibility breakpoint (<=, mg/L)')
    horiz_layouts[0].addWidget(self.susceptibility_label)
    self.resistance_label = QLabel('Resistance breakpoint (>=, mg/L)')
    horiz_layouts[0].addWidget(self.resistance_label)

    self.susceptibility_breakpoint = QLineEdit()
    self.susceptibility_breakpoint.setText('4')
    self.susceptibility_breakpoint.textChanged.connect(self.update_s_cutoff)
    horiz_layouts[1].addWidget(self.susceptibility_breakpoint)

    self.resistance_breakpoint = QLineEdit()
    self.resistance_breakpoint.setText('16')
    self.resistance_breakpoint.textChanged.connect(self.update_r_cutoff)
    horiz_layouts[1].addWidget(self.resistance_breakpoint)
    
    #Here's where the user can select the type of model they will use to fit.
    self.regression_type = QComboBox()
    self.regression_type.addItem("min gini impurity")
    self.regression_type.activated[str].connect(self.change_regression_type)
    horiz_layouts[2].addWidget(self.regression_type)

    self.color_palette = QComboBox()
    self.color_palette.addItem("Christmas Colors")
    self.color_palette.addItem("Blue Palette")
    self.color_palette.addItem("Green Palette")
    self.color_palette.activated[str].connect(self.change_color_palette)
    horiz_layouts[2].addWidget(self.color_palette)


    ##Now add text boxes user can add to modify the disk cutoffs if desired, after a checkbox to indicate whether or not manual cutoffs should override.
    self.manual_override = QCheckBox('Use user-specified cutoffs and override fitting procedure', self)
    self.manual_override.stateChanged.connect(self.manual_fit_button)
    horiz_layouts[3].addWidget(self.manual_override)

    self.mic_vs_mic_checkbox = QCheckBox('Recognize MIC vs MIC data and handle differently from MIC vs disk data', self)
    self.mic_vs_mic_checkbox.stateChanged.connect(self.mic_vs_mic_handling)
    horiz_layouts[3].addWidget(self.mic_vs_mic_checkbox)

    self.diskR_label = QLabel('Resistance disk cutoff (<=, mm)')
    horiz_layouts[4].addWidget(self.diskR_label)
    self.diskS_label = QLabel('Susceptibility disk cutoff(>=, mm)')
    horiz_layouts[4].addWidget(self.diskS_label)
    
    self.diskR_breakpoint = QLineEdit()
    self.diskR_breakpoint.setText('32')
    self.diskR_breakpoint.textChanged.connect(self.diskR_manual_cutoff)
    horiz_layouts[5].addWidget(self.diskR_breakpoint)
    self.diskS_breakpoint = QLineEdit()
    self.diskS_breakpoint.setText('12')
    self.diskS_breakpoint.textChanged.connect(self.diskS_manual_cutoff)
    horiz_layouts[5].addWidget(self.diskS_breakpoint)

    self.strain_name_label = QLabel('Strain Name:')
    horiz_layouts[6].addWidget(self.strain_name_label)
    self.strain_name_input = QLineEdit()
    self.strain_name_input.setText(self.curr_model.strain_name)
    self.strain_name_input.textChanged.connect(self.strain_name_change)
    horiz_layouts[6].addWidget(self.strain_name_input)

    mainlayout.addLayout(main_controls)
    for horiz_layout in horiz_layouts:
        mainlayout.addLayout(horiz_layout)
    self.show()
    
  def strain_name_change(self, text):
    self.curr_model.strain_name = text

  #Currently there is only one model type available; this function
  #is here in case we ever add another...
  def change_regression_type(self, text):
    if text == 'min gini model':
      self.curr_model.model_type = 'mgm'

  def change_color_palette(self, text):
    if text == 'Blue Palette':
      self.curr_model.colormap_type = 'continuous_blue'
    elif text == 'Christmas Colors':
      self.curr_model.colormap_type = 'christmas_colors'
    elif text == 'Green Palette':
      self.curr_model.colormap_type = 'continuous_green'

      #If loading a file, need to check to make sure it contains correctly formatted data
      #that pandas can read,
      #otherwise do some error handling. The sudden death function (defined later) prints
      #a message box with the error message passed to it and is used for error handling
      #throughout.
  def load_file(self):
    options = QFileDialog.Options()
    filename, _ = QFileDialog.getOpenFileName(self,"Load File",
            "","CSV Files (*.csv);;", options=options)
    if filename:
      try:
        self.curr_model.current_dataset = pd.read_csv(filename, header=None)
        self.curr_model.current_dataset.columns = ['mics', 'disks']
      except:
        self.sudden_death('There was an error opening the selected file! Clearly you have made a mistake. '
          'One reason why this may have occurred '
          'is if you selected a non-csv file or a file with more than two columns. '
          'Remember your instructions!')
      if len(self.curr_model.current_dataset.columns) > 2:
        self.sudden_death('There was an error opening the selected file! Clearly you have made a mistake. '
          'One reason why this may have occurred '
          'is if you selected a non-csv file or a file with more than two columns. '
          'Remember your instructions!')

  def fit_data(self):
    if len(self.curr_model.current_dataset.columns) < 2:
      self.sudden_death("You want to fit the data, but you haven't loaded any? Try loading some first. Now there's an idea!")
      return
    #We assume the user is importing mic vs disk data unless they checked the data could be MIC vs MIC flag. If so,
    #call determine_data_type to figure out whether this is MIC vs disk or MIC vs MIC data.
    data_type = 'disk'
    if self.curr_model.determine_if_mic_vs_mic:
      data_type, error_code = modeler.determine_data_type(self.curr_model)
      if error_code != '0':
        self.sudden_death(error_code)
        return
      if data_type == 'mic':
        self.curr_model.is_mic_vs_mic = True
        self.diskS_label.setText('Susceptibility cutoff (<=, mg/L)')
        self.diskR_label.setText('Resistance cutoff (>=, mg/L)')
      else:
        self.curr_model.is_mic_vs_mic = False
        self.diskS_label.setText('Susceptibility disk cutoff(>=, mm)')
        self.diskR_label.setText('Resistance disk cutoff (<=, mm)')
    #If the user is NOT specifying their own cutoffs, fit the data by passing the model (object of class model_parameter_set) to the fit_data function in the
#modeler.py file.
    if self.curr_model.use_user_defined_disk_cutoffs == False:
      output_code = modeler.fit_data(self.curr_model, data_type)
      if output_code == '0':
        pass
      #THe end user asked to know whether it was possible to get an optimal fit
      #using different window sizes, hence this.
      elif output_code.startswith('!'):
        window_sizes = output_code.split('!, ')[1]
        self.non_fatal_message('It was possible to fit the data using intermediate disk zone sizes of '
                               '%s mm. The program has defaulted to the smallest window size possible.'
                               %window_sizes)
      else:
        self.sudden_death(output_code)
        return
    #Plot the data regardless of whether we fitted it or used their cutoffs.
    output_code = plotting.gen_plot(self, data_type)
    if output_code != '0':
      self.sudden_death(output_code)
      return
    #Update the disk cutoff boxes to use the updated cutoffs from fitting (if the data was refit).
    self.diskS_breakpoint.setText(str(self.curr_model.diskcutoffS))
    self.diskR_breakpoint.setText(str(self.curr_model.diskcutoffR))
    self.curr_model.diskcutoffR = float(self.curr_model.diskcutoffR)
    self.curr_model.diskcutoffS = float(self.curr_model.diskcutoffS)

  def update_s_cutoff(self, text):
    try:
      self.curr_model.miccutoffS = float(text)
    except:
      pass

  def update_r_cutoff(self, text):
    try:
      self.curr_model.miccutoffR = float(text)
    except:
      pass

  def diskS_manual_cutoff(self, text):
    try:
      self.curr_model.diskcutoffS = float(text)
    except:
      pass

  def diskR_manual_cutoff(self, text):
    try:
      self.curr_model.diskcutoffR = float(text)
    except:
      pass

  def manual_fit_button(self, state):
    if state == QtCore.Qt.Checked:
      self.non_fatal_message("You have selected use of manual cutoffs! This will override the fitting procedure and use the cutoffs you have specified whether "
          "they are reasonable or not. 'Just because you can, doesn't mean you should.'")
      self.curr_model.use_user_defined_disk_cutoffs = True
    else:
      self.curr_model.use_user_defined_disk_cutoffs = False

  def mic_vs_mic_handling(self, state):
    if state == QtCore.Qt.Checked:
      self.non_fatal_message("The program will now try to recognize MIC vs MIC data based on the distribution of the "
                    "data and will fit and plot it differently than "
          "it would MIC vs disk data. You may now load files with MIC in column 1 and MIC in column 2.")
      self.curr_model.determine_if_mic_vs_mic = True
    else:
      self.curr_model.determine_if_mic_vs_mic = False
      self.curr_model.is_mic_vs_mic = False
      self.diskS_label.setText('Susceptibility disk cutoff(>=, mm)')
      self.diskR_label.setText('Resistance disk cutoff (<=, mm)')

  #The end user wanted the ability to output to a csv file with the same data
  #as contained in the plot but in a text-based histogram.
  def export_results(self):
    if len(self.curr_model.current_dataset.columns) < 2:
      self.sudden_death("You want to export the data, but you haven't loaded any? Try loading some first. Now there's an idea!")
      return
    options = QFileDialog.Options()
    filename, _ = QFileDialog.getSaveFileName(self,"Save File",
            "","CSV Files (*.csv);;", options=options)
    if filename:
      error_code = data_export.export_results(self.curr_model, filename)
      if error_code != '0':
        self.sudden_death(error_code)
        return
      self.non_fatal_message('Your results have been exported to a csv file entitled "%s" .'%filename)
    
  #This function prints out the error message passed to it in a zombie-themed
  #message box.
  def sudden_death(self, error_message):
    alert = QMessageBox()
    alert.setText(error_message)
    alert.setIconPixmap(QPixmap(os.path.join('img', 'picture_of_a_zombie.jpg')))
    alert.setWindowTitle('Sudden Death')
    alert.exec_()

  #This function prints out a non-fatal message passed to it in a microbiologist
  #themed text box.
  def non_fatal_message(self, message):
    alert = QMessageBox()
    alert.setText(message)
    alert.setIconPixmap(QPixmap(os.path.join('img', 'picture_of_a_microbiologist.jpg')))
    alert.setWindowTitle('Please note')
    alert.exec_()
  
#Entry point. When script runs, create an object of class disk_fitter after
#giving the user some preliminary information.
if __name__ == '__main__':
  app = QApplication([])
  alert = QMessageBox()
  alert.setText('Welcome to Disk Fitter! Disk Fitter accepts data imports in the form of .csv files. The first column '
      'should contain the mic values, the second column should contain the disk zones in mm. Enjoy!')
  alert.setIconPixmap(QPixmap(os.path.join('img', 'picture_of_a_microbiologist.jpg')))
  alert.setWindowTitle('Disk Fitter 1.0')
  alert.exec_()
  current_app = disk_fitter()
  app.exec_()
  exit()

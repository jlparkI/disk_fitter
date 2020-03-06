from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QPixmap
import os


#The intro message the user gets when starting the program.
def display_start_message():
  alert = QMessageBox()
  alert.setText('Welcome to Disk Fitter! Disk Fitter accepts data imports in the form of .csv files. The first column '
      'should contain the mic values, the second column should contain the disk zones in mm. Enjoy!')
  alert.setIconPixmap(QPixmap(os.path.join('img', 'picture_of_a_microbiologist.jpg')))
  alert.setWindowTitle('Disk Fitter 1.0')
  alert.exec_()

#This function prints out the error message passed to it in a zombie-themed
#message box.
def sudden_death(error_message):
  alert = QMessageBox()
  alert.setText(error_message)
  alert.setIconPixmap(QPixmap(os.path.join('img', 'picture_of_a_zombie.jpg')))
  alert.setWindowTitle('Sudden Death')
  alert.exec_()

#This function prints out a non-fatal message passed to it in a microbiologist
#themed text box.
def non_fatal_message(message):
  alert = QMessageBox()
  alert.setText(message)
  alert.setIconPixmap(QPixmap(os.path.join('img', 'picture_of_a_microbiologist.jpg')))
  alert.setWindowTitle('Please note')
  alert.exec_()

# coding=utf-8
# ui20241203
import os
import shutil

from winUI import Ui_MainWindow
import sys
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QMessageBox, QMainWindow, QApplication, QHeaderView
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QTableWidgetItem, QInputDialog
from PyQt5.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QWaitCondition, QMutex, pyqtSlot

from PyQt5.QtCore import QObject, pyqtSignal
import sys
import os
from ols_fetch_from_github.main_workflow import SBOWorkflowManager
from sboannotator.upload_model import copy_model_to_customer_dir, convert_to_relative_path
from sboannotator.config_manager import user_change_database_configuration, get_database_order


# Thread pool for checking updates

class check_updates_thread(QThread):
    def __init__(self, main_win):  # Constructor method
        super().__init__()  # Run parent class constructor method
        self.main_win = main_win

    def run(self):
        self.main_win.workflow_manager.run_workflow()


# Thread pool for running
class run_sboannotator_thread(QThread):
    # Define a custom signal for sending messages to the main thread
    append_signal = pyqtSignal(str)
    data_signal = pyqtSignal(dict, tuple)

    def __init__(self, mode_file):
        super().__init__()
        self.mode_file = mode_file

    def run(self):

        # cwd environment
        sboannotator_path = os.path.join(os.path.dirname(__file__), 'sboannotator')

        # Save current working directory
        original_cwd = os.getcwd()
        try:
            # Change current working directory to sboannotator_path
            os.chdir(sboannotator_path)

            # Add sboannotator directory to Python path
            sys.path.insert(0, sboannotator_path)

            # Import and run SBOannotator's main function
            from sboannotator.__main__ import run_sboannotator

            data, output_list = run_sboannotator(self.mode_file, self.append_signal)
            self.data_signal.emit(data, output_list)

        finally:
            # Restore original working directory
            os.chdir(original_cwd)


# Thread pool for running
class run_llm_thread_1(QThread):
    # Define a custom signal for sending messages to the main thread
    append_signal = pyqtSignal(str)
    data_signal = pyqtSignal(dict, str)
    before_signal = pyqtSignal(tuple)

    def __init__(self, output_file, parent_sbo_file_output_file):
        super().__init__()
        self.output_file = output_file
        self.parent_sbo_file_output_file = parent_sbo_file_output_file

    def run(self):

        # cwd environment
        sboannotator_path = os.path.join(os.path.dirname(__file__), 'sboannotator')

        # Save current working directory
        original_cwd = os.getcwd()
        try:
            # Change current working directory to sboannotator_path
            os.chdir(sboannotator_path)

            # Add sboannotator directory to Python path
            sys.path.insert(0, sboannotator_path)

            # Import and run SBOannotator's main function
            from sboannotator.__main__ import run_llm_script_1

            leave_recommended_data, text = run_llm_script_1(self.output_file, self.parent_sbo_file_output_file,
                                                            self.append_signal, self.before_signal)
            # Return information
            self.data_signal.emit(leave_recommended_data, text)

        finally:
            # Restore original working directory
            os.chdir(original_cwd)


# Thread pool for running
class run_llm_thread_2(QThread):
    # Define a custom signal for sending messages to the main thread
    append_signal = pyqtSignal(str)
    data_signal = pyqtSignal(str)
    insert_table = pyqtSignal(tuple)
    after_signal = pyqtSignal(tuple)

    def __init__(self, selected_recommendations, recommended_text, output_file):
        super().__init__()
        self.selected_recommendations = selected_recommendations
        self.recommended_text = recommended_text
        self.output_file = output_file

    def run(self):

        # cwd environment
        sboannotator_path = os.path.join(os.path.dirname(__file__), 'sboannotator')

        # Save current working directory
        original_cwd = os.getcwd()
        try:
            # Change current working directory to sboannotator_path
            os.chdir(sboannotator_path)

            # Add sboannotator directory to Python path
            sys.path.insert(0, sboannotator_path)

            # Import and run SBOannotator's main function
            from sboannotator.__main__ import run_llm_script_2

            output_file = run_llm_script_2(self.selected_recommendations, self.recommended_text, self.output_file,
                                           self.append_signal, self.insert_table, self.after_signal)
            # Return information
            self.data_signal.emit(output_file)

        finally:
            # Restore original working directory
            os.chdir(original_cwd)


class change_database_configuration(QThread):
    def __init__(self, communicator):  # Constructor method
        super().__init__()  # Run parent class constructor method
        self.communicator = communicator

    def run(self):
        user_change_database_configuration(self.communicator)
        print("Execution completed")


class Communicate(QObject):
    # Define a signal for requesting user input
    request_input = pyqtSignal(str, str, str)  # title, prompt message, dialog type
    # Define a signal for returning user input results
    input_result = pyqtSignal(str)

    append_text = pyqtSignal(str)
    download_file = pyqtSignal(str)
    append_text_database = pyqtSignal(str)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):  # Constructor method
        super(MainWindow, self).__init__()  # Run parent class constructor method
        self.setupUi(self)
        # Initialize interface
        self.init_ui()
        # Initialize table
        self.init_table_widget()
        # Select xml
        self.pushButton_choose_model.clicked.connect(self.upload_model)
        # Execute llm
        self.pushButton_LLM.clicked.connect(self.run_llm_script)
        # Cancel llm
        self.pushButton_cancel.clicked.connect(self.cancel_llm_script)
        # Accept all
        self.pushButton_all_adopted.clicked.connect(self.recommend_script)
        # Reject all
        self.pushButton_reject_all.clicked.connect(self.recommend_script)
        # Review
        self.pushButton_review.clicked.connect(self.recommend_script)
        # Accept
        self.pushButton_y.clicked.connect(self.choose_review_script)
        # Reject
        self.pushButton_n.clicked.connect(self.choose_review_script)
        # Exit
        self.pushButton_exit.clicked.connect(self.choose_review_script)
        # Download button
        self.pushButton_down_1.clicked.connect(self.download_1)
        # Download button
        self.pushButton_down_2.clicked.connect(self.download_2)
        # Enter SBOannotator
        self.pushButton.clicked.connect(self.run_sboannotator)
        self.pushButton_sbo_down.clicked.connect(self.download_3)
        # Model path
        self.model_path = None
        # Download file path
        self.output_file = None
        self.abs_output_file = None
        self.abs_output_file_2 = None
        self.sbo_file = None
        # SBO model
        self.parent_sbo_file_output_file = None
        # Review index
        self.review_index = 0
        self.recommended_data = {}
        self.selected_recommendations = {}
        self.recommended_text = ""

        # 1. Fetch SBO files
        self.fetch_sbo_files()

    # Interface initialization
    def init_ui(self):
        self.tableWidget_enhanced_After.setRowCount(0)
        self.tableWidget_enhanced_Before.setRowCount(0)
        self.tableWidget_llm_Before.setRowCount(0)
        self.tableWidget_llm_After.setRowCount(0)
        self.tableWidget_sbo.setRowCount(0)
        self.textEdit_run_1.clear()
        self.textEdit_run_2.clear()
        self.pushButton_choose_model.setEnabled(True)
        self.pushButton_sbo_down.setEnabled(False)
        self.pushButton_LLM.setEnabled(False)
        self.pushButton_cancel.setEnabled(False)
        self.pushButton_all_adopted.setEnabled(False)
        self.pushButton_reject_all.setEnabled(False)
        self.pushButton_review.setEnabled(False)
        self.review_widget.setEnabled(False)
        self.label_review_6.setText("[0/0] Reaction: None")
        self.label_review_1.setText("None")
        self.label_review_2.setText("None")
        self.label_review_3.setText("None")
        self.label_review_4.setText("None")
        self.label_review_5.setText("None")

    # Table initialization
    def init_table_widget(self):
        for _table in [self.tableWidget_llm_Before, self.tableWidget_llm_After, self.tableWidget_sbo,
                       self.tableWidget_enhanced_Before, self.tableWidget_enhanced_After]:
            """Traditional table"""
            _table.setColumnWidth(0, 120)
            _table.setColumnWidth(1, 120)

            # Set the last two columns to auto stretch
            _table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    """1. Fetch SBO files"""

    def fetch_sbo_files(self):
        # 创建通信器
        self.communicator = Communicate()
        # 连接请求输入的信号到处理方法
        self.communicator.request_input.connect(self.show_input_dialog)
        self.communicator.append_text.connect(lambda text: self.textEdit.append(text))
        self.communicator.append_text_database.connect(lambda text: self.textEdit_database.append(text))
        self.communicator.download_file.connect(self.sbo_download)
        # 实例化工作流管理器，传入通信器
        self.workflow_manager = SBOWorkflowManager(self.communicator)
        self.thread = check_updates_thread(self)
        self.thread.finished.connect(lambda :self.pushButton.setEnabled(True))
        self.thread.start()

    """2. Run SBOannotator"""

    def run_sboannotator(self):
        QMessageBox.information(self, 'Notice', 'About to enter SBO annotator')
        self.tabWidget.setCurrentIndex(1)

    # 2.1 Upload model
    def upload_model(self):
        # File filter settings
        file_filters = (
            "XML files (*.xml);;"
        )

        file_path, selected_filter = QFileDialog.getOpenFileName(
            self,
            "Select XML file",
            "",  # Initial directory empty (use system default)
            file_filters
        )

        if file_path and os.path.isfile(file_path):
            self.lineEdit_model_path.setText(file_path)
            local_model_path = copy_model_to_customer_dir(file_path)
            # Model path
            model_path = convert_to_relative_path(local_model_path)
            self.model_path = model_path
            QMessageBox.information(self, 'Notice', f"Copied model to Customer_Models directory: {model_path}")
            self.stackedWidget.setCurrentIndex(1)
            # Modify database Configuration
            self.modify_database()

    # 2.2 Modify database Configuration
    def modify_database(self):
        # Load a fresh model for enhanced annotator to ensure fair comparison
        current_order = get_database_order()
        self.textEdit_database.append('Do you want to modify database configuration before annotation?')
        self.textEdit_database.append(f'Current database order: {current_order}')
        # Show yes/no dialog box
        reply = QMessageBox.question(
            self,
            "Please select",
            "Modify database order? (y/n): ",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.thread = change_database_configuration(self.communicator)
            # Connect thread finished signal to custom slot function
            self.thread.finished.connect(self.modify_database_finished)
            self.thread.start()
        else:
            self.modify_database_finished()

    @pyqtSlot()
    def modify_database_finished(self):
        QMessageBox.information(self, 'Notice', 'Start SBO annotator')
        self.stackedWidget.setCurrentIndex(0)
        self.start_script()

    # 2.3 Execute main task
    def start_script(self):
        # Clear
        self.init_ui()
        # Status message
        self.statusbar.showMessage("Running")
        # Multi-threading
        self.thread = run_sboannotator_thread(self.model_path)
        self.thread.append_signal.connect(lambda x: self.textEdit_run_1.append(x))
        self.thread.data_signal.connect(self.show_annotations)
        self.thread.start()

    # Show enhanced Before and After tables
    def show_annotations(self, data, output_list):
        # Model path
        self.output_file, self.parent_sbo_file_output_file, self.abs_output_file = output_list

        names = ["Reactions", "Metabolites", "Genes", "Compartments"]

        for idx, name in enumerate(names):
            for index, (key, value) in enumerate(data['Before'][idx].items()):
                self.tableWidget_enhanced_Before.insertRow(index)
                # Class
                self.tableWidget_enhanced_Before.setItem(index, 0, QTableWidgetItem(f'{name}{index + 1}'))

                # SBO_id
                self.tableWidget_enhanced_Before.setItem(index, 1, QTableWidgetItem(str(key)))

                # Before
                self.tableWidget_enhanced_Before.setItem(index, 2, QTableWidgetItem(str(value)))

        for idx, name in enumerate(names):
            for index, (key, value) in enumerate(data['After'][idx].items()):
                self.tableWidget_enhanced_After.insertRow(index)
                # Class
                self.tableWidget_enhanced_After.setItem(index, 0, QTableWidgetItem(f'{name}{index + 1}'))

                # SBO_id
                self.tableWidget_enhanced_After.setItem(index, 1, QTableWidgetItem(str(key)))

                # Before
                self.tableWidget_enhanced_After.setItem(index, 2, QTableWidgetItem(str(value)))

        # Status message
        self.statusbar.showMessage("Please choose whether to use LLM for SBO annotation of EC reactions")
        self.pushButton_LLM.setEnabled(True)
        self.pushButton_cancel.setEnabled(True)

    # Execute LLM annotation
    def run_llm_script(self):
        self.pushButton_LLM.setEnabled(False)
        self.pushButton_cancel.setEnabled(False)
        self.statusbar.showMessage("Using SBOModel for SBO recommendations...")
        self.thread = run_llm_thread_1(self.output_file, self.parent_sbo_file_output_file)
        self.thread.data_signal.connect(self.ask_is_recommend)
        self.thread.append_signal.connect(lambda x: self.textEdit_run_2.append(x))
        self.thread.before_signal.connect(self.show_before_table)
        self.thread.start()

    # Do not execute LLM annotation, end process
    def cancel_llm_script(self):
        # Disable
        self.pushButton_LLM.setEnabled(False)
        self.pushButton_cancel.setEnabled(False)
        # Restore

        self.pushButton_choose_model.setEnabled(True)
        print(f'✅ SBO annotation model without LLM processing saved at: {self.output_file}')
        self.textEdit_run_2.append(f'✅ SBO annotation model without LLM processing saved at: {self.output_file}')
        # Status message
        self.statusbar.showMessage("Execution completed")

    # Show before table
    def show_before_table(self, before_data):
        names = ["Reactions", "Metabolites", "Genes", "Compartments"]

        for idx, name in enumerate(names):
            for index, (key, value) in enumerate(before_data[idx].items()):
                self.tableWidget_llm_Before.insertRow(index)
                # Class
                self.tableWidget_llm_Before.setItem(index, 0, QTableWidgetItem(f'{name}{index + 1}'))

                # SBO_id
                self.tableWidget_llm_Before.setItem(index, 1, QTableWidgetItem(str(key)))

                # Before
                self.tableWidget_llm_Before.setItem(index, 2, QTableWidgetItem(str(value)))

    # Ask whether to recommend
    def ask_is_recommend(self, recommended_data, text):

        if not recommended_data:
            # print("No available recommendation data")
            self.textEdit_run_2.append("No available recommendation data")
            return
        # First ask whether to accept all
        print(f"\nFound {len(recommended_data)} SBO recommendations")
        self.textEdit_run_2.append(f"\nFound {len(recommended_data)} SBO recommendations")
        self.statusbar.showMessage("Please choose whether to accept all recommendations")
        self.recommended_data = recommended_data
        self.recommended_text = text
        self.pushButton_all_adopted.setEnabled(True)
        self.pushButton_reject_all.setEnabled(True)
        self.pushButton_review.setEnabled(True)

    def recommend_script(self):
        sender = self.sender()
        # Disable
        self.pushButton_all_adopted.setEnabled(False)
        self.pushButton_review.setEnabled(False)
        self.pushButton_reject_all.setEnabled(False)

        if sender == self.pushButton_all_adopted:
            self.selected_recommendations = {k: v.copy() for k, v in self.recommended_data.items()}


        elif sender == self.pushButton_reject_all:
            print("❌ Do not accept any recommendations")
            self.textEdit_run_2.append("❌ Do not accept any recommendations")
            self.selected_recommendations = {}

        elif sender == self.pushButton_review:  # review or other input
            self.review_widget.setEnabled(True)
            print("\nReview recommendations individually:")
            print("-" * 60)
            self.review_index = 0
            # Show review
            self.show_review(self.review_index)
            return
        else:
            self.label_review_6.setText("[0/0] Reaction: None")
            self.label_review_1.setText("None")
            self.label_review_2.setText("None")
            self.label_review_3.setText("None")
            self.label_review_4.setText("None")
            self.label_review_5.setText("None")
            self.review_widget.setEnabled(False)

        self.thread = run_llm_thread_2(self.selected_recommendations, self.recommended_text, self.output_file)
        self.thread.append_signal.connect(lambda x: self.textEdit_run_2.append(x))
        self.thread.insert_table.connect(self.insert_sbo_table)
        self.thread.after_signal.connect(self.show_after_table)
        self.thread.data_signal.connect(self.workflow_complete)
        self.thread.start()

    def apply_selected_recommendations(self):
        """Apply selected recommendations to model without exiting the page"""
        # Disable review controls
        self.label_review_6.setText("[0/0] Reaction: None")
        self.label_review_1.setText("None")
        self.label_review_2.setText("None") 
        self.label_review_3.setText("None")
        self.label_review_4.setText("None")
        self.label_review_5.setText("None")
        self.review_widget.setEnabled(False)
        
        # Apply the selected recommendations to the model
        self.thread = run_llm_thread_2(self.selected_recommendations, self.recommended_text, self.output_file)
        self.thread.append_signal.connect(lambda x: self.textEdit_run_2.append(x))
        self.thread.insert_table.connect(self.insert_sbo_table)
        self.thread.after_signal.connect(self.show_after_table)
        self.thread.data_signal.connect(self.workflow_complete)
        self.thread.start()

    def workflow_complete(self, output):
        self.abs_output_file_2 = output
        self.statusbar.showMessage("Execution completed")
        self.pushButton_choose_model.setEnabled(True)

    def show_after_table(self, after_data):
        names = ["Reactions", "Metabolites", "Genes", "Compartments"]

        for idx, name in enumerate(names):
            for index, (key, value) in enumerate(after_data[idx].items()):
                self.tableWidget_llm_After.insertRow(index)
                # Class
                self.tableWidget_llm_After.setItem(index, 0, QTableWidgetItem(f'{name}{index + 1}'))

                # SBO_id
                self.tableWidget_llm_After.setItem(index, 1, QTableWidgetItem(str(key)))

                # Before
                self.tableWidget_llm_After.setItem(index, 2, QTableWidgetItem(str(value)))

    def insert_sbo_table(self, data):
        reaction, original_sbo, sbo_after = data
        index = self.tableWidget_sbo.rowCount()
        self.tableWidget_sbo.insertRow(index)
        # reaction
        self.tableWidget_sbo.setItem(index, 0, QTableWidgetItem(str(reaction)))
        # SBO_id
        self.tableWidget_sbo.setItem(index, 1, QTableWidgetItem(str(original_sbo)))
        # Before
        self.tableWidget_sbo.setItem(index, 2, QTableWidgetItem(str(sbo_after)))

    def show_review(self, index):

        reaction_id, data = list(self.recommended_data.items())[index]

        self.label_review_6.setText(f"[{index + 1}/{len(self.recommended_data)}] Reaction: {reaction_id}")

        print(f"[{index + 1}/{len(self.recommended_data)}] Reaction: {reaction_id}")
        # Show original SBO information
        original_sbo = data.get('original_sbo', 'None')
        original_sbo_term = data.get('original_sbo_term', '')
        print(f"Original SBO: {original_sbo} - {original_sbo_term}")
        self.label_review_1.setText(f"{original_sbo} - {original_sbo_term}")
        print(f"EC numbers: {data.get('ec_numbers', [])}")
        self.label_review_2.setText(f"{data.get('ec_numbers', [])}")
        print(f"EC text: {data.get('ec_text_to_llm', '')}")
        self.label_review_3.setText(f"{data.get('ec_text_to_llm', '')}")
        print(f"Recommended SBO: {data.get('recommended_sbo_id')} - {data.get('recommend_sbo_term')}")
        self.label_review_4.setText(f"{data.get('recommended_sbo_id')} - {data.get('recommend_sbo_term')}")
        print(f"Recommendation reason: {data.get('recommend_sbo_reason', '')}")
        self.label_review_5.setText(f"{data.get('recommend_sbo_reason', '')}")

    def next_review(self):
        self.review_index += 1
        self.show_review(self.review_index)

    def choose_review_script(self):
        sender = self.sender()
        if sender == self.pushButton_y:
            reaction_id, data = list(self.recommended_data.items())[self.review_index]
            self.selected_recommendations[reaction_id] = data.copy()
            print("✅ Accepted")


        elif sender == self.pushButton_n:
            print("❌ Not accepted")

        else:
            # Exit review early - stop reviewing remaining reactions but apply accepted changes
            print("Exit selection early")
            print(f"\nSummary: Adopted {len(self.selected_recommendations)}/{len(self.recommended_data)} recommendations")
            
            if self.selected_recommendations:
                print("\nAdopted recommendations:")
                for reaction_id, data in self.selected_recommendations.items():
                    print(f"- {reaction_id}: {data.get('original_sbo')} -> {data.get('recommended_sbo_id')}")
            
            # Apply the accepted recommendations to the model
            self.apply_selected_recommendations()
            return


        if self.review_index + 1 == len(self.recommended_data.items()):
            print("Review completed")
            self.recommend_script()
        else:
            self.next_review()

        # else:

    def show_input_dialog(self, title, message, dialog_type):
        """Show input dialog and send result back to workflow manager"""
        if dialog_type == "yesno":
            # Show yes/no dialog box
            reply = QMessageBox.question(
                self,
                title,
                message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            result = "Yes" if reply == QMessageBox.Yes else "No"
        else:
            # Show text input dialog box
            result, ok = QInputDialog.getText(self, title, message)
            if not ok:
                result = ""  # User canceled

        # Send result back to workflow manager
        self.communicator.input_result.emit(result)

    def download_3(self):
        if self.sbo_file is None:
            QMessageBox.information(self, 'Notice', 'Unable to download')
            return
            # Open file dialog to select save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save file", self.sbo_file,
            "All files (*.json);;"
        )
        if file_path:
            # Fix: os.path.samefile() requires both files to exist
            # When user selects a new file name, file_path may not exist yet
            # Original code: if not os.path.samefile(self.sbo_file, file_path):
            # Fixed: Only check samefile if destination exists
            if not (os.path.exists(file_path) and os.path.samefile(self.sbo_file, file_path)):
                shutil.copy(self.sbo_file, file_path)
            QMessageBox.information(self, 'Notice', 'Saved successfully')

    def sbo_download(self, path):
        self.sbo_file = path
        self.pushButton_sbo_down.setEnabled(True)


    def download_1(self):
        if self.abs_output_file is None:
            QMessageBox.information(self, 'Notice', 'Please run Enhanced first')
            return
        # Open file dialog to select save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save file", self.abs_output_file,
            "All files (*.xml);;"
        )
        if file_path:
            # Fix: os.path.samefile() requires both files to exist
            # When user selects a new file name, file_path may not exist yet
            # Original code: if not os.path.samefile(self.abs_output_file, file_path):
            # Fixed: Only check samefile if destination exists
            if not (os.path.exists(file_path) and os.path.samefile(self.abs_output_file, file_path)):
                shutil.copy(self.abs_output_file, file_path)
            QMessageBox.information(self, 'Notice', 'Saved successfully')

    def download_2(self):
        if self.abs_output_file_2 is None:
            QMessageBox.information(self, 'Notice', 'Please run Enhanced first')
            return
        # Open file dialog to select save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save file", self.abs_output_file_2,
            "All files (*.xml);;"
        )
        if file_path:
            # Fix: os.path.samefile() requires both files to exist
            # When user selects a new file name, file_path may not exist yet
            # Original code: if not os.path.samefile(self.abs_output_file_2, file_path):
            # Fixed: Only check samefile if destination exists
            if not (os.path.exists(file_path) and os.path.samefile(self.abs_output_file_2, file_path)):
                shutil.copy(self.abs_output_file_2, file_path)
            QMessageBox.information(self, 'Notice', 'Saved successfully')


if __name__ == '__main__':
    # Resolution adaptation
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

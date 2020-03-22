import pathlib

from PyQt5.QtCore import QDir, Qt
from PyQt5.QtGui import QImage, QPainter, QPalette, QPixmap
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QLabel,
        QMainWindow, QMenu, QMessageBox, QScrollArea, QSizePolicy)
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter

from imageviewer import Ui_MainWindow

class ImageViewer(QMainWindow):
    def __init__(self):
        super(ImageViewer, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.scaleFactor = 0.0

        self.imageLabel = QLabel() 
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)
        self.original_image = None
        self.images = []
        self.img_index = 0


        self.scrollArea = self.ui.scrollArea
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.setCentralWidget(self.scrollArea)

        self.createActions()
        self.createMenus()
        self.connect_buttons()

        #self.setWindowTitle("Image Viewer")
        #self.resize(500, 400)

    def files_with_extension(self, path=".", patterns=("*.jpg", "*.JPG", "*.jpeg", "*.JPEG", "*.png", "*.PNG")):
        """ returns file list that satisfy pattern """
        files = []
        # define the path
        path = pathlib.Path(path)
        for pattern in patterns:
            files.extend(list(sorted(path.glob(pattern))))
        return files           


    def open(self):

#        fileName, _ = QFileDialog.getOpenFileName(self, "Open File",
#                QDir.currentPath())

        dirName = QFileDialog.getExistingDirectory(self, "Select Images Directory",
                QDir.currentPath())

        if dirName:
            self.images = list(map(str, self.files_with_extension(dirName)))
            print(self.images)
            if not self.images :
                QMessageBox.information(self, "Directory Browser",
                        "No images under %s. " % dirName)
                return
            
            self.ui.listWidget_images.addItems(self.images)
            self.ui.listWidget_images.setCurrentRow(0)
            self.open_image(0)
            
    def open_image(self, idx):
        self.img_index = idx
        fileName = self.images[idx]
        image = QImage(fileName)
        if image.isNull():
            QMessageBox.information(self, "Image Viewer",
                    "Cannot load %s." % fileName)
            return

        self.original_image = image
        self.imageLabel.setPixmap(QPixmap.fromImage(image))
        self.scaleFactor = 1.0

        self.fitToWindowAct.setEnabled(True)
        self.updateActions()

        if not self.fitToWindowAct.isChecked():
            self.imageLabel.adjustSize()


    def zoomIn(self):
        if self.zoomInAct.isEnabled():
            self.scaleImage(1.05)

    def zoomOut(self):
        if self.zoomOutAct.isEnabled():
            self.scaleImage(0.9)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()

    def about(self):
        QMessageBox.about(self, "About Image Viewer",
                "<p>The <b>Image Viewer</b> example shows how to combine "
                "QLabel and QScrollArea to display an image. QLabel is "
                "typically used for displaying text, but it can also display "
                "an image. QScrollArea provides a scrolling view around "
                "another widget. If the child widget exceeds the size of the "
                "frame, QScrollArea automatically provides scroll bars.</p>"
                "<p>The example demonstrates how QLabel's ability to scale "
                "its contents (QLabel.scaledContents), and QScrollArea's "
                "ability to automatically resize its contents "
                "(QScrollArea.widgetResizable), can be used to implement "
                "zooming and scaling features.</p>"
                "<p>In addition the example shows how to use QPainter to "
                "print an image.</p>")

    def createActions(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+O",
                triggered=self.open)

        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                triggered=self.close)

        self.zoomInAct = QAction("Zoom &In (5%)", self, shortcut="Ctrl++",
                enabled=False, triggered=self.zoomIn)

        self.zoomOutAct = QAction("Zoom &Out (5%)", self, shortcut="Ctrl+-",
                enabled=False, triggered=self.zoomOut)

        self.normalSizeAct = QAction("&Normal Size", self, shortcut="Ctrl+S",
                enabled=False, triggered=self.normalSize)

        self.fitToWindowAct = QAction("&Fit to Window", self, enabled=False,
                checkable=True, shortcut="Ctrl+F", triggered=self.fitToWindow)

        self.aboutAct = QAction("&About", self, triggered=self.about)

        self.aboutQtAct = QAction("About &Qt", self,
                triggered=QApplication.instance().aboutQt)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    def connect_buttons(self):
        self.ui.pushButton_zoomin.clicked.connect(self.zoomIn)
        self.ui.pushButton_zoomout.clicked.connect(self.zoomOut)
        self.ui.pushButton_prev.clicked.connect(self.prev_image)
        self.ui.pushButton_next.clicked.connect(self.next_image)
        self.ui.listWidget_images.itemClicked.connect(self.imageSelected)
        self.ui.listWidget_images.itemSelectionChanged.connect(self.imageSelected)

    def imageSelected(self):
        self.img_index = self.ui.listWidget_images.currentRow()
        self.open_image(self.img_index)

    def next_image(self):
        if self.img_index < len(self.images)-1:
            self.ui.listWidget_images.setCurrentRow(self.img_index+1)
            #self.open_image(self.img_index+1)

    def prev_image(self):
        if self.img_index > 0:
            self.ui.listWidget_images.setCurrentRow(self.img_index-1)
            #self.open_image(self.img_index-1)
    
    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    imageViewer = ImageViewer()
    imageViewer.show()
    sys.exit(app.exec_())
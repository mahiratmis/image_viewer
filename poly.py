from pathlib import Path
from enum import Enum
from functools import partial
import pandas as pd

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QDir, Qt
from PyQt5.QtGui import QImage, QPainter, QPalette, QPixmap
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QLabel,
        QMainWindow, QMenu, QMessageBox, QScrollArea, QSizePolicy)

from imageviewer_gw import Ui_MainWindow

class GripItem(QtWidgets.QGraphicsPathItem):
    circle = QtGui.QPainterPath()
    circle.addEllipse(QtCore.QRectF(-5, -5, 10, 10))
    square = QtGui.QPainterPath()
    square.addRect(QtCore.QRectF(-15, -15, 30, 30))

    def __init__(self, annotation_item, index):
        super(GripItem, self).__init__()
        self.m_annotation_item = annotation_item
        self.m_index = index

        self.setPath(GripItem.circle)
        self.setBrush(QtGui.QColor("green"))
        self.setPen(QtGui.QPen(QtGui.QColor("green"), 2))
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(11)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

    def hoverEnterEvent(self, event):
        self.setPath(GripItem.square)
        self.setBrush(QtGui.QColor("red"))
        super(GripItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPath(GripItem.circle)
        self.setBrush(QtGui.QColor("green"))
        super(GripItem, self).hoverLeaveEvent(event)

    def mouseReleaseEvent(self, event):
        self.setSelected(False)
        super(GripItem, self).mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionChange and self.isEnabled():
            self.m_annotation_item.movePoint(self.m_index, value)
        return super(GripItem, self).itemChange(change, value)


class PolygonAnnotation(QtWidgets.QGraphicsPolygonItem):
    def __init__(self, parent=None):
        super(PolygonAnnotation, self).__init__(parent)
        self.m_points = []
        self.setZValue(10)
        self.setPen(QtGui.QPen(QtGui.QColor("green"), 2))
        self.setAcceptHoverEvents(True)

        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)

        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        self.m_items = []

    def number_of_points(self):
        return len(self.m_items)

    def addPoint(self, p):
        self.m_points.append(p)
        self.setPolygon(QtGui.QPolygonF(self.m_points))
        item = GripItem(self, len(self.m_points) - 1)
        self.scene().addItem(item)
        self.m_items.append(item)
        item.setPos(p)

    def removeLastPoint(self):
        if self.m_points:
            self.m_points.pop()
            self.setPolygon(QtGui.QPolygonF(self.m_points))
            it = self.m_items.pop()
            self.scene().removeItem(it)
            del it

    def movePoint(self, i, p):
        if 0 <= i < len(self.m_points):
            self.m_points[i] = self.mapFromScene(p)
            self.setPolygon(QtGui.QPolygonF(self.m_points))

    def move_item(self, index, pos):
        if 0 <= index < len(self.m_items):
            item = self.m_items[index]
            item.setEnabled(False)
            item.setPos(pos)
            item.setEnabled(True)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            for i, point in enumerate(self.m_points):
                self.move_item(i, self.mapToScene(point))
        return super(PolygonAnnotation, self).itemChange(change, value)

    def hoverEnterEvent(self, event):
        self.setBrush(QtGui.QColor(255, 0, 0, 100))
        super(PolygonAnnotation, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
        super(PolygonAnnotation, self).hoverLeaveEvent(event)

    def make_invisible(self):
        for item in self.m_items:
            item.setEnabled(False)
            item.setVisible(False)
        self.setVisible(False)

    def make_visible(self):
        for item in self.m_items:
            item.setEnabled(True)
            item.setVisible(True)
        self.setVisible(True)

    def make_ineditable(self):
        for item in self.m_items:
            item.setEnabled(False)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)

    def get_top_left_coord(self):
        minx, miny = self.m_points[0].x(), self.m_points[0].y()
        for point in self.m_points:
            x, y = point.x(), point.y()
            if x < minx and y < miny:
                minx, miny = x, y
        return (minx, miny)
    
    def remove_points(self):
        for item in self.m_items:
            self.scene().removeItem(item)


class Instructions(Enum):
    No_Instruction = 0
    Polygon_Instruction = 1


class AnnotationScene(QtWidgets.QGraphicsScene):
    def __init__(self, parent=None):
        super(AnnotationScene, self).__init__(parent)
        self.image_item = QtWidgets.QGraphicsPixmapItem()
        self.image_item.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        self.addItem(self.image_item)
        self.current_instruction = Instructions.No_Instruction
        self.added_polygons = []

    def load_image(self, filename):
        self.image_item.setPixmap(QtGui.QPixmap(filename))
        self.setSceneRect(self.image_item.boundingRect())

    def setCurrentInstruction(self, instruction):
        self.current_instruction = instruction
        self.polygon_item = PolygonAnnotation()
        self.addItem(self.polygon_item)
        self.added_polygons.append(self.polygon_item)

    def mousePressEvent(self, event):
        if self.current_instruction == Instructions.Polygon_Instruction:
            self.polygon_item.removeLastPoint()
            self.polygon_item.addPoint(event.scenePos())
            # movable element
            self.polygon_item.addPoint(event.scenePos())
        super(AnnotationScene, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.current_instruction == Instructions.Polygon_Instruction:
            self.polygon_item.movePoint(self.polygon_item.number_of_points()-1, event.scenePos())
        super(AnnotationScene, self).mouseMoveEvent(event)


class AnnotationView(QtWidgets.QGraphicsView):
    factor = 1.05

    def __init__(self, parent=None):
        super(AnnotationView, self).__init__(parent)
        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        self.setMouseTracking(True)
        QtWidgets.QShortcut(QtGui.QKeySequence.ZoomIn, self, activated=self.zoomIn)
        QtWidgets.QShortcut(QtGui.QKeySequence.ZoomOut, self, activated=self.zoomOut)

    @QtCore.pyqtSlot()
    def zoomIn(self):
        self.zoom(AnnotationView.factor)

    @QtCore.pyqtSlot()
    def zoomOut(self):
        self.zoom(1 / AnnotationView.factor)

    def zoom(self, f):
        self.scale(f, f)
        if self.scene() is not None:
            self.centerOn(self.scene().image_item)


class AnnotationWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(AnnotationWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.graphicsView = AnnotationView()
        self.m_view = self.ui.graphicsView
        self.m_scene = AnnotationScene(self)
        self.m_view.setScene(self.m_scene)
        self.setCentralWidget(self.m_view)

        self.images = []
        self.img_index = 0
        self.img_dir = None
        self.gt_dir = None
        self.gt = []
        self.polygons = []
        self.texts = []

        self.createActions()
        self.createMenus()
        self.connect_buttons()

        QtWidgets.QShortcut(QtCore.Qt.Key_Escape, self, activated=partial(self.m_scene.setCurrentInstruction, Instructions.No_Instruction))

    def ground_truth_dir(self):
        dirName = QFileDialog.getExistingDirectory(self, "Select Images Folder",
                QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.PicturesLocation))
        if dirName:
            self.gt_dir = Path(dirName)

    def files_with_extension(self, path=".", patterns=("*.jpg", "*.JPG", 
        "*.jpeg", "*.JPEG", "*.png", "*.PNG")):
        """ returns file list that satisfy pattern """
        files = []
        # define the path
        path = Path(path)
        for pattern in patterns:
            files.extend(list(sorted(path.glob(pattern))))
        return files           

    @QtCore.pyqtSlot()
    def open(self):
        """ Open the directory containing the images load first image and its annotations"""
        dirName = QFileDialog.getExistingDirectory(self, "Select Images Folder",
                QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.PicturesLocation))

        if dirName:
            self.img_dir = Path(dirName)
            self.images = list(map(str, self.files_with_extension(dirName)))
            if not self.images :
                QMessageBox.information(self, "Directory Browser",
                        "No images under %s. " % dirName)
                return
            
            # populate QlistWidget and select the first row
            self.ui.listWidget_images.addItems(self.images)
            self.ui.listWidget_images.setCurrentRow(0)
            # open the image and fill the screen with image and annotation
            self.open_image(0)
    
    def clear_scene(self):
        """ Clear previously displayed polygons and texts from the scene"""
        for poly in self.polygons:
            poly.remove_points()
            self.m_scene.removeItem(poly)
        for text in self.texts:
            self.m_scene.removeItem(text)
        for poly in self.m_scene.added_polygons:
            poly.remove_points()
            self.m_scene.removeItem(poly)
        
        self.m_scene.added_polygons =[]
        self.texts = []
        self.polygons = []
        
    def open_image(self, idx):
        """ Load the image on to scene and the annotations it has """
        self.clear_scene()
        # load image
        self.img_index = idx
        fileName = self.images[idx]
        image = QImage(fileName)
        if image.isNull():
            QMessageBox.information(self, "Image Viewer",
                    "Cannot load %s." % fileName)
            return
        
        self.m_scene.load_image(fileName)

        # load ground truth
        if self.gt_dir:
            image_path = Path(fileName)
            gt_path = self.gt_dir / ("gt_" + image_path.stem + ".txt")
            self.gt = self.read_icdar2015_gt(gt_path)

            # add annotation
            for data in self.gt:
                # add polygon
                poly_item = PolygonAnnotation()        
                self.m_scene.addItem(poly_item)
                for i in range(4):
                    poly_item.addPoint(QtCore.QPointF(data[2*i],data[2*i+1]))
                poly_item.make_ineditable()
                self.polygons.append(poly_item)
                
                # add texts
                text_item = self.m_scene.addText(data[8])
                text_item.setPos(*poly_item.get_top_left_coord())
                self.texts.append(text_item)

        # check if the user wants to see annotation or not
        self.polygonsVisibility()
        self.textVisibility()
        #  image is loaded so activate buttons and menu links
        self.updateActions()

    def read_icdar2015_gt(self, fname):
        """ Return annotations inside the file.

            Annotation consists of lines in the following format
            x1,y1,x2,y2,x3,y3,x4,y4,Text
            coordinates start from topleft(x1,y1) going clockwise and
            ending at bottom left(x4,y4)  
        """

        df = pd.read_csv(fname, header=None)
        return df.values.tolist()

    def normalSize(self):
        # TODO
        self.m_view.zoom(1)

    def fitToWindow(self):
        """ Fit image to the screen size """
        self.m_view.fitInView(self.m_scene.image_item, QtCore.Qt.KeepAspectRatio)
        self.m_view.centerOn(self.m_scene.image_item)

    def about(self):
        QMessageBox.about(self, "About Image Viewer",
                "<p>This <b>Annotation Viewer</b> shows how to load "
                " Images in a directory and the Ground truth "
                " corresponding to the selected image for ICDAR 2015 dataset.")

    def createActions(self):
        """ Actions for Menus """
        self.openAct = QAction("&Open Images Dir", self, shortcut="Ctrl+O",
                triggered=self.open)

        self.gtAct = QAction("Choose Ground &Truth Folder", self, shortcut="Ctrl+T",
                triggered=self.ground_truth_dir)

        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                triggered=self.close)

        self.zoomInAct = QAction("Zoom &In (5%)", self, shortcut="Ctrl++",
                enabled=False, triggered=self.m_view.zoomIn)

        self.zoomOutAct = QAction("Zoom &Out (5%)", self, shortcut="Ctrl+-",
                enabled=False, triggered=self.m_view.zoomOut)

        self.normalSizeAct = QAction("&Normal Size", self, shortcut="Ctrl+S",
                enabled=False, triggered=self.normalSize)

        self.fitToWindowAct = QAction("&Fit to Window", self, enabled=False,
                shortcut="Ctrl+F", triggered=self.fitToWindow)

        self.aboutAct = QAction("&About", self, triggered=self.about)

        self.aboutQtAct = QAction("About &Qt", self,
                triggered=QApplication.instance().aboutQt)
        
        self.polygonAct = QAction("Insert Polygon", self, shortcut="Ctrl+G", 
                enabled=False, 
                triggered=partial(self.m_scene.setCurrentInstruction, 
                        Instructions.Polygon_Instruction) )

    def createMenus(self):
        """ Create Menus and place Actions inside them"""
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.gtAct)
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

        self.polyMenu = QMenu("&Insert", self)
        self.polyMenu.addAction(self.polygonAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.polyMenu)
        self.menuBar().addMenu(self.helpMenu)
       
    def updateActions(self):
        """ Check if some of the actions should be active or not"""
        active = len(self.images)>0
        self.zoomInAct.setEnabled(active)
        self.zoomOutAct.setEnabled(active)
        self.normalSizeAct.setEnabled(active)
        self.fitToWindowAct.setEnabled(active)
        self.polygonAct.setEnabled(active)

    def connect_buttons(self):
        """ Specify which item triggers which functions"""
        self.ui.pushButton_zoomin.clicked.connect(self.m_view.zoomIn)
        self.ui.pushButton_zoomout.clicked.connect(self.m_view.zoomOut)
        self.ui.pushButton_prev.clicked.connect(self.prev_image)
        self.ui.pushButton_next.clicked.connect(self.next_image)
        self.ui.listWidget_images.itemClicked.connect(self.imageSelected)
        self.ui.listWidget_images.itemSelectionChanged.connect(self.imageSelected)
        self.ui.checkBox_poly.clicked.connect(self.polygonsVisibility)
        self.ui.checkBox_text.clicked.connect(self.textVisibility)

    def polygonsVisibility(self):
        if self.ui.checkBox_poly.isChecked():
            for poly in self.polygons:
                poly.make_visible()
        else:
            for poly in self.polygons:
                poly.make_invisible()

    def textVisibility(self):
        visible = self.ui.checkBox_text.isChecked()
        for text in self.texts:
            text.setVisible(visible)

    def imageSelected(self):
        self.img_index = self.ui.listWidget_images.currentRow()
        self.open_image(self.img_index)

    def next_image(self):
        if self.img_index < len(self.images)-1:
            self.ui.listWidget_images.setCurrentRow(self.img_index+1)

    def prev_image(self):
        if self.img_index > 0:
            self.ui.listWidget_images.setCurrentRow(self.img_index-1)
    

if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = AnnotationWindow()
    w.resize(640, 480)
    w.show()
    sys.exit(app.exec_())